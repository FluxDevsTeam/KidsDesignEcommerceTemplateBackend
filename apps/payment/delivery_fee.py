from .utils import AVAILABLE_STATES, state_coords, calculate_distance, WAREHOUSE_CITY
import math
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Hardcoded fee values to avoid undefined variable issues
FEE_PER_KM = 100  # NGN/km
BASE_FEE = 3000   # NGN
WEIGHT_FEE = 2000 # NGN/kg
SIZE_FEE = 2000   # NGN/kg

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
    print(f"Calculating volumetric weight for weight_choice: {weight_choice}, size_choice: {size_choice}")
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
    volumetric_weight = max(actual_weight, dimensional_weight)
    print(f"Actual weight: {actual_weight}, Dimensional weight: {dimensional_weight}, Volumetric weight: {volumetric_weight}")
    return volumetric_weight

def get_distance_rate(distance):
    print(f"Calculating distance rate for distance: {distance} km")
    for threshold, multiplier in DISTANCE_TIERS:
        if distance < threshold:
            rate = FEE_PER_KM * multiplier
            print(f"Distance tier: <{threshold} km, multiplier: {multiplier}, rate: {rate} NGN/kg")
            return rate
    rate = FEE_PER_KM * DISTANCE_TIERS[-1][1]
    print(f"Distance tier: >1000 km, multiplier: {DISTANCE_TIERS[-1][1]}, rate: {rate} NGN/kg")
    return rate

def get_quantity_factor(total_quantity):
    print(f"Calculating quantity factor for total_quantity: {total_quantity}")
    if total_quantity <= 0:
        raise ValueError("Total quantity must be positive")
    quantity_factor = 1 - 0.3 * (1 - 1 / (1 + 0.1 * total_quantity))
    print(f"Quantity factor: {quantity_factor}")
    return quantity_factor

def calculate_delivery_fee(cart):
    try:
        print("Starting delivery fee calculation")
        # Validate cart state
        selected_state = getattr(cart, 'state', None)
        print(f"Selected state: {selected_state}")
        if not selected_state or selected_state.lower() not in [state.lower() for state in AVAILABLE_STATES]:
            raise ValueError(f"Invalid or missing delivery state: {selected_state}")

        # Get coordinates
        state_coord_lower = {key.lower(): value for key, value in state_coords.items()}
        warehouse_coord = state_coord_lower.get(WAREHOUSE_CITY.lower())
        state_coord = state_coord_lower.get(selected_state.lower())
        print(f"Warehouse coords: {warehouse_coord}, State coords: {state_coord}")

        if not warehouse_coord:
            raise ValueError(f"Warehouse coordinates not found for {WAREHOUSE_CITY}")
        if not state_coord:
            raise ValueError(f"Coordinates not found for state: {selected_state}")

        # Calculate distance
        distance = calculate_distance(warehouse_coord, state_coord)
        print(f"Calculated distance: {distance} km")

        # Get cart items
        try:
            cart_items = cart.cartitem_cart.all()  # Fixed: Use correct related_name
            print(f"Number of cart items: {len(cart_items)}")
        except AttributeError as e:
            logger.error(f"Error accessing cart items: {str(e)}")
            raise ValueError("Cart items could not be accessed")

        if not cart_items:
            raise ValueError("Cart is empty")

        total_volumetric_weight = 0
        total_quantity = 0
        for item in cart_items:
            try:
                weight_choice = item.product.weight
                size_choice = item.product.dimensional_size
                quantity = item.quantity
                product_name = getattr(item.product, 'name', 'unknown')
                print(f"Processing item: {product_name}, Weight: {weight_choice}, Size: {size_choice}, Quantity: {quantity}")
            except AttributeError as e:
                logger.error(f"Invalid product data for cart item: {str(e)}")
                raise ValueError(f"Invalid product data: {str(e)}")

            if quantity <= 0:
                raise ValueError(f"Invalid quantity for product {product_name}: {quantity}")

            volumetric_weight = get_volumetric_weight(weight_choice, size_choice)
            total_volumetric_weight += volumetric_weight * quantity
            total_quantity += quantity
            print(f"Item volumetric weight: {volumetric_weight}, Total for item: {volumetric_weight * quantity}")

        print(f"Total volumetric weight: {total_volumetric_weight} kg, Total quantity: {total_quantity}")
        quantity_factor = get_quantity_factor(total_quantity)
        rate_per_kg = get_distance_rate(distance)
        distance_fee = total_volumetric_weight * rate_per_kg * quantity_factor
        weight_fee = total_volumetric_weight * WEIGHT_FEE * quantity_factor
        size_fee = total_volumetric_weight * SIZE_FEE * (1 + 0.1 * math.log(1 + total_volumetric_weight)) * quantity_factor
        total_fee = BASE_FEE + distance_fee + weight_fee + size_fee

        print(f"Distance fee: {distance_fee}, Weight fee: {weight_fee}, Size fee: {size_fee}, Base fee: {BASE_FEE}")
        print(f"Total delivery fee: {round(total_fee)} NGN")

        return round(total_fee)

    except ValueError as e:
        logger.error(f"Delivery fee calculation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delivery fee calculation: {str(e)}")
        raise ValueError(f"Unexpected error: {str(e)}")