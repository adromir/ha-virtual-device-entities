"""Config Flow and Options Flow for Virtual Device Entities."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_ENTITY_NAME,
    CONF_PLATFORM_TYPE,
    CONF_INITIAL_VALUE,
    CONF_ICON,
    CONF_UNIT,
    CONF_DEVICE_CLASS,
    CONF_LINKED_ENTITY,
    CONF_MIN_VALUE,
    CONF_MAX_VALUE,
    CONF_STEP_VALUE,
    PLATFORM_SENSOR,
    PLATFORM_BINARY_SENSOR,
    PLATFORM_SWITCH,
    PLATFORM_NUMBER,
    PLATFORM_BUTTON,
    PLATFORM_TEXT,
    SUPPORTED_PLATFORMS,
)


class VirtualDeviceEntitiesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Virtual Device Entities."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            title = user_input.get(CONF_ENTITY_NAME, "Virtual Entity")
            return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_ENTITY_NAME, default="Virtual Entity"): selector.TextSelector(),
                vol.Required(
                    CONF_PLATFORM_TYPE, default=PLATFORM_SENSOR
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=PLATFORM_SENSOR, label="Sensor (Value / Status / Date)"),
                            selector.SelectOptionDict(value=PLATFORM_BINARY_SENSOR, label="Binary Sensor (On / Off / Condition)"),
                            selector.SelectOptionDict(value=PLATFORM_SWITCH, label="Switch (Virtual Toggle)"),
                            selector.SelectOptionDict(value=PLATFORM_NUMBER, label="Number (Slider / Setpoint)"),
                            selector.SelectOptionDict(value=PLATFORM_BUTTON, label="Button (Action / Reset Trigger)"),
                            selector.SelectOptionDict(value=PLATFORM_TEXT, label="Text (Notes / Serial / Instructions)"),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_DEVICE_ID): selector.DeviceSelector(),
                vol.Optional(CONF_INITIAL_VALUE, default=""): selector.TextSelector(),
                vol.Optional(CONF_ICON, default="mdi:chip"): selector.IconSelector(),
                vol.Optional(CONF_UNIT): selector.TextSelector(),
                vol.Optional(CONF_DEVICE_CLASS): selector.TextSelector(),
                vol.Optional(CONF_LINKED_ENTITY): selector.EntitySelector(),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return VirtualDeviceEntitiesOptionsFlow(config_entry)


class VirtualDeviceEntitiesOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Virtual Device Entities."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENTITY_NAME,
                    default=current.get(CONF_ENTITY_NAME, "Virtual Entity"),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_INITIAL_VALUE,
                    default=current.get(CONF_INITIAL_VALUE, ""),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_ICON,
                    default=current.get(CONF_ICON, "mdi:chip"),
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_UNIT,
                    description={"suggested_value": current.get(CONF_UNIT, "")},
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_DEVICE_CLASS,
                    description={"suggested_value": current.get(CONF_DEVICE_CLASS, "")},
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_LINKED_ENTITY,
                    description={"suggested_value": current.get(CONF_LINKED_ENTITY)},
                ): selector.EntitySelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
