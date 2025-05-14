from .utils import AVAILABLE_STATES, state_coords, calculate_distance, WAREHOUSE_CITY
from .variables import fee_per_km, base_fee, weight_fee, size_fee
import math

FEE_PER_KM = fee_per_km
BASE_FEE = base_fee
WEIGHT_FEE = weight_fee
SIZE_FEE = size_fee

DISTANCE_TIERS = [
    (100, 0.5),
    (500, 1.0),
    (1000, 1.5),
    (float('inf'), 2.0),
]

DIM_FACTOR = 6000

WEIGHT_MAPPING = {
    'Very Light': 0.3,
    'Light': 0.5,
    'Medium': 1.5,
    'Heavy': 3.0,
    'Very Heavy': 5.0,
    'XXHeavy': 10.0
}

SIZE_MAPPING = {
    'Very Small': (15, 10, 5),
    'Small': (20, 15, 10),
    'Medium': (30, 20, 15),
    'Large': (40, 30, 20),
    'Very Large': (50, 40, 30),
    'XXL': (60, 50, 40)
}


def get_volumetric_weight(weight_choice, size_choice):
    if not weight_choice or not size_choice:
        raise ValueError("Weight or size choice missing for product")
    actual_weight = WEIGHT_MAPPING.get(weight_choice)
    if actual_weight is None:
        raise ValueError(f"Invalid weight choice: {weight_choice}")
    dimensions = SIZE_MAPPING.get(size_choice)
    if dimensions is None:
        raise ValueError(f"Invalid size choice: {size_choice}")
    length, width, height = dimensions
    dimensional_weight = (length * width * height) / DIM_FACTOR
    return max(actual_weight, dimensional_weight)


def get_distance_rate(distance):
    for threshold, multiplier in DISTANCE_TIERS:
        if distance < threshold:
            return FEE_PER_KM * multiplier
    return FEE_PER_KM * DISTANCE_TIERS[-1][1]


def get_quantity_factor(total_quantity):
    if total_quantity <= 0:
        raise ValueError("Total quantity must be positive")
    return 1 - 0.3 * (1 - 1 / (1 + 0.1 * total_quantity))


def calculate_delivery_fee(cart):
    selected_state = cart.state
    if not selected_state or selected_state.lower() not in [state.lower() for state in AVAILABLE_STATES]:
        raise ValueError(f"Invalid or missing delivery state: {selected_state}")

    state_coord_lower = {key.lower(): value for key, value in state_coords.items()}
    warehouse_coord = state_coord_lower.get(WAREHOUSE_CITY.lower())
    state_coord = state_coord_lower.get(selected_state.lower())

    if not warehouse_coord:
        raise ValueError(f"Warehouse coordinates not found for {WAREHOUSE_CITY}")
    if not state_coord:
        raise ValueError(f"Coordinates not found for state: {selected_state}")

    distance = calculate_distance(warehouse_coord, state_coord)
    cart_items = cart.items.all()
    if not cart_items:
        raise ValueError("Cart is empty")

    total_volumetric_weight = 0
    total_quantity = 0
    for item in cart_items:
        weight_choice = item.product.weight
        size_choice = item.product.dimensional_size
        quantity = item.quantity
        if quantity <= 0:
            raise ValueError(f"Invalid quantity for product {item.product.name}: {quantity}")
        volumetric_weight = get_volumetric_weight(weight_choice, size_choice)
        total_volumetric_weight += volumetric_weight * quantity
        total_quantity += quantity

    quantity_factor = get_quantity_factor(total_quantity)
    rate_per_kg = get_distance_rate(distance)
    distance_fee = total_volumetric_weight * rate_per_kg * quantity_factor
    weight_fee = total_volumetric_weight * WEIGHT_FEE * quantity_factor
    size_fee = total_volumetric_weight * SIZE_FEE * (1 + 0.1 * math.log(1 + total_volumetric_weight)) * quantity_factor
    total_fee = BASE_FEE + distance_fee + weight_fee + size_fee
    return round(total_fee)