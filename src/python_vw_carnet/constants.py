import re
from enum import Enum

BASE_URL = "https://b-h-s.spr.us00.p.con-veh.net"
IDENTITY_URL = "https://identity.na.vwgroup.io"
ANDROID_CLIENT_ID = "59992128-69a9-42c3-8621-7942041ba824_MYVW_ANDROID"
REDIRECT_URI = "kombi:///login"
APP_VERSION = "2026.3.11-8768"
DEVICE_MODEL = "SM-G975U"
DEVICE_OS = "30"
DEFAULT_LOCALE = "en-US"
DEFAULT_COUNTRY = "US"
USER_AGENT_APP = "okhttp/5.3.2"
USER_AGENT_WEB = (
    "Mozilla/5.0 (Linux; Android 11; SM-G975U Build/RP1A.200720.012; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
    "Chrome/83.0.4103.106 Mobile Safari/537.36"
)
WINDOW_IDK_PATTERN = re.compile(r"window\._IDK\s*=\s*\{", re.IGNORECASE)


class BatteryCapacity(Enum):
    SIXTY_TWO = 62
    EIGHTY_TWO = 82


# This is a map of `modelCode` (found in GarageResponse) to battery capacity
BATTERY_CAPACITIES: dict[str, BatteryCapacity] = {
    "E812MJ": BatteryCapacity.SIXTY_TWO,
    "E813MN": BatteryCapacity.EIGHTY_TWO,
    "E813SN": BatteryCapacity.EIGHTY_TWO,
    "E813MJ": BatteryCapacity.SIXTY_TWO,
    "E814MN": BatteryCapacity.EIGHTY_TWO,
    "E814SN": BatteryCapacity.EIGHTY_TWO,
    "E815MN": BatteryCapacity.EIGHTY_TWO,
    "E815SN": BatteryCapacity.EIGHTY_TWO,
}
