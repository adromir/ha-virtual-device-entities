"""Constants for the Virtual Device Entities integration."""

DOMAIN = "virtual_device_entities"

# Configuration keys
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"
CONF_ENTITY_NAME = "entity_name"
CONF_PLATFORM_TYPE = "platform_type"
CONF_INITIAL_VALUE = "initial_value"
CONF_ICON = "icon"
CONF_UNIT = "unit_of_measurement"
CONF_DEVICE_CLASS = "device_class"
CONF_LINKED_ENTITY = "linked_entity"
CONF_MIN_VALUE = "min_value"
CONF_MAX_VALUE = "max_value"
CONF_STEP_VALUE = "step_value"

# Supported platform types
PLATFORM_SENSOR = "sensor"
PLATFORM_BINARY_SENSOR = "binary_sensor"
PLATFORM_SWITCH = "switch"
PLATFORM_NUMBER = "number"
PLATFORM_BUTTON = "button"
PLATFORM_TEXT = "text"

SUPPORTED_PLATFORMS = [
    PLATFORM_SENSOR,
    PLATFORM_BINARY_SENSOR,
    PLATFORM_SWITCH,
    PLATFORM_NUMBER,
    PLATFORM_BUTTON,
    PLATFORM_TEXT,
]

# Service names
SERVICE_SET_VALUE = "set_value"
SERVICE_RESET = "reset"
ATTR_VALUE = "value"
