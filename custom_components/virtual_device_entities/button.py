"""Button platform for Virtual Device Entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_ENTITY_NAME,
    CONF_ICON,
    CONF_LINKED_ENTITY,
)
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Device Entities button."""
    entity = VirtualDeviceButton(hass, entry)
    async_add_entities([entity], True)


class VirtualDeviceButton(ButtonEntity):
    """Virtual Button attached to a device or standalone."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the virtual button."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_button"

        opts = entry.options
        data = entry.data

        self._attr_name = opts.get(CONF_ENTITY_NAME, data.get(CONF_ENTITY_NAME, "Virtual Action"))
        self._base_device_id = opts.get(CONF_DEVICE_ID, data.get(CONF_DEVICE_ID))
        self._attr_icon = opts.get(CONF_ICON, data.get(CONF_ICON, "mdi:gesture-tap-button"))
        self._linked_entity = opts.get(CONF_LINKED_ENTITY, data.get(CONF_LINKED_ENTITY))

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

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        entities_list = self.hass.data.get(f"{DOMAIN}_entities", [])
        if self in entities_list:
            entities_list.remove(self)
        await super().async_will_remove_from_hass()

    async def async_press(self) -> None:
        """Handle button press."""
        now_iso = dt_util.utcnow().isoformat()
        _LOGGER.debug("Virtual button %s pressed at %s", self.entity_id, now_iso)

        # Fire Home Assistant bus event
        self.hass.bus.async_fire(
            "virtual_device_entities_button_pressed",
            {
                "entity_id": self.entity_id,
                "base_device_id": self._base_device_id,
                "timestamp": now_iso,
            },
        )

        # If a linked entity exists (e.g. maintenance timestamp sensor), update it directly
        if self._linked_entity:
            for entity in self.hass.data.get(f"{DOMAIN}_entities", []):
                if getattr(entity, "entity_id", None) == self._linked_entity:
                    if hasattr(entity, "async_set_value"):
                        await entity.async_set_value(now_iso)

    async def async_reset(self) -> None:
        """Reset action alias."""
        await self.async_press()
