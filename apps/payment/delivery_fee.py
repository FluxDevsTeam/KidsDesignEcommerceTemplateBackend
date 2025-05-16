import math
from .utils import AVAILABLE_STATES, state_coords, calculate_distance, WAREHOUSE_CITY

FEE_PER_KM = 3000
BASE_FEE = 3000
WEIGHT_FEE = 2000
SIZE_FEE = 2000
EXPONENT = 0.9

DISTANCE_TIERS = [
    (150, 2.0),
    (400, 3.0),
    (float('inf'), 4.0),
]

WEIGHT_MAPPING = {
    'Very Light': 0.3,
    'Light': 0.4,
    'Medium': 0.5,
    'Heavy': 0.6,
    'Very Heavy': 0.7,
    'XXHeavy': 0.8
}

SIZE_MAPPING = {
    'Very Small': 0.4,
    'Small': 0.5,
    'Medium': 0.6,
    'Large': 0.7,
    'Very Large': 0.8,
    'XXL': 0.9
}

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

        total_multiplier = 0
        for item in cart_items:
            product = item.product
            quantity = item.quantity
            if quantity <= 0:
                raise ValueError(f"Invalid quantity for product {product.name}: {quantity}")

            weight_choice = product.weight
            size_choice = product.dimensional_size
            weight_multiplier = WEIGHT_MAPPING.get(weight_choice)
            size_multiplier = SIZE_MAPPING.get(size_choice)
            if weight_multiplier is None or size_multiplier is None:
                raise ValueError(f"Invalid weight or size choice: {weight_choice}, {size_choice}")

            weight_fee = WEIGHT_FEE * weight_multiplier
            size_fee = SIZE_FEE * size_multiplier
            item_multiplier = weight_fee + size_fee
            adjusted_multiplier = item_multiplier * (quantity ** EXPONENT)
            total_multiplier += adjusted_multiplier

        rate_per_kg = 0
        for threshold, multiplier in DISTANCE_TIERS:
            if distance < threshold:
                rate_per_kg = FEE_PER_KM * multiplier
                break
        else:
            rate_per_kg = FEE_PER_KM * DISTANCE_TIERS[-1][1]

        distance_fee = total_multiplier * rate_per_kg
        total_fee = (BASE_FEE + distance_fee) / 10
        return round(total_fee)

    except ValueError as e:
        raise
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")