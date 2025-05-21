import math
from .utils import AVAILABLE_STATES, state_coords, calculate_distance, WAREHOUSE_CITY
from .variables import fee_per_km, base_fee, weight_fee, size_fee

# FEE_PER_KM = fee_per_km
# BASE_FEE = base_fee
# WEIGHT_FEE = weight_fee
# SIZE_FEE = size_fee

FEE_PER_KM = 100
BASE_FEE = 1500
WEIGHT_FEE = 1000
SIZE_FEE = 1000

DISTANCE_TIERS = [
    (1, 0),
    (150, 0.019),
    (400, 0.016),
    (800, 0.014),
    (float('inf'), 0.0125)
]

QUANTITY_TIERS_LIGHT = [
    (5, 1.2),
    (10, 1.15),
    (20, 1.1),
    (float('inf'), 1.0)
]

QUANTITY_TIERS_HEAVY = [
    (150, [(5, 1.3), (10, 1.8), (20, 2.5), (float('inf'), 4.0)]),
    (400, [(5, 1.3), (10, 1.9), (20, 2.7), (float('inf'), 4.5)]),
    (800, [(5, 1.3), (10, 2.0), (20, 2.9), (float('inf'), 5.8)]),
    (float('inf'), [(5, 1.3), (10, 2.2), (20, 3.2), (float('inf'), 8.5)])
]

WEIGHT_MAPPING = {
    'Very Light': 0.5,
    'Light': 1.0,
    'Medium': 2.0,
    'Heavy': 3.0,
    'Very Heavy': 4.0,
    'XXHeavy': 5.0
}

SIZE_MAPPING = {
    'Very Small': 0.5,
    'Small': 1.0,
    'Medium': 2.0,
    'Large': 3.0,
    'Very Large': 4.0,
    'XXL': 5.0
}

def is_valid_pair(weight, size):
    weight_values = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
    size_values = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
    weight_idx = weight_values.index(WEIGHT_MAPPING[weight])
    size_idx = size_values.index(SIZE_MAPPING[size])
    return abs(weight_idx - size_idx) <= 1

def calculate_delivery_fee(cart):
    try:
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

        cart_items = cart.cartitem_cart.all()
        if not cart_items:
            raise ValueError("Cart is empty")

        total_fee = BASE_FEE
        rate_per_unit_base = 0
        light_item_scaling = 0.4 if distance < 150 else 0.5

        for threshold, multiplier in DISTANCE_TIERS:
            if distance < threshold:
                rate_per_unit_base = FEE_PER_KM * multiplier
                break
        else:
            rate_per_unit_base = FEE_PER_KM * DISTANCE_TIERS[-1][1]

        has_heavy_item = any(
            (WEIGHT_FEE * WEIGHT_MAPPING.get(item.product.weight, 0) +
             SIZE_FEE * SIZE_MAPPING.get(item.product.dimensional_size, 0)) >= 4000
            for item in cart_items
        )

        for item in cart_items:
            product = item.product
            quantity = item.quantity
            if quantity <= 0 or not isinstance(quantity, int):
                raise ValueError(f"Invalid quantity for product {product.name}: {quantity}")

            weight_choice = product.weight
            size_choice = product.dimensional_size
            if not is_valid_pair(weight_choice, size_choice):
                raise ValueError(f"Invalid weight-size pair: {weight_choice}, {size_choice}")

            weight_multiplier = WEIGHT_MAPPING.get(weight_choice)
            size_multiplier = SIZE_MAPPING.get(size_choice)
            if weight_multiplier is None or size_multiplier is None:
                raise ValueError(f"Invalid weight or size choice: {weight_choice}, {size_choice}")

            weight_fee = WEIGHT_FEE * weight_multiplier
            size_fee = SIZE_FEE * size_multiplier
            item_multiplier = weight_fee + size_fee
            item_fee = item_multiplier * quantity

            quantity_multiplier = 1.0
            tiers = QUANTITY_TIERS_LIGHT if item_multiplier < 4000 else None
            if item_multiplier >= 4000:
                for dist_threshold, qty_tiers in QUANTITY_TIERS_HEAVY:
                    if distance < dist_threshold:
                        tiers = qty_tiers
                        break
                else:
                    tiers = QUANTITY_TIERS_HEAVY[-1][1]
            for qty_threshold, qty_multiplier in tiers:
                if quantity <= qty_threshold:
                    quantity_multiplier = qty_multiplier
                    break
            else:
                quantity_multiplier = tiers[-1][1]

            item_fee *= quantity_multiplier

            rate_per_unit = rate_per_unit_base * min(item_multiplier / 1000, 5)
            if item_multiplier >= 4000 and quantity >= 20:
                rate_per_unit *= (1 + 0.21 * (quantity / 20))
            elif item_multiplier < 4000 and quantity >= 5:
                rate_per_unit *= (1 + 0.18 * (quantity / 20))

            if has_heavy_item and item_multiplier < 4000 and quantity < 10:
                item_fee *= light_item_scaling
                distance_fee = item_fee * rate_per_unit * distance * light_item_scaling
            else:
                distance_fee = item_fee * rate_per_unit * distance

            total_fee += item_fee + distance_fee

        return round(total_fee, -2)

    except ValueError as e:
        raise
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")