import decimal
from decimal import Decimal, ROUND_HALF_UP
from django.utils.functional import SimpleLazyObject
from ..ecommerce_admin.models import DeliverySettings, OrganizationSettings
from .utils import state_coords, calculate_distance

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


def get_delivery_settings():
    delivery_settings = DeliverySettings.objects.first()
    if not delivery_settings:
        raise ValueError("No DeliverySettings record found in the database")

    try:
        return {
            'fee_per_km': validate_decimal(delivery_settings.fee_per_km, "fee_per_km"),
            'base_fee': validate_decimal(delivery_settings.base_fee, "base_fee"),
            'weight_fee': validate_decimal(delivery_settings.weight_fee, "weight_fee"),
            'size_fee': validate_decimal(delivery_settings.size_fee, "size_fee")
        }
    except AttributeError as e:
        raise ValueError(f"Invalid DeliverySettings configuration: {str(e)}")


def validate_decimal(value, field_name):
    if isinstance(value, SimpleLazyObject):
        value = value._wrapped if hasattr(value, '_wrapped') else value
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


def is_valid_pair(weight, size):
    weight_values = [Decimal('0.5'), Decimal('1.0'), Decimal('2.0'), Decimal('3.0'), Decimal('4.0'), Decimal('5.0')]
    size_values = [Decimal('0.5'), Decimal('1.0'), Decimal('2.0'), Decimal('3.0'), Decimal('4.0'), Decimal('5.0')]
    try:
        weight_idx = weight_values.index(WEIGHT_MAPPING[weight])
        size_idx = size_values.index(SIZE_MAPPING[size])
        return abs(weight_idx - size_idx) <= 1
    except (KeyError, ValueError):
        raise ValueError(f"Invalid weight or size: weight={weight}, size={size}")


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
    try:
        scale = (item_multiplier - min_multiplier) / (max_multiplier - min_multiplier)
        scale = max(Decimal('0'), min(Decimal('1'), scale))
        return Decimal('1.0') + scale * (base_multiplier - Decimal('1.0'))
    except decimal.InvalidOperation:
        raise ValueError(
            f"Invalid calculation in get_quantity_multiplier: quantity={quantity}, item_multiplier={item_multiplier}")


def calculate_fee_for_pair(pair, quantity, distance, rate_per_unit_base):
    pair_multipliers = {
        'VL-VS': 1500, 'L-S': 3000, 'M-M': 6000, 'H-L': 9000, 'VH-VL': 12000, 'XXH-XXL': 15000
    }
    try:
        item_multiplier = Decimal(str(pair_multipliers[pair]))
        quantity_multiplier = get_quantity_multiplier(quantity, item_multiplier)
        item_fee = item_multiplier * Decimal(str(quantity)) * quantity_multiplier
        rate_per_unit = rate_per_unit_base * min(item_multiplier / Decimal('1000'), Decimal('5'))
        distance_fee = min(item_fee * rate_per_unit * distance, Decimal('50000'))
        return item_fee + distance_fee
    except (KeyError, decimal.InvalidOperation):
        raise ValueError(
            f"Invalid calculation in calculate_fee_for_pair: pair={pair}, quantity={quantity}, distance={distance}")


