"""Helper utilities for Virtual Device Entities."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


def get_device_info(
    hass: HomeAssistant,
    entry_id: str,
    base_device_id: str | None,
    device_name: str,
) -> DeviceInfo:
    """Resolve DeviceInfo linking to an existing device or standalone virtual device."""
    if base_device_id:
        dev_reg = dr.async_get(hass)
        base_dev = dev_reg.async_get(base_device_id)
        if base_dev:
            # Bind to existing device connections/identifiers
            return DeviceInfo(
                connections=base_dev.connections,
                identifiers=base_dev.identifiers,
            )

    # Standalone Virtual Device
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=device_name or "Virtual Device",
        manufacturer="Virtual Device Helper",
        model="Virtual Entity Suite",
    )
