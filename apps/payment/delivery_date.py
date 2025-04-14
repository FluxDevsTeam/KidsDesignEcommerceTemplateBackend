from .utils import AVAILABLE_STATES, WAREHOUSE_CITY, state_coords, calculate_distance
import datetime

ZONE_DELIVERY_GAPS = {
    "same_state": (1, 2),
    "near": (2, 4),
    "medium": (4, 6),
    "far": (6, 9)
}


def get_weekday_delivery_dates(start_date, delivery_gap_days):
    if delivery_gap_days <= 0:
        return start_date.strftime("%Y-%m-%d")

    days_added = 0
    while days_added < delivery_gap_days:
        start_date += datetime.timedelta(days=1)
        if start_date.weekday() < 5:
            days_added += 1
    return start_date.strftime("%Y-%m-%d")


def group_states_by_proximity(warehouse_city, available_states):
    warehouse_coord = state_coords.get(warehouse_city)
    if not warehouse_coord:
        raise ValueError("Invalid warehouse city")

    zones = {"same_state": [], "near": [], "medium": [], "far": []}

    for state, coord in state_coords.items():
        if state not in available_states:
            continue
        distance = calculate_distance(warehouse_coord, coord)
        if state == warehouse_city:
            zones["same_state"].append(state)
        elif distance <= 150:
            zones["near"].append(state)
        elif distance <= 400:
            zones["medium"].append(state)
        else:
            zones["far"].append(state)

    return zones


def calculate_delivery_dates(selected_state):
    if selected_state.lower() not in [state.lower() for state in AVAILABLE_STATES]:
        return f"Currently not delivering to {selected_state}"

    zones = group_states_by_proximity(WAREHOUSE_CITY, AVAILABLE_STATES)
    today = datetime.date.today()

    selected_zone = None
    if selected_state.lower() == WAREHOUSE_CITY.lower():
        selected_zone = "same_state"
    else:
        for zone, states in zones.items():
            if selected_state.lower() in [state.lower() for state in states]:
                selected_zone = zone
                break

    if not selected_zone:
        return f"Currently not delivering to {selected_state}"

    delivery_gap_start, delivery_gap_end = ZONE_DELIVERY_GAPS[selected_zone.lower()]

    first_delivery_date = get_weekday_delivery_dates(today, delivery_gap_start)
    last_delivery_date = get_weekday_delivery_dates(today, delivery_gap_end)

    return [first_delivery_date, last_delivery_date]
