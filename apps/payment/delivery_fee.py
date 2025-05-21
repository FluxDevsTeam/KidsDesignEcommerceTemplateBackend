import math
from decimal import Decimal, ROUND_HALF_UP

from .utils import AVAILABLE_STATES, state_coords, calculate_distance, WAREHOUSE_CITY
from .variables import fee_per_km, base_fee, weight_fee, size_fee

# FEE_PER_KM = fee_per_km
# BASE_FEE = base_fee
# WEIGHT_FEE = weight_fee
# SIZE_FEE = size_fee
print(fee_per_km)
print(weight_fee)
print(base_fee)
print(size_fee)
print(type(size_fee))
# print(type(Decimal(size_fee)))

FEE_PER_KM = Decimal('100')
BASE_FEE = Decimal('1500')
WEIGHT_FEE = Decimal('1000')
SIZE_FEE = Decimal('1000')

DISTANCE_TIERS = [
    (1, Decimal('0')),
    (150, Decimal('0.019')),
    (400, Decimal('0.016')),
    (800, Decimal('0.014')),
    (float('inf'), Decimal('0.0125'))
]

QUANTITY_TIERS_LIGHT = [
    (5, Decimal('1.2')),
    (10, Decimal('1.15')),
    (20, Decimal('1.1')),
    (float('inf'), Decimal('1.0'))
]

QUANTITY_TIERS_HEAVY = [
    (150, [(5, Decimal('1.3')), (10, Decimal('1.8')), (20, Decimal('2.5')), (float('inf'), Decimal('4.0'))]),
    (400, [(5, Decimal('1.3')), (10, Decimal('1.9')), (20, Decimal('2.7')), (float('inf'), Decimal('4.5'))]),
    (800, [(5, Decimal('1.3')), (10, Decimal('2.0')), (20, Decimal('2.9')), (float('inf'), Decimal('5.8'))]),
    (float('inf'), [(5, Decimal('1.3')), (10, Decimal('2.2')), (20, Decimal('3.2')), (float('inf'), Decimal('8.5'))])
]

WEIGHT_MAPPING = {
    'Very Light': Decimal('0.5'),
    'Light': Decimal('1.0'),
    'Medium': Decimal('2.0'),
    'Heavy': Decimal('3.0'),
    'Very Heavy': Decimal('4.0'),
    'XXHeavy': Decimal('5.0')
}

SIZE_MAPPING = {
    'Very Small': Decimal('0.5'),
    'Small': Decimal('1.0'),
    'Medium': Decimal('2.0'),
    'Large': Decimal('3.0'),
    'Very Large': Decimal('4.0'),
    'XXL': Decimal('5.0')
}


def is_valid_pair(weight, size):
    weight_values = [Decimal('0.5'), Decimal('1.0'), Decimal('2.0'), Decimal('3.0'), Decimal('4.0'), Decimal('5.0')]
    size_values = [Decimal('0.5'), Decimal('1.0'), Decimal('2.0'), Decimal('3.0'), Decimal('4.0'), Decimal('5.0')]
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

        distance = Decimal(str(calculate_distance(warehouse_coord, state_coord)))

        cart_items = cart.cartitem_cart.all()
        if not cart_items:
            raise ValueError("Cart is empty")

        total_fee = BASE_FEE
        rate_per_unit_base = Decimal('0')
        light_item_scaling = Decimal('0.4') if distance < 150 else Decimal('0.5')

        for threshold, multiplier in DISTANCE_TIERS:
            if distance < threshold:
                rate_per_unit_base = FEE_PER_KM * multiplier
                break
        else:
            rate_per_unit_base = FEE_PER_KM * DISTANCE_TIERS[-1][1]

        has_heavy_item = any(
            (WEIGHT_FEE * WEIGHT_MAPPING.get(item.product.weight, Decimal('0')) +
             SIZE_FEE * SIZE_MAPPING.get(item.product.dimensional_size, Decimal('0'))) >= Decimal('4000')
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
            item_fee = item_multiplier * Decimal(str(quantity))

            quantity_multiplier = Decimal('1.0')
            tiers = QUANTITY_TIERS_LIGHT if item_multiplier < Decimal('4000') else None
            if item_multiplier >= Decimal('4000'):
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

            rate_per_unit = rate_per_unit_base * min(item_multiplier / Decimal('1000'), Decimal('5'))
            if item_multiplier >= Decimal('4000') and quantity >= 20:
                rate_per_unit *= (Decimal('1') + Decimal('0.21') * (Decimal(str(quantity)) / Decimal('20')))
            elif item_multiplier < Decimal('4000') and quantity >= 5:
                rate_per_unit *= (Decimal('1') + Decimal('0.18') * (Decimal(str(quantity)) / Decimal('20')))

            if has_heavy_item and item_multiplier < Decimal('4000') and quantity < 10:
                item_fee *= light_item_scaling
                distance_fee = item_fee * rate_per_unit * distance * light_item_scaling
            else:
                distance_fee = item_fee * rate_per_unit * distance

            total_fee += item_fee + distance_fee

        return total_fee.quantize(Decimal('100'), rounding=ROUND_HALF_UP)

    except ValueError as e:
        raise
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")
