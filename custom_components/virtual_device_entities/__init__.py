"""Universal Virtual Device Entities Helper Integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_platform

from .const import (
    DOMAIN,
    CONF_PLATFORM_TYPE,
    SERVICE_SET_VALUE,
    SERVICE_RESET,
    ATTR_VALUE,
)

_LOGGER = logging.getLogger(__name__)

SET_VALUE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_VALUE): cv.match_all,
    }
)

RESET_SCHEMA = vol.Schema({})


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Virtual Device Entities component services."""
    hass.data.setdefault(DOMAIN, {})

    async def handle_set_value(call: ServiceCall) -> None:
        """Handle the set_value service call."""
        value = call.data.get(ATTR_VALUE)
        for entity in hass.data.get(f"{DOMAIN}_entities", []):
            if hasattr(entity, "entity_id") and entity.entity_id in call.target.get("entity_id", []):
                if hasattr(entity, "async_set_value"):
                    await entity.async_set_value(value)

    async def handle_reset(call: ServiceCall) -> None:
        """Handle the reset service call."""
        for entity in hass.data.get(f"{DOMAIN}_entities", []):
            if hasattr(entity, "entity_id") and entity.entity_id in call.target.get("entity_id", []):
                if hasattr(entity, "async_reset"):
                    await entity.async_reset()

    # Register services on domain
    if not hass.services.has_service(DOMAIN, SERVICE_SET_VALUE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_VALUE,
            handle_set_value,
            schema=cv.make_entity_service_schema(SET_VALUE_SCHEMA),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_RESET):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESET,
            handle_reset,
            schema=cv.make_entity_service_schema(RESET_SCHEMA),
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Virtual Device Entities config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data.setdefault(f"{DOMAIN}_entities", [])

    platform_type = entry.options.get(
        CONF_PLATFORM_TYPE, entry.data.get(CONF_PLATFORM_TYPE, "sensor")
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "platform_type": platform_type,
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, [platform_type])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Virtual Device Entities config entry."""
    platform_type = hass.data[DOMAIN].get(entry.entry_id, {}).get("platform_type")
    unload_ok = True
    if platform_type:
        unload_ok = await hass.config_entries.async_forward_entry_unload(
            entry, platform_type
        )

    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
