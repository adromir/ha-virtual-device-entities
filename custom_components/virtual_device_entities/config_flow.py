"""Config Flow and Options Flow for Virtual Device Entities."""
from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_DEVICE_NAME,
    CONF_BASE_DEVICE_ID,
    CONF_ATTACH_TO_BASE,
    CONF_ENTITIES,
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
    CONF_MIN_VALUE,
    CONF_MAX_VALUE,
    CONF_STEP_VALUE,
    TYPE_STATE_MACHINE,
    TYPE_MIRROR,
    TYPE_TEMPLATE,
    TYPE_MANUAL,
    PLATFORM_SENSOR,
    PLATFORM_BINARY_SENSOR,
    PLATFORM_SWITCH,
    PLATFORM_NUMBER,
    PLATFORM_BUTTON,
    PLATFORM_TEXT,
)


class VirtualDeviceEntitiesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Virtual Device Entities."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow state."""
        self._device_data: dict[str, Any] = {}
        self._selected_entity_type: str = TYPE_STATE_MACHINE

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 1: Define the Virtual Device and choose the initial entity type."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._device_data = {
                CONF_DEVICE_NAME: user_input[CONF_DEVICE_NAME],
                CONF_BASE_DEVICE_ID: user_input.get(CONF_BASE_DEVICE_ID),
                CONF_ATTACH_TO_BASE: user_input.get(CONF_ATTACH_TO_BASE, False),
                CONF_ENTITIES: {},
            }
            self._selected_entity_type = user_input.get(CONF_ENTITY_TYPE, TYPE_STATE_MACHINE)
            return await self.async_step_add_entity()

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_NAME, default="Virtuelle Waschmaschine"): selector.TextSelector(),
                vol.Optional(CONF_BASE_DEVICE_ID): selector.DeviceSelector(),
                vol.Optional(CONF_ATTACH_TO_BASE, default=False): selector.BooleanSelector(),
                vol.Required(
                    CONF_ENTITY_TYPE, default=TYPE_STATE_MACHINE
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=TYPE_STATE_MACHINE,
                                label="State & Color Machine (Zustand mit eigenen Farben & Icons)",
                            ),
                            selector.SelectOptionDict(
                                value=TYPE_MIRROR,
                                label="Mirror / Proxy (Entität eines anderen Geräts spiegeln, z. B. Verbrauch)",
                            ),
                            selector.SelectOptionDict(
                                value=TYPE_TEMPLATE,
                                label="Template Calculation (Jinja2-Formel / Schätzung)",
                            ),
                            selector.SelectOptionDict(
                                value=TYPE_MANUAL,
                                label="Manual Helper (Datum, Zahl, Notiz, Schalter, Taster)",
                            ),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_add_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 2: Configure the specific entity based on selected type."""
        errors: dict[str, str] = {}

        if user_input is not None:
            entity_id = str(uuid.uuid4())[:8]
            entity_cfg = {
                CONF_ENTITY_ID: entity_id,
                CONF_ENTITY_TYPE: self._selected_entity_type,
                **user_input,
            }
            self._device_data[CONF_ENTITIES][entity_id] = entity_cfg

            title = self._device_data.get(CONF_DEVICE_NAME, "Virtual Device")
            return self.async_create_entry(
                title=title,
                data=self._device_data,
            )

        schema_dict: dict[Any, Any] = {}

        if self._selected_entity_type == TYPE_STATE_MACHINE:
            schema_dict = {
                vol.Required(CONF_ENTITY_NAME, default="Betriebsstatus"): selector.TextSelector(),
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(),
                vol.Required(
                    CONF_STATE_RULES,
                    default=(
                        "< 3.5 | Standby | mdi:washing-machine-off | #9e9e9e\n"
                        "3.5 - 200 | Spülen | mdi:washing-machine | #2196f3\n"
                        "> 200 | Schleudern | mdi:washing-machine-alert | #ff9800"
                    ),
                ): selector.TemplateSelector(),
                vol.Optional(CONF_DEFAULT_STATE, default="Standby"): selector.TextSelector(),
                vol.Optional(CONF_DEFAULT_ICON, default="mdi:washing-machine"): selector.IconSelector(),
                vol.Optional(CONF_DEFAULT_COLOR, default="#9e9e9e"): selector.TextSelector(),
                vol.Optional(CONF_PLATFORM, default=PLATFORM_SENSOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[PLATFORM_SENSOR],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }

        elif self._selected_entity_type == TYPE_MIRROR:
            schema_dict = {
                vol.Required(CONF_ENTITY_NAME, default="Sensor"): selector.TextSelector(),
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(),
                vol.Optional(CONF_ICON): selector.IconSelector(),
                vol.Optional(CONF_UNIT): selector.TextSelector(),
                vol.Optional(CONF_DEVICE_CLASS): selector.TextSelector(),
                vol.Optional(CONF_PLATFORM, default=PLATFORM_SENSOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[PLATFORM_SENSOR, PLATFORM_BINARY_SENSOR],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }

        elif self._selected_entity_type == TYPE_TEMPLATE:
            schema_dict = {
                vol.Required(CONF_ENTITY_NAME, default="Geschätzter Batteriestand"): selector.TextSelector(),
                vol.Required(
                    CONF_TEMPLATE,
                    default="{{ 100 - ((as_timestamp(now()) - as_timestamp(states('sensor.akku_gewechselt_am'))) / 86400 * 1.5) | round(0) }}",
                ): selector.TemplateSelector(),
                vol.Optional(CONF_ICON, default="mdi:battery-heart-variant"): selector.IconSelector(),
                vol.Optional(CONF_UNIT, default="%"): selector.TextSelector(),
                vol.Optional(CONF_DEVICE_CLASS, default="battery"): selector.TextSelector(),
                vol.Optional(CONF_PLATFORM, default=PLATFORM_SENSOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[PLATFORM_SENSOR, PLATFORM_BINARY_SENSOR],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }

        elif self._selected_entity_type == TYPE_MANUAL:
            schema_dict = {
                vol.Required(CONF_ENTITY_NAME, default="Akku gewechselt am"): selector.TextSelector(),
                vol.Required(CONF_PLATFORM, default=PLATFORM_SENSOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            PLATFORM_SENSOR,
                            PLATFORM_BINARY_SENSOR,
                            PLATFORM_SWITCH,
                            PLATFORM_NUMBER,
                            PLATFORM_BUTTON,
                            PLATFORM_TEXT,
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_INITIAL_VALUE, default="2026-01-15"): selector.TextSelector(),
                vol.Optional(CONF_ICON, default="mdi:calendar-clock"): selector.IconSelector(),
                vol.Optional(CONF_UNIT): selector.TextSelector(),
                vol.Optional(CONF_DEVICE_CLASS, default="timestamp"): selector.TextSelector(),
            }

        return self.async_show_form(
            step_id="add_entity",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow handler."""
        return VirtualDeviceEntitiesOptionsFlow(config_entry)


class VirtualDeviceEntitiesOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for adding, editing, and managing entities of a virtual device."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._new_entity_type: str = TYPE_STATE_MACHINE

    @property
    def config_entry(self) -> config_entries.ConfigEntry:
        """Return the config entry."""
        return getattr(self, "_config_entry", None) or super().config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show main options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_entity_type", "edit_device"],
        )

    async def async_step_edit_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Edit device metadata."""
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            updated = dict(current)
            updated[CONF_DEVICE_NAME] = user_input[CONF_DEVICE_NAME]
            updated[CONF_BASE_DEVICE_ID] = user_input.get(CONF_BASE_DEVICE_ID)
            updated[CONF_ATTACH_TO_BASE] = user_input.get(CONF_ATTACH_TO_BASE, False)
            return self.async_create_entry(title="", data=updated)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_NAME,
                    default=current.get(CONF_DEVICE_NAME, "Virtuelle Waschmaschine"),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_BASE_DEVICE_ID,
                    description={"suggested_value": current.get(CONF_BASE_DEVICE_ID)},
                ): selector.DeviceSelector(),
                vol.Optional(
                    CONF_ATTACH_TO_BASE,
                    default=current.get(CONF_ATTACH_TO_BASE, False),
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="edit_device", data_schema=schema)

    async def async_step_add_entity_type(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Select type of new entity to add to this device."""
        if user_input is not None:
            self._new_entity_type = user_input[CONF_ENTITY_TYPE]
            return await self.async_step_add_entity_details()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENTITY_TYPE, default=TYPE_STATE_MACHINE
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=TYPE_STATE_MACHINE,
                                label="State & Color Machine (Zustand mit eigenen Farben & Icons)",
                            ),
                            selector.SelectOptionDict(
                                value=TYPE_MIRROR,
                                label="Mirror / Proxy (Entität eines anderen Geräts spiegeln)",
                            ),
                            selector.SelectOptionDict(
                                value=TYPE_TEMPLATE,
                                label="Template Calculation (Jinja2-Formel)",
                            ),
                            selector.SelectOptionDict(
                                value=TYPE_MANUAL,
                                label="Manual Helper (Datum, Zahl, Notiz, Schalter, Taster)",
                            ),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="add_entity_type", data_schema=schema)

    async def async_step_add_entity_details(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure and add the new entity."""
        current = {**self.config_entry.data, **self.config_entry.options}
        entities = dict(current.get(CONF_ENTITIES, {}))

        if user_input is not None:
            ent_id = str(uuid.uuid4())[:8]
            entities[ent_id] = {
                CONF_ENTITY_ID: ent_id,
                CONF_ENTITY_TYPE: self._new_entity_type,
                **user_input,
            }
            updated = dict(current)
            updated[CONF_ENTITIES] = entities
            return self.async_create_entry(title="", data=updated)

        schema_dict: dict[Any, Any] = {}
        if self._new_entity_type == TYPE_STATE_MACHINE:
            schema_dict = {
                vol.Required(CONF_ENTITY_NAME, default="Status"): selector.TextSelector(),
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(),
                vol.Required(
                    CONF_STATE_RULES,
                    default=(
                        "< 3.5 | Standby | mdi:washing-machine-off | #9e9e9e\n"
                        "3.5 - 200 | Spülen | mdi:washing-machine | #2196f3\n"
                        "> 200 | Schleudern | mdi:washing-machine-alert | #ff9800"
                    ),
                ): selector.TemplateSelector(),
                vol.Optional(CONF_DEFAULT_STATE, default="Standby"): selector.TextSelector(),
                vol.Optional(CONF_DEFAULT_ICON, default="mdi:chip"): selector.IconSelector(),
                vol.Optional(CONF_DEFAULT_COLOR, default="#9e9e9e"): selector.TextSelector(),
                vol.Optional(CONF_PLATFORM, default=PLATFORM_SENSOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[PLATFORM_SENSOR],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        elif self._new_entity_type == TYPE_MIRROR:
            schema_dict = {
                vol.Required(CONF_ENTITY_NAME, default="Sensor"): selector.TextSelector(),
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(),
                vol.Optional(CONF_ICON, default="mdi:flash"): selector.IconSelector(),
                vol.Optional(CONF_UNIT): selector.TextSelector(),
                vol.Optional(CONF_DEVICE_CLASS): selector.TextSelector(),
                vol.Optional(CONF_PLATFORM, default=PLATFORM_SENSOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[PLATFORM_SENSOR, PLATFORM_BINARY_SENSOR],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        elif self._new_entity_type == TYPE_TEMPLATE:
            schema_dict = {
                vol.Required(CONF_ENTITY_NAME, default="Berechneter Wert"): selector.TextSelector(),
                vol.Required(CONF_TEMPLATE, default="{{ states('sensor.xyz') }}"): selector.TemplateSelector(),
                vol.Optional(CONF_ICON, default="mdi:calculator"): selector.IconSelector(),
                vol.Optional(CONF_UNIT): selector.TextSelector(),
                vol.Optional(CONF_DEVICE_CLASS): selector.TextSelector(),
                vol.Optional(CONF_PLATFORM, default=PLATFORM_SENSOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[PLATFORM_SENSOR, PLATFORM_BINARY_SENSOR],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        elif self._new_entity_type == TYPE_MANUAL:
            schema_dict = {
                vol.Required(CONF_ENTITY_NAME, default="Helfer"): selector.TextSelector(),
                vol.Required(CONF_PLATFORM, default=PLATFORM_SENSOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            PLATFORM_SENSOR,
                            PLATFORM_BINARY_SENSOR,
                            PLATFORM_SWITCH,
                            PLATFORM_NUMBER,
                            PLATFORM_BUTTON,
                            PLATFORM_TEXT,
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_INITIAL_VALUE, default=""): selector.TextSelector(),
                vol.Optional(CONF_ICON, default="mdi:chip"): selector.IconSelector(),
                vol.Optional(CONF_UNIT): selector.TextSelector(),
                vol.Optional(CONF_DEVICE_CLASS): selector.TextSelector(),
            }

        return self.async_show_form(step_id="add_entity_details", data_schema=vol.Schema(schema_dict))
