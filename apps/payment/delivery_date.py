# delivery_date.py

from .utils import AVAILABLE_STATES, WAREHOUSE_CITY, ZONE_DELIVERY_GAPS, state_coords, calculate_distance
import datetime


# Function to get the next weekday delivery date
def get_weekday_delivery_dates(start_date, delivery_gap_days):
    """
    Returns the next weekday delivery date after adding the delivery gap days.

    :param start_date: The starting date.
    :param delivery_gap_days: The number of delivery gap days.
    :return: The calculated delivery date as a string.
    """
    if delivery_gap_days <= 0:
        return start_date.strftime("%Y-%m-%d")  # Return the same day if no gap

    days_added = 0
    while days_added < delivery_gap_days:
        start_date += datetime.timedelta(days=1)
        if start_date.weekday() < 5:  # Monday to Friday
            days_added += 1
    return start_date.strftime("%Y-%m-%d")


# Function to group states by proximity from the warehouse city
def group_states_by_proximity(warehouse_city, available_states):
    warehouse_coord = state_coords.get(warehouse_city)
    if not warehouse_coord:
        raise ValueError("Invalid warehouse city")

    zones = {"same_state": [], "near": [], "medium": [], "far": []}

    for state, coord in state_coords.items():
        if state not in available_states:
            continue
        distance = calculate_distance(warehouse_coord, coord)
        if state == warehouse_city:  # Treat the warehouse city separately
            zones["same_state"].append(state)  # Same city should have a shorter delivery time
        elif distance <= 150:
            zones["near"].append(state)
        elif distance <= 400:
            zones["medium"].append(state)
        else:
            zones["far"].append(state)

    return zones


# Function to calculate the delivery date range for the selected state
def calculate_delivery_dates(selected_state):
    """
    Calculates the delivery date range for the selected state.

    :param selected_state: The state where the delivery is going.
    :return: A string representing the estimated delivery date range.
    """
    if selected_state not in AVAILABLE_STATES:
        return f"Currently not delivering to {selected_state}"

    # Get zones based on warehouse city
    zones = group_states_by_proximity(WAREHOUSE_CITY, AVAILABLE_STATES)

    today = datetime.date.today()

    # Determine the zone of the selected state
    selected_zone = None
    if selected_state == WAREHOUSE_CITY:
        selected_zone = "same_state"  # Special treatment for warehouse city
    else:
        for zone, states in zones.items():
            if selected_state in states:
                selected_zone = zone
                break

    if not selected_zone:
        return f"Currently not delivering to {selected_state}"

    # Determine the delivery gap based on the zone
    delivery_gap_start, delivery_gap_end = ZONE_DELIVERY_GAPS[selected_zone]

    # Calculate the estimated delivery date range
    first_delivery_date = get_weekday_delivery_dates(today, delivery_gap_start)
    last_delivery_date = get_weekday_delivery_dates(today, delivery_gap_end)

    return f"Estimated delivery for {selected_state} is between {first_delivery_date} and {last_delivery_date}"
