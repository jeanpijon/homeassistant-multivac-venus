DOMAIN = "heat_exchanger"
PLATFORMS = ["climate", "sensor"]
DEFAULT_POLL_SECONDS = 1.0

CONF_HOST = "host"
CONF_PORT = "port"

HA2DEV_MODE = {"off": "idle", "auto": "auto", "cool": "cool"}
DEV2HA_MODE = {v: k for k, v in HA2DEV_MODE.items()}

# include 0 to represent 'stopped' (off)
FAN_LEVELS = ("0", "1", "2", "3")

SENSOR_MAP = {
    "temperature.out_ingress": ("°C", "temperature"),
    "temperature.out_egress": ("°C", "temperature"),
    "temperature.in_ingress": ("°C", "temperature"),
    "temperature.in_egress": ("°C", "temperature"),
    "power_factor.fan_ingress": ("%", None),
    "power_factor.fan_egress": ("%", None),
}

MANUFACTURER = "MultiVac Pardubice"
MODEL = "Venus"
DEVICE_NAME = "Venus Heat Exchanger"
