"""Number platform for Virtual Device Entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
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
    CONF_UNIT,
    CONF_MIN_VALUE,
    CONF_MAX_VALUE,
    CONF_STEP_VALUE,
)
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Device Entities number."""
    entity = VirtualDeviceNumber(hass, entry)
    async_add_entities([entity], True)


class VirtualDeviceNumber(RestoreEntity, NumberEntity):
    """Virtual Number attached to a device or standalone."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.AUTO

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the virtual number."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_number"

        opts = entry.options
        data = entry.data

        self._attr_name = opts.get(CONF_ENTITY_NAME, data.get(CONF_ENTITY_NAME, "Virtual Number"))
        self._base_device_id = opts.get(CONF_DEVICE_ID, data.get(CONF_DEVICE_ID))
        self._attr_icon = opts.get(CONF_ICON, data.get(CONF_ICON, "mdi:numeric"))
        self._attr_native_unit_of_measurement = opts.get(CONF_UNIT, data.get(CONF_UNIT))

        self._attr_native_min_value = float(opts.get(CONF_MIN_VALUE, data.get(CONF_MIN_VALUE, 0.0)))
        self._attr_native_max_value = float(opts.get(CONF_MAX_VALUE, data.get(CONF_MAX_VALUE, 100.0)))
        self._attr_native_step = float(opts.get(CONF_STEP_VALUE, data.get(CONF_STEP_VALUE, 1.0)))

        try:
            init_val = float(opts.get(CONF_INITIAL_VALUE, data.get(CONF_INITIAL_VALUE, 0.0)))
        except (ValueError, TypeError):
            init_val = self._attr_native_min_value
        self._attr_native_value = init_val

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
            try:
                self._attr_native_value = float(last_state.state)
                self.async_write_ha_state()
            except (ValueError, TypeError):
                pass

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        entities_list = self.hass.data.get(f"{DOMAIN}_entities", [])
        if self in entities_list:
            entities_list.remove(self)
        await super().async_will_remove_from_hass()

    async def async_set_native_value(self, value: float) -> None:
        """Set native value."""
        self._attr_native_value = float(value)
        self.async_write_ha_state()

    async def async_set_value(self, value: Any) -> None:
        """Set value via service."""
        try:
            self._attr_native_value = float(value)
            self.async_write_ha_state()
        except (ValueError, TypeError):
            pass

    async def async_reset(self) -> None:
        """Reset number to minimum or initial value."""
        init_val = self._entry.options.get(
            CONF_INITIAL_VALUE, self._entry.data.get(CONF_INITIAL_VALUE, self._attr_native_min_value)
        )
        try:
            self._attr_native_value = float(init_val)
        except (ValueError, TypeError):
            self._attr_native_value = self._attr_native_min_value
        self.async_write_ha_state()
