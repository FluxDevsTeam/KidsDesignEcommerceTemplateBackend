import datetime
from math import radians, sin, cos, sqrt, atan2

AVAILABLE_STATES = ["Lagos", "Ogun", "Abuja", "Kaduna", "Anambra", "Cross River"]
WAREHOUSE_CITY = "Lagos"


state_coords = {
    "Lagos": (6.5244, 3.3792),
    "Ogun": (7.1604, 3.3481),
    "Oyo": (7.3775, 3.9470),
    "Osun": (7.5629, 4.5190),
    "Ondo": (7.1000, 4.8419),
    "Ekiti": (7.7180, 5.3101),
    "Edo": (6.5243, 5.9500),
    "Delta": (5.4891, 5.9891),
    "Kwara": (8.4800, 4.5400),
    "Kogi": (7.8000, 6.7333),
    "Niger": (9.6000, 6.5500),
    "Abuja": (9.0765, 7.3986),
    "Kaduna": (10.5105, 7.4165),
    "Kano": (12.0000, 8.5167),
    "Borno": (11.8333, 13.1500),
    "Yobe": (12.0000, 11.5000),
    "Sokoto": (13.0059, 5.2476),
    "Zamfara": (12.0000, 6.2333),
    "Taraba": (7.8704, 10.7903),
    "Gombe": (10.2900, 11.1700),
    "Bauchi": (10.3000, 9.8333),
    "Adamawa": (9.3265, 12.3984),
    "Katsina": (12.9855, 7.6170),
    "Jigawa": (12.2280, 9.5616),
    "Nasarawa": (8.4910, 8.5140),
    "Benue": (7.1907, 9.5616),
    "Kebbi": (12.4500, 4.1990),
    "Bayelsa": (4.9240, 6.2649),
    "Rivers": (4.8436, 6.9112),
    "Akwa Ibom": (5.0280, 7.9319),
    "Cross River": (5.9631, 8.3309),
    "Enugu": (6.4599, 7.5489),
    "Anambra": (6.2209, 6.9366),
    "Abia": (5.5320, 7.4860),
    "Imo": (5.4897, 7.0143),
    "Ebonyi": (6.3249, 8.1137),
    "FCT - Abuja": (9.0765, 7.3986),
}


def calculate_distance(coord1, coord2):
    R = 6371.0
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

