"""Sensor platform for Virtual Device Entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_template_result, TrackTemplate
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_DEVICE_NAME,
    CONF_BASE_DEVICE_ID,
    CONF_ATTACH_TO_BASE,
    CONF_ENTITY_ID,
    CONF_ENTITY_TYPE,
    CONF_ENTITY_NAME,
    CONF_PLATFORM,
    CONF_ICON,
    CONF_UNIT,
    CONF_DEVICE_CLASS,
    CONF_SOURCE_ENTITY,
    CONF_STATE_RULES,
    CONF_DEFAULT_STATE,
    CONF_DEFAULT_ICON,
    CONF_DEFAULT_COLOR,
    CONF_TEMPLATE,
    CONF_INITIAL_VALUE,
    TYPE_STATE_MACHINE,
    TYPE_MIRROR,
    TYPE_TEMPLATE,
    TYPE_MANUAL,
    PLATFORM_SENSOR,
)
from .helpers import (
    get_device_info,
    parse_state_rules,
    evaluate_condition,
    color_to_rgb,
    resolve_inherited_device_class,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Device sensors from a config entry."""
    entry_data = {**entry.data, **entry.options}
    entities_map = entry_data.get(CONF_ENTITIES, {})
    device_name = entry_data.get(CONF_DEVICE_NAME, entry.title)
    base_device_id = entry_data.get(CONF_BASE_DEVICE_ID)
    attach_to_base = entry_data.get(CONF_ATTACH_TO_BASE, False)

    sensors = []
    for ent_id, cfg in entities_map.items():
        if cfg.get(CONF_PLATFORM, PLATFORM_SENSOR) == PLATFORM_SENSOR:
            sensors.append(
                VirtualDeviceSensor(
                    hass=hass,
                    entry=entry,
                    entity_id_key=ent_id,
                    config=cfg,
                    device_name=device_name,
                    base_device_id=base_device_id,
                    attach_to_base=attach_to_base,
                )
            )

    if sensors:
        async_add_entities(sensors, True)


