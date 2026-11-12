"""Switch platform for Virtual Device Entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_DEVICE_NAME,
    CONF_BASE_DEVICE_ID,
    CONF_ATTACH_TO_BASE,
    CONF_ENTITY_NAME,
    CONF_PLATFORM,
    CONF_ICON,
    CONF_INITIAL_VALUE,
    PLATFORM_SWITCH,
)
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Device switches."""
    entry_data = {**entry.data, **entry.options}
    entities_map = entry_data.get(CONF_ENTITIES, {})
    device_name = entry_data.get(CONF_DEVICE_NAME, entry.title)
    base_device_id = entry_data.get(CONF_BASE_DEVICE_ID)
    attach_to_base = entry_data.get(CONF_ATTACH_TO_BASE, False)

    switches = []
    for ent_id, cfg in entities_map.items():
        if cfg.get(CONF_PLATFORM) == PLATFORM_SWITCH:
            switches.append(
                VirtualDeviceSwitch(
                    hass=hass,
                    entry=entry,
                    entity_id_key=ent_id,
                    config=cfg,
                    device_name=device_name,
                    base_device_id=base_device_id,
                    attach_to_base=attach_to_base,
                )
            )

    if switches:
        async_add_entities(switches, True)


class VirtualDeviceSwitch(RestoreEntity, SwitchEntity):
    """Virtual Switch attached to a device or standalone."""

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
        """Initialize the virtual switch."""
        self.hass = hass
        self._entry = entry
        self._entity_id_key = entity_id_key
        self._config = config
        self._device_name = device_name
        self._base_device_id = base_device_id
        self._attach_to_base = attach_to_base

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{entity_id_key}"
        self._attr_name = config.get(CONF_ENTITY_NAME, "Virtual Switch")
        self._attr_icon = config.get(CONF_ICON, "mdi:toggle-switch")

        init_val = str(config.get(CONF_INITIAL_VALUE, "off")).lower()
        self._attr_is_on = init_val in ("on", "true", "1")

    @property
    def device_info(self):
        """Return device information."""
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
        return {
            "is_virtual": True,
            "base_device_id": self._base_device_id,
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

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        entities_list = self.hass.data.get(f"{DOMAIN}_entities", [])
        if self in entities_list:
            entities_list.remove(self)
        await super().async_will_remove_from_hass()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn switch on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn switch off."""
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_set_value(self, value: Any) -> None:
        """Set switch state via service."""
        val_str = str(value).lower()
        self._attr_is_on = val_str in ("on", "true", "1")
        self.async_write_ha_state()

    async def async_reset(self) -> None:
        """Reset switch to off."""
        self._attr_is_on = False
        self.async_write_ha_state()