def get_main_value(weight, size, quantity, group, weight_fee, size_fee):
    pair_multipliers = {
        (0.5, 0.5): 'VL-VS', (1.0, 1.0): 'L-S', (2.0, 2.0): 'M-M',
        (3.0, 3.0): 'H-L', (4.0, 4.0): 'VH-VL', (5.0, 5.0): 'XXH-XXL'
    }
    try:
        if weight not in WEIGHT_MAPPING:
            raise ValueError(f"Invalid weight: {weight}")
        if size not in SIZE_MAPPING:
            raise ValueError(f"Invalid size: {size}")
        if group not in {'Group 1', 'Group 2', 'Group 3', 'Group 4', 'Group 5'}:
            raise ValueError(f"Invalid group: {group}")
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise ValueError(f"Invalid quantity: {quantity}")

        standard_pair = pair_multipliers.get((WEIGHT_MAPPING[weight], SIZE_MAPPING[size]))
        if standard_pair:
            quantity_tiers = sorted(MAIN_VALUES[standard_pair].keys())
            if quantity in quantity_tiers:
                return Decimal(str(MAIN_VALUES[standard_pair][quantity][group]))

            lower_qty = max([q for q in quantity_tiers if q <= quantity], default=quantity_tiers[0])
            upper_qty = min([q for q in quantity_tiers if q >= quantity], default=quantity_tiers[-1])

            if lower_qty == upper_qty:
                return Decimal(str(MAIN_VALUES[standard_pair][lower_qty][group]))

            lower_fee = Decimal(str(MAIN_VALUES[standard_pair][lower_qty][group]))
            upper_fee = Decimal(str(MAIN_VALUES[standard_pair][upper_qty][group]))
            fraction = Decimal(str(quantity - lower_qty)) / Decimal(str(upper_qty - lower_qty))
            return lower_fee + fraction * (upper_fee - lower_fee)

        item_multiplier = weight_fee * WEIGHT_MAPPING[weight] + size_fee * SIZE_MAPPING[size]
        standard_multipliers = sorted([1500, 3000, 6000, 9000, 12000, 15000])
        lower_mult = max([m for m in standard_multipliers if m <= item_multiplier], default=1500)
        upper_mult = min([m for m in standard_multipliers if m >= item_multiplier], default=15000)
        lower_pair = {1500: 'VL-VS', 3000: 'L-S', 6000: 'M-M', 9000: 'H-L', 12000: 'VH-VL', 15000: 'XXH-XXL'}[
            lower_mult]
        upper_pair = {1500: 'VL-VS', 3000: 'L-S', 6000: 'M-M', 9000: 'H-L', 12000: 'VH-VL', 15000: 'XXH-XXL'}[
            upper_mult]

        quantity_tiers = sorted(MAIN_VALUES[lower_pair].keys())
        lower_qty = max([q for q in quantity_tiers if q <= quantity], default=quantity_tiers[0])
        upper_qty = min([q for q in quantity_tiers if q >= quantity], default=quantity_tiers[-1])

        if lower_qty == upper_qty:
            lower_fee = Decimal(str(MAIN_VALUES[lower_pair][lower_qty][group]))
            upper_fee = Decimal(str(MAIN_VALUES[upper_pair][lower_qty][group]))
        else:
            lower_fee_lower = Decimal(str(MAIN_VALUES[lower_pair][lower_qty][group]))
            lower_fee_upper = Decimal(str(MAIN_VALUES[lower_pair][upper_qty][group]))
            upper_fee_lower = Decimal(str(MAIN_VALUES[upper_pair][lower_qty][group]))
            upper_fee_upper = Decimal(str(MAIN_VALUES[upper_pair][upper_qty][group]))
            qty_fraction = Decimal(str(quantity - lower_qty)) / Decimal(str(upper_qty - lower_qty))
            lower_fee = lower_fee_lower + qty_fraction * (lower_fee_upper - lower_fee_lower)
            upper_fee = upper_fee_lower + qty_fraction * (upper_fee_upper - upper_fee_lower)

        if lower_mult == upper_mult:
            return lower_fee

        mult_fraction = (item_multiplier - Decimal(str(lower_mult))) / (
                    Decimal(str(upper_mult)) - Decimal(str(lower_mult)))
        return lower_fee + mult_fraction * (upper_fee - lower_fee)

    except (KeyError, ValueError, decimal.InvalidOperation):
        raise ValueError(
            f"Invalid calculation in get_main_value: weight={weight}, size={size}, quantity={quantity}, group={group}")


def adjust_fee_to_deviation(fee, main_value):
    try:
        min_fee = main_value * Decimal('0.92')
        max_fee = main_value * Decimal('1.08')
        return max(min_fee, min(fee, max_fee)).quantize(Decimal('100'), rounding=ROUND_HALF_UP)
    except decimal.InvalidOperation:
        raise ValueError(f"Invalid calculation in adjust_fee_to_deviation: fee={fee}, main_value={main_value}")


