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
    CONF_DEVICE_ID,
    CONF_ENTITY_NAME,
    CONF_INITIAL_VALUE,
    CONF_ICON,
)
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Device Entities switch."""
    entity = VirtualDeviceSwitch(hass, entry)
    async_add_entities([entity], True)


class VirtualDeviceSwitch(RestoreEntity, SwitchEntity):
    """Virtual Switch attached to a device or standalone."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the virtual switch."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_switch"

        opts = entry.options
        data = entry.data

        self._attr_name = opts.get(CONF_ENTITY_NAME, data.get(CONF_ENTITY_NAME, "Virtual Switch"))
        self._base_device_id = opts.get(CONF_DEVICE_ID, data.get(CONF_DEVICE_ID))
        self._attr_icon = opts.get(CONF_ICON, data.get(CONF_ICON, "mdi:toggle-switch"))

        init_val = str(opts.get(CONF_INITIAL_VALUE, data.get(CONF_INITIAL_VALUE, "off"))).lower()
        self._attr_is_on = init_val in ("on", "true", "1")

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
