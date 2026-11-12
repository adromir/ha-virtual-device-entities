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
    CONF_ENTITIES,
    CONF_DEVICE_NAME,
    CONF_BASE_DEVICE_ID,
    CONF_ATTACH_TO_BASE,
    CONF_ENTITY_NAME,
    CONF_PLATFORM,
    CONF_ICON,
    CONF_SOURCE_ENTITY,
    PLATFORM_BUTTON,
)
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Device buttons."""
    entry_data = {**entry.data, **entry.options}
    entities_map = entry_data.get(CONF_ENTITIES, {})
    device_name = entry_data.get(CONF_DEVICE_NAME, entry.title)
    base_device_id = entry_data.get(CONF_BASE_DEVICE_ID)
    attach_to_base = entry_data.get(CONF_ATTACH_TO_BASE, False)

    buttons = []
    for ent_id, cfg in entities_map.items():
        if cfg.get(CONF_PLATFORM) == PLATFORM_BUTTON:
            buttons.append(
                VirtualDeviceButton(
                    hass=hass,
                    entry=entry,
                    entity_id_key=ent_id,
                    config=cfg,
                    device_name=device_name,
                    base_device_id=base_device_id,
                    attach_to_base=attach_to_base,
                )
            )

    if buttons:
        async_add_entities(buttons, True)


class VirtualDeviceButton(ButtonEntity):
    """Virtual Button attached to a device or standalone."""

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
        """Initialize the virtual button."""
        self.hass = hass
        self._entry = entry
        self._entity_id_key = entity_id_key
        self._config = config
        self._device_name = device_name
        self._base_device_id = base_device_id
        self._attach_to_base = attach_to_base

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{entity_id_key}"
        self._attr_name = config.get(CONF_ENTITY_NAME, "Virtual Action")
        self._attr_icon = config.get(CONF_ICON, "mdi:gesture-tap-button")
        self._target_entity = config.get(CONF_SOURCE_ENTITY)

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
            "target_entity": self._target_entity,
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

        self.hass.bus.async_fire(
            "virtual_device_entities_button_pressed",
            {
                "entity_id": self.entity_id,
                "base_device_id": self._base_device_id,
                "timestamp": now_iso,
            },
        )

        # Update target entity if linked (e.g. timestamp sensor for filter replacement)
        if self._target_entity:
            for entity in self.hass.data.get(f"{DOMAIN}_entities", []):
                if getattr(entity, "entity_id", None) == self._target_entity:
                    if hasattr(entity, "async_set_value"):
                        await entity.async_set_value(now_iso)

    async def async_reset(self) -> None:
        """Reset alias for button."""
        await self.async_press()
