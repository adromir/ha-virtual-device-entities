"""Binary Sensor platform for Virtual Device Entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_ENTITY_NAME,
    CONF_INITIAL_VALUE,
    CONF_ICON,
    CONF_DEVICE_CLASS,
    CONF_LINKED_ENTITY,
)
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Device Entities binary sensor."""
    entity = VirtualDeviceBinarySensor(hass, entry)
    async_add_entities([entity], True)


class VirtualDeviceBinarySensor(RestoreEntity, BinarySensorEntity):
    """Virtual Binary Sensor attached to a device or standalone."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the virtual binary sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_binary_sensor"

        opts = entry.options
        data = entry.data

        self._attr_name = opts.get(CONF_ENTITY_NAME, data.get(CONF_ENTITY_NAME, "Virtual Binary Sensor"))
        self._base_device_id = opts.get(CONF_DEVICE_ID, data.get(CONF_DEVICE_ID))
        self._attr_icon = opts.get(CONF_ICON, data.get(CONF_ICON, "mdi:checkbox-marked-circle-outline"))
        self._attr_device_class = opts.get(CONF_DEVICE_CLASS, data.get(CONF_DEVICE_CLASS))
        self._linked_entity = opts.get(CONF_LINKED_ENTITY, data.get(CONF_LINKED_ENTITY))

        init_val = str(opts.get(CONF_INITIAL_VALUE, data.get(CONF_INITIAL_VALUE, "off"))).lower()
        self._attr_is_on = init_val in ("on", "true", "1", "yes")
        self._unsub_tracker = None

    @property
    def device_info(self):
        """Return device information linking to base device or standalone."""
        return get_device_info(
            self.hass,
            self._entry.entry_id,
            self._base_device_id,
            self._attr_name,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "is_virtual": True,
            "base_device_id": self._base_device_id,
            "linked_entity": self._linked_entity,
        }

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant."""
        await super().async_added_to_hass()

        entities_list = self.hass.data.setdefault(f"{DOMAIN}_entities", [])
        entities_list.append(self)

        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in ("on", "off"):
            self._attr_is_on = (last_state.state == "on")
            self.async_write_ha_state()

        if self._linked_entity:
            @callback
            def _handle_source_change(event):
                new_state = event.data.get("new_state")
                if new_state is not None:
                    val_str = str(new_state.state).lower()
                    self._attr_is_on = val_str in ("on", "true", "1", "yes")
                    self.async_write_ha_state()

            self._unsub_tracker = async_track_state_change_event(
                self.hass, [self._linked_entity], _handle_source_change
            )

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        if self._unsub_tracker:
            self._unsub_tracker()
            self._unsub_tracker = None

        entities_list = self.hass.data.get(f"{DOMAIN}_entities", [])
        if self in entities_list:
            entities_list.remove(self)

        await super().async_will_remove_from_hass()

    async def async_set_value(self, value: Any) -> None:
        """Set binary state via service."""
        val_str = str(value).lower()
        self._attr_is_on = val_str in ("on", "true", "1", "yes")
        self.async_write_ha_state()

    async def async_reset(self) -> None:
        """Reset binary state to off or initial value."""
        self._attr_is_on = False
        self.async_write_ha_state()
