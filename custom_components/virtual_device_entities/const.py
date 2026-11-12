"""Constants for the Virtual Device Entities integration."""

DOMAIN = "virtual_device_entities"

# Device configuration keys
CONF_DEVICE_NAME = "device_name"
CONF_BASE_DEVICE_ID = "base_device_id"
CONF_ATTACH_TO_BASE = "attach_to_base_device"
CONF_AREA_ID = "area_id"
CONF_ENTITIES = "entities"

# Entity configuration keys
CONF_ENTITY_ID = "id"
CONF_ENTITY_TYPE = "entity_type"
CONF_ENTITY_NAME = "name"
CONF_PLATFORM = "platform"
CONF_ICON = "icon"
CONF_UNIT = "unit_of_measurement"
CONF_DEVICE_CLASS = "device_class"
CONF_SOURCE_ENTITY = "source_entity"
CONF_STATE_RULES = "state_rules"
CONF_DEFAULT_STATE = "default_state"
CONF_DEFAULT_ICON = "default_icon"
CONF_DEFAULT_COLOR = "default_color"
CONF_TEMPLATE = "template"
CONF_INITIAL_VALUE = "initial_value"
CONF_MIN_VALUE = "min_value"
CONF_MAX_VALUE = "max_value"
CONF_STEP_VALUE = "step_value"

# Entity types
TYPE_STATE_MACHINE = "state_machine"
TYPE_MIRROR = "mirror"
TYPE_TEMPLATE = "template"
TYPE_MANUAL = "manual"

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
