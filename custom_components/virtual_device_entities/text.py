"""Text platform for Virtual Device Entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.text import TextEntity
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
    """Set up the Virtual Device Entities text entity."""
    entity = VirtualDeviceText(hass, entry)
    async_add_entities([entity], True)


class VirtualDeviceText(RestoreEntity, TextEntity):
    """Virtual Text attached to a device or standalone."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the virtual text entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_text"

        opts = entry.options
        data = entry.data

        self._attr_name = opts.get(CONF_ENTITY_NAME, data.get(CONF_ENTITY_NAME, "Virtual Text"))
        self._base_device_id = opts.get(CONF_DEVICE_ID, data.get(CONF_DEVICE_ID))
        self._attr_icon = opts.get(CONF_ICON, data.get(CONF_ICON, "mdi:text-box-outline"))

        self._attr_native_value = str(opts.get(CONF_INITIAL_VALUE, data.get(CONF_INITIAL_VALUE, "")))

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
        if last_state is not None and last_state.state not in (None, "unknown", "unavailable"):
            self._attr_native_value = last_state.state
            self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        entities_list = self.hass.data.get(f"{DOMAIN}_entities", [])
        if self in entities_list:
            entities_list.remove(self)
        await super().async_will_remove_from_hass()

    async def async_set_value(self, value: str) -> None:
        """Set text value."""
        self._attr_native_value = str(value) if value is not None else ""
        self.async_write_ha_state()

    async def async_reset(self) -> None:
        """Reset text to initial value."""
        init_val = self._entry.options.get(
            CONF_INITIAL_VALUE, self._entry.data.get(CONF_INITIAL_VALUE, "")
        )
        self._attr_native_value = str(init_val)
        self.async_write_ha_state()