class VirtualDeviceSensor(RestoreEntity, SensorEntity):
    """Virtual Sensor supporting State Machine, Mirroring, Templates, or Manual storage."""

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
        """Initialize the virtual sensor."""
        self.hass = hass
        self._entry = entry
        self._entity_id_key = entity_id_key
        self._config = config
        self._device_name = device_name
        self._base_device_id = base_device_id
        self._attach_to_base = attach_to_base

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{entity_id_key}"
        self._attr_name = config.get(CONF_ENTITY_NAME, "Virtual Sensor")
        self._attr_native_unit_of_measurement = config.get(CONF_UNIT)
        self._attr_device_class = config.get(CONF_DEVICE_CLASS)
        self._default_icon = config.get(CONF_ICON, config.get(CONF_DEFAULT_ICON, "mdi:chip"))

        self._entity_type = config.get(CONF_ENTITY_TYPE, TYPE_MANUAL)
        self._source_entity = config.get(CONF_SOURCE_ENTITY)
        self._state_rules_raw = config.get(CONF_STATE_RULES, "")
        self._parsed_rules = parse_state_rules(self._state_rules_raw)
        self._default_state = config.get(CONF_DEFAULT_STATE, "Unknown")
        self._default_color = config.get(CONF_DEFAULT_COLOR, "#9E9E9E")
        self._template_str = config.get(CONF_TEMPLATE, "")

        # Dynamic state & color properties
        self._current_icon = self._default_icon
        self._current_color = self._default_color
        self._matched_condition = None
        self._raw_source_state = None

        init_val = config.get(CONF_INITIAL_VALUE, self._default_state)
        self._attr_native_value = init_val
        self._unsub = None

    @property
    def device_info(self):
        """Return device information linking to base device or virtual device."""
        return get_device_info(
            self.hass,
            self._entry.entry_id,
            self._base_device_id,
            self._attach_to_base,
            self._device_name,
        )

    @property
    def icon(self) -> str | None:
        """Dynamically return the icon of the active state."""
        if self._current_icon:
            return self._current_icon
        if self._default_icon:
            return self._default_icon
        if self._source_entity:
            st = self.hass.states.get(self._source_entity)
            if st and st.attributes.get("icon"):
                return st.attributes.get("icon")
        return "mdi:chip"

    @property
    def device_class(self) -> str | None:
        """Return device class, inheriting from source entity or base device if not set."""
        if self._attr_device_class:
            return self._attr_device_class
        return resolve_inherited_device_class(
            self.hass,
            source_entity_id=self._source_entity,
            base_device_id=self._base_device_id,
            platform=PLATFORM_SENSOR,
        )

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement, inheriting from source entity if not set."""
        if self._attr_native_unit_of_measurement:
            return self._attr_native_unit_of_measurement
        if self._source_entity:
            st = self.hass.states.get(self._source_entity)
            if st and st.attributes.get("unit_of_measurement"):
                return st.attributes.get("unit_of_measurement")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes including colors and matched rules."""
        attrs: dict[str, Any] = {
            "is_virtual": True,
            "entity_type": self._entity_type,
            "base_device_id": self._base_device_id,
        }
        if self._entity_type == TYPE_STATE_MACHINE:
            attrs.update({
                "color": self._current_color,
                "icon_color": self._current_color,
                "state_color": self._current_color,
                "rgb_color": color_to_rgb(self._current_color),
                "matched_condition": self._matched_condition,
                "source_entity": self._source_entity,
                "source_state": self._raw_source_state,
                "configured_rules_count": len(self._parsed_rules),
            })
        elif self._entity_type == TYPE_MIRROR:
            attrs.update({
                "source_entity": self._source_entity,
                "source_state": self._raw_source_state,
            })
        elif self._entity_type == TYPE_TEMPLATE:
            attrs.update({
                "template": self._template_str,
            })
        return attrs

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant."""
        await super().async_added_to_hass()

        entities_list = self.hass.data.setdefault(f"{DOMAIN}_entities", [])
        entities_list.append(self)

        # Restore previous state
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (None, "unknown", "unavailable"):
            self._attr_native_value = last_state.state
            if "color" in last_state.attributes:
                self._current_color = last_state.attributes["color"]
            if "icon" in last_state.attributes:
                self._current_icon = last_state.attributes["icon"]

        # Setup dynamic behavior based on entity type
        if self._entity_type == TYPE_STATE_MACHINE and self._source_entity:
            @callback
            def _handle_state_machine_source(event):
                new_state = event.data.get("new_state")
                if new_state is not None and new_state.state not in (None, "unknown", "unavailable"):
                    self._evaluate_state_machine(new_state.state)

            self._unsub = async_track_state_change_event(
                self.hass, [self._source_entity], _handle_state_machine_source
            )
            # Evaluate current source state immediately
            cur = self.hass.states.get(self._source_entity)
            if cur is not None and cur.state not in (None, "unknown", "unavailable"):
                self._evaluate_state_machine(cur.state)

        elif self._entity_type == TYPE_MIRROR and self._source_entity:
            @callback
            def _handle_mirror_source(event):
                new_state = event.data.get("new_state")
                if new_state is not None:
                    self._raw_source_state = new_state.state
                    self._attr_native_value = new_state.state
                    if not self._attr_native_unit_of_measurement and new_state.attributes.get("unit_of_measurement"):
                        self._attr_native_unit_of_measurement = new_state.attributes.get("unit_of_measurement")
                    self.async_write_ha_state()

            self._unsub = async_track_state_change_event(
                self.hass, [self._source_entity], _handle_mirror_source
            )
            cur = self.hass.states.get(self._source_entity)
            if cur is not None:
                self._raw_source_state = cur.state
                self._attr_native_value = cur.state
                if not self._attr_native_unit_of_measurement and cur.attributes.get("unit_of_measurement"):
                    self._attr_native_unit_of_measurement = cur.attributes.get("unit_of_measurement")

        elif self._entity_type == TYPE_TEMPLATE and self._template_str:
            tmpl = Template(self._template_str, self.hass)

            @callback
            def _handle_template_result(event, updates):
                result = updates.pop().result
                if isinstance(result, Exception):
                    _LOGGER.warning("Error rendering template for %s: %s", self.entity_id, result)
                    return
                self._attr_native_value = str(result)
                self.async_write_ha_state()

            self._unsub = async_track_template_result(
                self.hass,
                [TrackTemplate(tmpl, None)],
                _handle_template_result,
            )

        self.async_write_ha_state()

    def _evaluate_state_machine(self, raw_state: Any) -> None:
        """Evaluate source state against rules and update value, icon, and color."""
        self._raw_source_state = raw_state
        matched = False
        for rule in self._parsed_rules:
            if evaluate_condition(rule["condition"], raw_state):
                self._attr_native_value = rule["state"]
                self._current_icon = rule["icon"] or self._default_icon
                self._current_color = rule["color"] or self._default_color
                self._matched_condition = rule["condition"]
                matched = True
                break

        if not matched:
            self._attr_native_value = self._default_state
            self._current_icon = self._default_icon
            self._current_color = self._default_color
            self._matched_condition = "default"

        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        if self._unsub:
            self._unsub()
            self._unsub = None

        entities_list = self.hass.data.get(f"{DOMAIN}_entities", [])
        if self in entities_list:
            entities_list.remove(self)

        await super().async_will_remove_from_hass()

    async def async_set_value(self, value: Any) -> None:
        """Set value via service."""
        self._attr_native_value = str(value) if value is not None else ""
        self.async_write_ha_state()

    async def async_reset(self) -> None:
        """Reset value to current timestamp or initial value."""
        if self._attr_device_class == "timestamp":
            self._attr_native_value = dt_util.utcnow().isoformat()
        else:
            self._attr_native_value = self._config.get(CONF_INITIAL_VALUE, self._default_state)
        self.async_write_ha_state()
