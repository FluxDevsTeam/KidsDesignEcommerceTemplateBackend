import decimal
from decimal import Decimal, ROUND_HALF_UP
from ..ecommerce_admin.models import DeliverySettings
from .utils import AVAILABLE_STATES, state_coords, calculate_distance, WAREHOUSE_CITY

# old
# FEE_PER_KM = Decimal('100')
# BASE_FEE = Decimal('1500')
# WEIGHT_FEE = Decimal('1000')
# SIZE_FEE = Decimal('1000')

# new
# FEE_PER_KM = Decimal('150')
# BASE_FEE = Decimal('4000')
# SIZE_FEE = Decimal('1500')
# WEIGHT_FEE = Decimal('1500')

DISTANCE_TIERS = [
    (1, Decimal('0'), 'Group 1'),
    (150, Decimal('0.08'), 'Group 2'),
    (400, Decimal('0.07'), 'Group 3'),
    (800, Decimal('0.06'), 'Group 4'),
    (float('inf'), Decimal('0.05'), 'Group 5')
]

QUANTITY_TIERS = [
    (5, Decimal('1.5')),
    (10, Decimal('2.0')),
    (20, Decimal('2.5')),
    (100, Decimal('4.0')),
    (float('inf'), Decimal('5.0'))
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

MAIN_VALUES = {
    'VL-VS': {
        1: {'Group 1': 3000, 'Group 2': 3500, 'Group 3': 6900, 'Group 4': 7360, 'Group 5': 7820},
        5: {'Group 1': 4000, 'Group 2': 5980, 'Group 3': 7360, 'Group 4': 8280, 'Group 5': 9200},
        10: {'Group 1': 5000, 'Group 2': 6440, 'Group 3': 8280, 'Group 4': 9660, 'Group 5': 11040},
        20: {'Group 1': 6440, 'Group 2': 8280, 'Group 3': 9660, 'Group 4': 11040, 'Group 5': 12880},
        100: {'Group 1': 11040, 'Group 2': 12880, 'Group 3': 13800, 'Group 4': 16560, 'Group 5': 21160}
    },
    'L-S': {
        1: {'Group 1': 5000, 'Group 2': 6440, 'Group 3': 7360, 'Group 4': 8280, 'Group 5': 9200},
        5: {'Group 1': 9200, 'Group 2': 12880, 'Group 3': 14720, 'Group 4': 16560, 'Group 5': 18400},
        10: {'Group 1': 11960, 'Group 2': 16560, 'Group 3': 18400, 'Group 4': 20240, 'Group 5': 23000},
        20: {'Group 1': 14720, 'Group 2': 20240, 'Group 3': 23000, 'Group 4': 24840, 'Group 5': 27600},
        100: {'Group 1': 23000, 'Group 2': 32200, 'Group 3': 36800, 'Group 4': 46000, 'Group 5': 55200}
    },
    'M-M': {
        1: {'Group 1': 23000, 'Group 2': 27600, 'Group 3': 32200, 'Group 4': 36800, 'Group 5': 41400},
        5: {'Group 1': 42320, 'Group 2': 46000, 'Group 3': 55200, 'Group 4': 82800, 'Group 5': 92000},
        10: {'Group 1': 55200, 'Group 2': 73600, 'Group 3': 92000, 'Group 4': 110400, 'Group 5': 138000},
        20: {'Group 1': 73600, 'Group 2': 92000, 'Group 3': 110400, 'Group 4': 128800, 'Group 5': 184000},
        100: {'Group 1': 322000, 'Group 2': 414000, 'Group 3': 460000, 'Group 4': 552000, 'Group 5': 644000}
    },
    'H-L': {
        1: {'Group 1': 36800, 'Group 2': 41400, 'Group 3': 46000, 'Group 4': 50600, 'Group 5': 55200},
        5: {'Group 1': 64400, 'Group 2': 73600, 'Group 3': 82800, 'Group 4': 92000, 'Group 5': 119600},
        10: {'Group 1': 82800, 'Group 2': 92000, 'Group 3': 110400, 'Group 4': 138000, 'Group 5': 165600},
        20: {'Group 1': 110400, 'Group 2': 128800, 'Group 3': 147200, 'Group 4': 184000, 'Group 5': 230000},
        100: {'Group 1': 460000, 'Group 2': 552000, 'Group 3': 644000, 'Group 4': 736000, 'Group 5': 828000}
    },
    'VH-VL': {
        1: {'Group 1': 50600, 'Group 2': 59800, 'Group 3': 69000, 'Group 4': 78200, 'Group 5': 92000},
        5: {'Group 1': 87400, 'Group 2': 101200, 'Group 3': 110400, 'Group 4': 138000, 'Group 5': 184000},
        10: {'Group 1': 119600, 'Group 2': 138000, 'Group 3': 156400, 'Group 4': 184000, 'Group 5': 276000},
        20: {'Group 1': 147200, 'Group 2': 184000, 'Group 3': 230000, 'Group 4': 276000, 'Group 5': 368000},
        100: {'Group 1': 598000, 'Group 2': 736000, 'Group 3': 828000, 'Group 4': 920000, 'Group 5': 1104000}
    },
    'XXH-XXL': {
        1: {'Group 1': 69000, 'Group 2': 78200, 'Group 3': 92000, 'Group 4': 119600, 'Group 5': 138000},
        5: {'Group 1': 110400, 'Group 2': 128800, 'Group 3': 147200, 'Group 4': 184000, 'Group 5': 230000},
        10: {'Group 1': 147200, 'Group 2': 184000, 'Group 3': 230000, 'Group 4': 276000, 'Group 5': 368000},
        20: {'Group 1': 184000, 'Group 2': 230000, 'Group 3': 276000, 'Group 4': 368000, 'Group 5': 460000},
        100: {'Group 1': 736000, 'Group 2': 920000, 'Group 3': 1104000, 'Group 4': 1288000, 'Group 5': 1472000}
    }
}


def is_valid_pair(weight, size):
    weight_values = [Decimal('0.5'), Decimal('1.0'), Decimal('2.0'), Decimal('3.0'), Decimal('4.0'), Decimal('5.0')]
    size_values = [Decimal('0.5'), Decimal('1.0'), Decimal('2.0'), Decimal('3.0'), Decimal('4.0'), Decimal('5.0')]
    weight_idx = weight_values.index(WEIGHT_MAPPING[weight])
    size_idx = size_values.index(SIZE_MAPPING[size])
    return abs(weight_idx - size_idx) <= 1


def get_quantity_multiplier(quantity, item_multiplier):
    base_multiplier = Decimal('1.0')
    for qty_threshold, multiplier in QUANTITY_TIERS:
        if quantity <= qty_threshold:
            base_multiplier = multiplier
            break
    else:
        base_multiplier = QUANTITY_TIERS[-1][1]
    min_multiplier = Decimal('1500')
    max_multiplier = Decimal('15000')
    scale = (item_multiplier - min_multiplier) / (max_multiplier - min_multiplier)
    scale = max(Decimal('0'), min(Decimal('1'), scale))
    return Decimal('1.0') + scale * (base_multiplier - Decimal('1.0'))


def calculate_fee_for_pair(pair, quantity, distance, rate_per_unit_base):
    pair_multipliers = {
        'VL-VS': 1500, 'L-S': 3000, 'M-M': 6000, 'H-L': 9000, 'VH-VL': 12000, 'XXH-XXL': 15000
    }
    item_multiplier = Decimal(str(pair_multipliers[pair]))
    quantity_multiplier = get_quantity_multiplier(quantity, item_multiplier)
    item_fee = item_multiplier * Decimal(str(quantity)) * quantity_multiplier
    rate_per_unit = rate_per_unit_base * min(item_multiplier / Decimal('1000'), Decimal('5'))
    distance_fee = min(item_fee * rate_per_unit * distance, Decimal('50000'))
    return item_fee + distance_fee


def get_main_value(weight, size, quantity, group):
    pair_multipliers = {
        (0.5, 0.5): 'VL-VS', (1.0, 1.0): 'L-S', (2.0, 2.0): 'M-M',
        (3.0, 3.0): 'H-L', (4.0, 4.0): 'VH-VL', (5.0, 5.0): 'XXH-XXL'
    }
    standard_pair = pair_multipliers.get((WEIGHT_MAPPING[weight], SIZE_MAPPING[size]))
    if standard_pair:
        return Decimal(str(MAIN_VALUES[standard_pair][quantity][group]))

    item_multiplier = WEIGHT_FEE * WEIGHT_MAPPING[weight] + SIZE_FEE * SIZE_MAPPING[size]
    standard_multipliers = sorted([1500, 3000, 6000, 9000, 12000, 15000])
    lower_mult = max([m for m in standard_multipliers if m <= item_multiplier], default=1500)
    upper_mult = min([m for m in standard_multipliers if m >= item_multiplier], default=15000)
    lower_pair = {1500: 'VL-VS', 3000: 'L-S', 6000: 'M-M', 9000: 'H-L', 12000: 'VH-VL', 15000: 'XXH-XXL'}[lower_mult]
    upper_pair = {1500: 'VL-VS', 3000: 'L-S', 6000: 'M-M', 9000: 'H-L', 12000: 'VH-VL', 15000: 'XXH-XXL'}[upper_mult]

    lower_fee = Decimal(str(MAIN_VALUES[lower_pair][quantity][group]))
    upper_fee = Decimal(str(MAIN_VALUES[upper_pair][quantity][group]))
    if lower_mult == upper_mult:
        return lower_fee
    fraction = (item_multiplier - lower_mult) / (upper_mult - lower_mult)
    return lower_fee + fraction * (upper_fee - lower_fee)


def adjust_fee_to_deviation(fee, main_value):
    min_fee = main_value * Decimal('0.92')
    max_fee = main_value * Decimal('1.08')
    return max(min_fee, min(fee, max_fee)).quantize(Decimal('100'), rounding=ROUND_HALF_UP)


def calculate_delivery_fee(cart):
    try:
        delivery_settings = DeliverySettings.objects.first()
        if not delivery_settings:
            raise ValueError("No DeliverySettings record found in the database")

        def validate_decimal(value, field_name):
            if value is None:
                raise ValueError(f"{field_name} is None in DeliverySettings")
            if not isinstance(value, (int, float, str, Decimal)):
                raise ValueError(f"{field_name} has invalid type: {type(value)}")
            try:
                decimal_value = Decimal(str(value))
                if decimal_value.is_nan() or not decimal_value.is_finite():
                    raise ValueError(f"{field_name} is not a valid number: {value}")
                return decimal_value
            except (ValueError, decimal.InvalidOperation) as e:
                raise ValueError(
                    f"Invalid {field_name} in DeliverySettings: unable to convert to Decimal (value: {value}, error: {str(e)})")

        fee_per_km = validate_decimal(FEE_PER_KM, "fee_per_km")
        base_fee = validate_decimal(BASE_FEE, "base_fee")
        weight_fee = validate_decimal(WEIGHT_FEE, "weigh_fee")
        size_fee = validate_decimal(SIZE_FEE, "size_fee")

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

        total_fee = base_fee
        rate_per_unit_base = Decimal('0')
        selected_group = 'Group 1'

        for threshold, multiplier, group in DISTANCE_TIERS:
            if distance < threshold:
                rate_per_unit_base = fee_per_km * multiplier
                selected_group = group
                break
        else:
            rate_per_unit_base = fee_per_km * DISTANCE_TIERS[-1][1]
            selected_group = DISTANCE_TIERS[-1][2]

        standard_multipliers = {
            1500: 'VL-VS', 3000: 'L-S', 6000: 'M-M', 9000: 'H-L', 12000: 'VH-VL', 15000: 'XXH-XXL'
        }
        item_fees = []
        has_heavy_item = any(
            (weight_fee * WEIGHT_MAPPING.get(item.product.weight, Decimal('0')) +
             size_fee * SIZE_MAPPING.get(item.product.dimensional_size, Decimal('0'))) >= Decimal('9000')
            for item in cart_items
        )
        heavy_item_count = sum(
            1 for item in cart_items
            if (weight_fee * WEIGHT_MAPPING.get(item.product.weight, Decimal('0')) +
                size_fee * SIZE_MAPPING.get(item.product.dimensional_size, Decimal('0'))) >= Decimal('3500')
        )

        main_value_sum = Decimal('0')
        for item in cart_items:
            product = item.product
            quantity = item.quantity
            if quantity <= 0 or not isinstance(quantity, int):
                raise ValueError(f"Invalid quantity for product {product.name}: {quantity}")
            if quantity > 1000:
                raise ValueError(f"Quantity too large for product {product.name}: {quantity}")

            weight_choice = product.weight
            size_choice = product.dimensional_size
            if not is_valid_pair(weight_choice, size_choice):
                raise ValueError(f"Invalid weight-size pair: {weight_choice}, {size_choice}")

            weight_multiplier = WEIGHT_MAPPING.get(weight_choice)
            size_multiplier = SIZE_MAPPING.get(size_choice)
            if weight_multiplier is None or size_multiplier is None:
                raise ValueError(f"Invalid weight or size choice: {weight_choice}, {size_choice}")

            item_multiplier = weight_fee * weight_multiplier + size_fee * size_multiplier
            quantity_multiplier = get_quantity_multiplier(quantity, item_multiplier)
            item_fee = item_multiplier * Decimal(str(quantity)) * quantity_multiplier

            if has_heavy_item and item_multiplier < Decimal('3500'):
                item_fee *= Decimal('0.5')

            rate_per_unit = rate_per_unit_base * min(item_multiplier / Decimal('1000'), Decimal('5'))
            distance_fee = min(item_fee * rate_per_unit * distance, Decimal('50000'))

            lower_mult = max([m for m in standard_multipliers if m <= item_multiplier],
                             default=min(standard_multipliers))
            upper_mult = min([m for m in standard_multipliers if m >= item_multiplier],
                             default=max(standard_multipliers))
            lower_fee = calculate_fee_for_pair(standard_multipliers[lower_mult], quantity, distance, rate_per_unit_base)
            upper_fee = calculate_fee_for_pair(standard_multipliers[upper_mult], quantity, distance, rate_per_unit_base)
            total_item_fee = max(lower_fee, min(item_fee + distance_fee, upper_fee))

            item_fees.append(total_item_fee)
            main_value_sum += get_main_value(weight_choice, size_choice, quantity, selected_group)

        if heavy_item_count >= 2:
            reduction_factor = Decimal('0.98') if heavy_item_count == 2 else Decimal('0.95')
            item_fees = [fee * reduction_factor for fee in item_fees]

        total_fee += sum(item_fees)

        if total_fee < 0:
            raise ValueError("Calculated delivery fee is negative")

        total_fee = adjust_fee_to_deviation(total_fee, main_value_sum)

        return total_fee.quantize(Decimal('100'), rounding=ROUND_HALF_UP)

    except ValueError as e:
        raise
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")