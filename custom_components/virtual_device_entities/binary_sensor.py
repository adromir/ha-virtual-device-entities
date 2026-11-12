"""Binary Sensor platform for Virtual Device Entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_template_result, TrackTemplate
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.template import Template

from .const import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_DEVICE_NAME,
    CONF_BASE_DEVICE_ID,
    CONF_ATTACH_TO_BASE,
    CONF_ENTITY_NAME,
    CONF_PLATFORM,
    CONF_ICON,
    CONF_DEVICE_CLASS,
    CONF_SOURCE_ENTITY,
    CONF_TEMPLATE,
    CONF_INITIAL_VALUE,
    TYPE_MIRROR,
    TYPE_TEMPLATE,
    TYPE_MANUAL,
    PLATFORM_BINARY_SENSOR,
)
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Device binary sensors from a config entry."""
    entry_data = {**entry.data, **entry.options}
    entities_map = entry_data.get(CONF_ENTITIES, {})
    device_name = entry_data.get(CONF_DEVICE_NAME, entry.title)
    base_device_id = entry_data.get(CONF_BASE_DEVICE_ID)
    attach_to_base = entry_data.get(CONF_ATTACH_TO_BASE, False)

    binary_sensors = []
    for ent_id, cfg in entities_map.items():
        if cfg.get(CONF_PLATFORM) == PLATFORM_BINARY_SENSOR:
            binary_sensors.append(
                VirtualDeviceBinarySensor(
                    hass=hass,
                    entry=entry,
                    entity_id_key=ent_id,
                    config=cfg,
                    device_name=device_name,
                    base_device_id=base_device_id,
                    attach_to_base=attach_to_base,
                )
            )

    if binary_sensors:
        async_add_entities(binary_sensors, True)


class VirtualDeviceBinarySensor(RestoreEntity, BinarySensorEntity):
    """Virtual Binary Sensor supporting Mirroring, Templates, or Manual state."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        entity_id_key: str,
        config: dict[str, Any],
        device_name: str,
        base_device_id: str | None,
        attach_to_base: bool,
    ) -> None:
        """Initialize the virtual binary sensor."""
        self.hass = hass
        self._entry = entry
        self._entity_id_key = entity_id_key
        self._config = config
        self._device_name = device_name
        self._base_device_id = base_device_id
        self._attach_to_base = attach_to_base

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{entity_id_key}"
        self._attr_name = config.get(CONF_ENTITY_NAME, "Virtual Binary Sensor")
        self._attr_icon = config.get(CONF_ICON, "mdi:checkbox-marked-circle-outline")
        self._attr_device_class = config.get(CONF_DEVICE_CLASS)

        self._entity_type = config.get("entity_type", TYPE_MANUAL)
        self._source_entity = config.get(CONF_SOURCE_ENTITY)
        self._template_str = config.get(CONF_TEMPLATE, "")

        init_val = str(config.get(CONF_INITIAL_VALUE, "off")).lower()
        self._attr_is_on = init_val in ("on", "true", "1", "yes")
        self._unsub = None

    @property
    def device_info(self):
        """Return device information linking to base device or virtual device."""
        return get_device_info(
            self.hass,
            self._entry.entry_id,
            self._base_device_id,
            self._attach_to_base,
            self._device_name,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {
            "is_virtual": True,
            "entity_type": self._entity_type,
            "base_device_id": self._base_device_id,
        }
        if self._source_entity:
            attrs["source_entity"] = self._source_entity
        return attrs

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant."""
        await super().async_added_to_hass()
        entities_list = self.hass.data.setdefault(f"{DOMAIN}_entities", [])
        entities_list.append(self)

        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in ("on", "off"):
            self._attr_is_on = (last_state.state == "on")
            self.async_write_ha_state()

        if self._entity_type == TYPE_MIRROR and self._source_entity:
            @callback
            def _handle_source(event):
                new_state = event.data.get("new_state")
                if new_state is not None:
                    v = str(new_state.state).lower()
                    self._attr_is_on = v in ("on", "true", "1", "yes")
                    self.async_write_ha_state()

            self._unsub = async_track_state_change_event(
                self.hass, [self._source_entity], _handle_source
            )
            cur = self.hass.states.get(self._source_entity)
            if cur is not None:
                self._attr_is_on = str(cur.state).lower() in ("on", "true", "1", "yes")

        elif self._entity_type == TYPE_TEMPLATE and self._template_str:
            tmpl = Template(self._template_str, self.hass)

            @callback
            def _handle_template(event, updates):
                result = updates.pop().result
                if isinstance(result, Exception):
                    return
                self._attr_is_on = str(result).lower() in ("on", "true", "1", "yes")
                self.async_write_ha_state()

            self._unsub = async_track_template_result(
                self.hass, [TrackTemplate(tmpl, None)], _handle_template
            )

        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        if self._unsub:
            self._unsub()
            self._unsub = None
        entities_list = self.hass.data.get(f"{DOMAIN}_entities", [])
        if self in entities_list:
            entities_list.remove(self)
        await super().async_will_remove_from_hass()

    async def async_set_value(self, value: Any) -> None:
        """Set value via service."""
        val_str = str(value).lower()
        self._attr_is_on = val_str in ("on", "true", "1", "yes")
        self.async_write_ha_state()

    async def async_reset(self) -> None:
        """Reset to off."""
        self._attr_is_on = False
        self.async_write_ha_state()
