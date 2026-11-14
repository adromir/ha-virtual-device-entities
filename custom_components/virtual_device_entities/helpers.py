"""Helper utilities and rule parser for Virtual Device Entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

COLOR_NAMES = {
    "green": (76, 175, 80),
    "red": (244, 67, 54),
    "blue": (33, 150, 243),
    "orange": (255, 152, 0),
    "amber": (255, 193, 7),
    "yellow": (255, 235, 59),
    "purple": (156, 39, 176),
    "grey": (158, 158, 158),
    "gray": (158, 158, 158),
    "teal": (0, 150, 136),
    "cyan": (0, 188, 212),
}


def color_to_rgb(color_str: str | None) -> list[int] | None:
    """Convert CSS color name or HEX string (#RRGGBB) to [R, G, B] list."""
    if not color_str:
        return None
    c = color_str.strip().lower()
    if c in COLOR_NAMES:
        return list(COLOR_NAMES[c])
    if c.startswith("#") and len(c) == 7:
        try:
            return [int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
        except ValueError:
            return None
    return None


def get_device_info(
    hass: HomeAssistant,
    entry_id: str,
    base_device_id: str | None,
    attach_to_base: bool,
    device_name: str,
) -> DeviceInfo:
    """Resolve DeviceInfo linking to an existing base device or standalone virtual device."""
    if base_device_id and attach_to_base:
        dev_reg = dr.async_get(hass)
        base_dev = dev_reg.async_get(base_device_id)
        if base_dev:
            # Bind directly to the physical device's identifiers
            return DeviceInfo(
                connections=base_dev.connections,
                identifiers=base_dev.identifiers,
            )

    # Standalone Virtual Device (optionally linked to base device via_device)
    info = DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=device_name or "Virtual Device",
        manufacturer="Virtual Device Helper",
        model="Enhanced Virtual Appliance",
    )
    if base_device_id:
        info["via_device"] = (DOMAIN, base_device_id)

    return info


def parse_state_rules(rules_text: str | None) -> list[dict[str, Any]]:
    """Parse pipe-separated multiline state rules into structured list.
    Format per line: condition | state_name | [icon] | [color]
    """
    if not rules_text:
        return []
    rules = []
    for line in rules_text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            cond = parts[0]
            state_val = parts[1]
            icon = parts[2] if len(parts) > 2 and parts[2] else None
            color = parts[3] if len(parts) > 3 and parts[3] else None
            rules.append({
                "condition": cond,
                "state": state_val,
                "icon": icon,
                "color": color,
            })
    return rules


def evaluate_condition(cond: str, raw_state: Any) -> bool:
    """Evaluate whether a raw state satisfies a given rule condition."""
    cond = cond.strip()
    raw_str = str(raw_state).strip()

    # Numeric comparisons
    try:
        val = float(raw_str)
        # Range: "X - Y" or "X..Y"
        if " - " in cond or ".." in cond:
            sep = " - " if " - " in cond else ".."
            low_str, high_str = cond.split(sep, 1)
            low = float(low_str.strip())
            high = float(high_str.strip())
            return low <= val <= high
        if cond.startswith("<="):
            return val <= float(cond[2:].strip())
        if cond.startswith(">="):
            return val >= float(cond[2:].strip())
        if cond.startswith("<"):
            return val < float(cond[1:].strip())
        if cond.startswith(">"):
            return val > float(cond[1:].strip())
        if cond.startswith("=="):
            return val == float(cond[2:].strip())
    except (ValueError, TypeError):
        pass

    # Exact string comparison (case-insensitive)
    if cond.lower() == raw_str.lower():
        return True

    # Substring contains: "contains XYZ"
    if cond.lower().startswith("contains "):
        sub = cond[9:].strip().lower()
        return sub in raw_str.lower()

    return False


def resolve_inherited_device_class(
    hass: HomeAssistant,
    source_entity_id: str | None = None,
    base_device_id: str | None = None,
    platform: str | None = None,
) -> str | None:
    """Resolve inherited device_class from source entity or base device."""
    ent_reg = er.async_get(hass)

    # 1. Direct inheritance from source entity
    if source_entity_id:
        entry = ent_reg.async_get(source_entity_id)
        if entry:
            if entry.device_class:
                return str(entry.device_class)
            if entry.original_device_class:
                return str(entry.original_device_class)
        state = hass.states.get(source_entity_id)
        if state and state.attributes.get("device_class"):
            return str(state.attributes.get("device_class"))

    # 2. Inheritance from base device entities (if no source entity or source entity has none)
    if base_device_id:
        device_entries = er.async_entries_for_device(ent_reg, base_device_id)
        for entry in device_entries:
            if platform and entry.domain != platform:
                continue
            if entry.device_class:
                return str(entry.device_class)
            if entry.original_device_class:
                return str(entry.original_device_class)
        # Fallback without platform filter if matching platform wasn't found
        if platform:
            for entry in device_entries:
                if entry.device_class:
                    return str(entry.device_class)
                if entry.original_device_class:
                    return str(entry.original_device_class)

    return None

