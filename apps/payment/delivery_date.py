from .utils import AVAILABLE_STATES, WAREHOUSE_CITY, state_coords, calculate_distance
import datetime
from collections import defaultdict
import math

ZONE_DELIVERY_GAPS = {
    "same_state": (1, 2),
    "near": (2, 4),
    "medium": (4, 6),
    "far": (6, 9)
}

MAX_REDUCTION = 0.9
QUANTITY_SCALING_FACTOR = 0.5
MIN_PRODUCTION_FRACTION_SAME = 0.3
MIN_PRODUCTION_FRACTION_MIXED = 0.8
FINAL_REDUCTION_MAX = 0.2
FINAL_REDUCTION_MIN = 0.1


def get_weekday_delivery_dates(start_date, delivery_gap_days):
    if delivery_gap_days <= 0:
        return start_date.strftime("%Y-%m-%d")

    days_added = 0
    current_date = start_date
    while days_added < delivery_gap_days:
        current_date += datetime.timedelta(days=1)
        if current_date.weekday() < 5:
            days_added += 1
    return current_date.strftime("%Y-%m-%d")


def calculate_single_product_days(quantity, base_days):
    if base_days == 0 or quantity == 0:
        return 0
    if quantity == 1:
        return base_days
    reduction_factor = MAX_REDUCTION * (1 - 1 / (1 + QUANTITY_SCALING_FACTOR * math.sqrt(quantity)))
    adjusted_days = base_days * (1 - reduction_factor)
    total_days = adjusted_days * quantity
    min_days = base_days * MIN_PRODUCTION_FRACTION_SAME * quantity
    return max(min_days, total_days)


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


def calculate_delivery_dates(cart):
    selected_state = cart.state
    if selected_state.lower() not in [state.lower() for state in AVAILABLE_STATES]:
        return f"Currently not delivering to {selected_state}"

    zones = group_states_by_proximity(WAREHOUSE_CITY, AVAILABLE_STATES)
    today = datetime.date.today()
    product_quantities = defaultdict(int)
    product_production_days = {}
    total_quantity = 0
    for item in cart.cartitem_cart.all():
        product_id = item.product.id
        product_quantities[product_id] += item.quantity
        product_production_days[product_id] = item.product.production_days
        total_quantity += item.quantity
    preliminary_total_days = 0
    prior_reductions = []
    for product_id, quantity in product_quantities.items():
        base_days = product_production_days[product_id]
        direct_sum = base_days * quantity
        reduced_days = calculate_single_product_days(quantity, base_days)
        preliminary_total_days += reduced_days
        if direct_sum > 0:
            reduction_percent = (direct_sum - reduced_days) / direct_sum
            prior_reductions.append(reduction_percent)
        else:
            prior_reductions.append(0)
    if total_quantity == 1 or preliminary_total_days == 0:
        total_production_days = preliminary_total_days
    else:
        avg_prior_reduction = sum(prior_reductions) / len(prior_reductions) if prior_reductions else 0
        if avg_prior_reduction >= 0.5:
            final_reduction = FINAL_REDUCTION_MIN
        elif avg_prior_reduction <= 0.2:
            final_reduction = FINAL_REDUCTION_MAX
        else:
            final_reduction = FINAL_REDUCTION_MAX - (avg_prior_reduction - 0.2) * (
                    (FINAL_REDUCTION_MAX - FINAL_REDUCTION_MIN) / 0.3)
        total_production_days = preliminary_total_days * (1 - final_reduction)
        min_days = preliminary_total_days * MIN_PRODUCTION_FRACTION_MIXED
        total_production_days = max(min_days, total_production_days)
    start_date = today + datetime.timedelta(days=math.ceil(total_production_days))
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

    first_delivery_date = get_weekday_delivery_dates(start_date, delivery_gap_start)
    last_delivery_date = get_weekday_delivery_dates(start_date, delivery_gap_end)
    return [first_delivery_date, last_delivery_date, math.ceil(total_production_days)]


def calculate_direct_sum(product_quantities, product_production_days):
    direct_sum = 0
    for product_id, quantity in product_quantities.items():
        if quantity > 0:
            direct_sum += product_production_days[product_id] * quantity
    return direct_sum