def calculate_delivery_fee(cart):
    try:
        settings = get_delivery_settings()
        fee_per_km = settings['fee_per_km']
        base_fee = settings['base_fee']
        weight_fee = settings['weight_fee']
        size_fee = settings['size_fee']

        organization_settings = OrganizationSettings.objects.first()
        if not organization_settings:
            raise ValueError("No OrganizationSettings record found in the database")
        available_states = organization_settings.available_states
        warehouse_state = organization_settings.warehouse_state

        selected_state = cart.state
        if not selected_state or selected_state.lower() not in [state.lower() for state in available_states]:
            raise ValueError(f"Invalid or missing delivery state: {selected_state}")

        state_coord_lower = {key.lower(): value for key, value in state_coords.items()}
        warehouse_coord = state_coord_lower.get(warehouse_state.lower())
        state_coord = state_coord_lower.get(selected_state.lower())

        if not warehouse_coord:
            raise ValueError(f"Warehouse coordinates not found for {warehouse_state}")
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

        heavy_items = []
        light_items = []
        item_details = []

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

            if weight_multiplier >= Decimal('3.0') or size_multiplier >= Decimal('3.0'):
                heavy_items.append((quantity, item_multiplier))
            else:
                light_items.append((quantity, item_multiplier))

            item_details.append({
                'quantity': quantity,
                'multiplier': item_multiplier,
                'weight': weight_choice,
                'size': size_choice
            })

        total_heavy_qty = sum(q for q, m in heavy_items)
        total_light_qty = sum(q for q, m in light_items)

        light_discounts = {}
        if heavy_items and light_items:
            for qty, multiplier in light_items:
                ratio = qty / total_heavy_qty if total_heavy_qty > 0 else float('inf')
                if ratio <= 1:
                    discount = Decimal('0.5')
                elif ratio < 2:
                    discount = Decimal('0.3')
                else:
                    discount = Decimal('0.1')
                light_discounts[(qty, multiplier)] = discount

        item_fees = []
        main_value_sum = Decimal('0')
        has_heavy_item = len(heavy_items) > 0
        heavy_item_count = len(heavy_items)

        for item in item_details:
            quantity = item['quantity']
            original_multiplier = item['multiplier']

            if (quantity, original_multiplier) in light_discounts:
                multiplier = original_multiplier * (Decimal('1') - light_discounts[(quantity, original_multiplier)])
            else:
                multiplier = original_multiplier

            quantity_multiplier = get_quantity_multiplier(quantity, multiplier)
            item_fee = multiplier * Decimal(str(quantity)) * quantity_multiplier

            if has_heavy_item and original_multiplier < Decimal('3500'):
                item_fee *= Decimal('0.5')

            rate_per_unit = rate_per_unit_base * min(multiplier / Decimal('1000'), Decimal('5'))
            distance_fee = min(item_fee * rate_per_unit * distance, Decimal('50000'))

            standard_multipliers = {
                1500: 'VL-VS', 3000: 'L-S', 6000: 'M-M',
                9000: 'H-L', 12000: 'VH-VL', 15000: 'XXH-XXL'
            }
            lower_mult = max([m for m in standard_multipliers if m <= multiplier], default=1500)
            upper_mult = min([m for m in standard_multipliers if m >= multiplier], default=15000)

            lower_fee = calculate_fee_for_pair(
                standard_multipliers[lower_mult], quantity, distance, rate_per_unit_base
            )
            upper_fee = calculate_fee_for_pair(
                standard_multipliers[upper_mult], quantity, distance, rate_per_unit_base
            )

            total_item_fee = max(lower_fee, min(item_fee + distance_fee, upper_fee))
            item_fees.append(total_item_fee)

            main_value_sum += get_main_value(
                item['weight'], item['size'], quantity, selected_group, weight_fee, size_fee
            )

        if heavy_item_count >= 2:
            reduction_factor = Decimal('0.98') if heavy_item_count == 2 else Decimal('0.95')
            item_fees = [fee * reduction_factor for fee in item_fees]

        total_fee += sum(item_fees)

        if total_fee < 0:
            raise ValueError("Calculated delivery fee is negative")

        total_fee = adjust_fee_to_deviation(total_fee, main_value_sum)

        return total_fee.quantize(Decimal('100'), rounding=ROUND_HALF_UP)

    except ValueError:
        raise
    except Exception:
        raise ValueError("Unexpected error in calculate_delivery_fee")