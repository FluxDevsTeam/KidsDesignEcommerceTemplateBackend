from .utils import AVAILABLE_STATES, state_coords, calculate_distance, WAREHOUSE_CITY
from ..cart.models import CartItem
from .variables import fee_per_km, base_fee, weight_fee, size_fee

FEE_PER_KM = fee_per_km
BASE_FEE = base_fee
WEIGHT_FEE = weight_fee
SIZE_FEE = size_fee

# Quantity thresholds for different pricing tiers
QUANTITY_THRESHOLDS = [
    (3, 1800),
    (5, 1500),
    (10, 1200),
    (15, 1000),
    (20, 800),
    (50, 500),
    (100, 200),
]

WEIGHT_CATEGORIES = {
    "Very Light": 1,
    "Light": 2,
    "Medium": 3,
    "Heavy": 4,
    "Very Heavy": 5,
    "XXHeavy": 6
}

SIZE_CATEGORIES = {
    "Very Small": 1,
    "Small": 2,
    "Medium": 3,
    "Large": 4,
    "Very Large": 5,
    "XXL": 5
}


def get_weight_fee(weight, quantity):
    if weight not in WEIGHT_CATEGORIES:
        return 0
    weight_fee_calc = WEIGHT_FEE * WEIGHT_CATEGORIES[weight] * quantity
    return weight_fee_calc


def get_size_fee(size, quantity):
    if size not in SIZE_CATEGORIES:
        return 0
    size_fee_calc = SIZE_FEE * SIZE_CATEGORIES[size] * quantity
    return size_fee_calc


def get_item_fee(quantity):
    for threshold, fee in QUANTITY_THRESHOLDS:
        if quantity <= threshold:
            return fee
    return BASE_FEE


def calculate_delivery_fee(cart):
    selected_state = cart.state

    if selected_state.lower() not in [state.lower() for state in AVAILABLE_STATES]:
        return 0

    state_coord_lower = {key.lower(): value for key, value in state_coords.items()}
    warehouse_coord = state_coord_lower.get(WAREHOUSE_CITY.lower())
    state_coord = state_coord_lower.get(selected_state)

    if not warehouse_coord or not state_coord:
        return 3
    cart_item = CartItem.objects.filter(cart=cart)
    if not cart_item:
        return 4
    total_delivery_fee = []
    for item in cart_item:
        weight = item.product.weight
        quantity = item.quantity
        size = item.product.dimensional_size

        distance = calculate_distance(warehouse_coord, state_coord)
        delivery_fee = BASE_FEE + (distance * FEE_PER_KM)

        weight_fee_calc = get_weight_fee(weight, item.quantity)

        size_fee_calc = get_size_fee(size, quantity)

        item_fee_calc = get_item_fee(quantity) * quantity

        total_delivery_fee.append(delivery_fee + weight_fee_calc + size_fee_calc + item_fee_calc)
    return round(sum(total_delivery_fee))
