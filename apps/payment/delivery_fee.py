# delivery_fee.py

from utils import AVAILABLE_STATES, state_coords, calculate_distance, ZONE_DELIVERY_GAPS

# Delivery fee constants (these can be adjusted as per your needs)
FEE_PER_KM = 10  # Cost per kilometer (could be different based on weight or size)
BASE_FEE = 50  # A base fee for all deliveries
BASE_ITEM_FEE = 20  # Base cost per item, for a single small item
WEIGHT_FEE = 30  # Fee per kilogram for weight-based calculation
SIZE_FEE = 40  # Fee per cubic meter for size-based calculation

# Quantity thresholds for different pricing tiers
QUANTITY_THRESHOLDS = [
    (3, 18),  # For quantities up to 3 items, fee is 18 per item
    (5, 15),  # For quantities up to 5 items, fee is 15 per item
    (10, 12),  # For quantities up to 10 items, fee is 12 per item
    (15, 10),  # For quantities up to 15 items, fee is 10 per item
    (20, 8),  # For quantities up to 20 items, fee is 8 per item
    (50, 5),  # For quantities up to 50 items, fee is 5 per item (lower cost per item)
]

# Set the warehouse city globally (adjust as needed)
WAREHOUSE_CITY = "Lagos"

# Weight categories and ranges (in kg)
WEIGHT_CATEGORIES = {
    "Very Small": (0, 1),  # 0 - 1 kg
    "Small": (1.1, 3),  # 1.1 - 3 kg
    "Medium": (3.1, 5),  # 3.1 - 5 kg
    "Large": (5.1, 10),  # 5.1 - 10 kg
    "XXL": (10.1, float('inf'))  # 10.1 kg and above
}

# Size categories and ranges (in cubic meters)
SIZE_CATEGORIES = {
    "Very Small": (0, 0.01),  # 0 - 0.01 cubic meters
    "Small": (0.01, 0.05),  # 0.01 - 0.05 cubic meters
    "Medium": (0.05, 0.1),  # 0.05 - 0.1 cubic meters
    "Large": (0.1, 0.2),  # 0.1 - 0.2 cubic meters
    "XXL": (0.2, float('inf'))  # 0.2 cubic meters and above
}


def get_weight_fee(weight_category, quantity):
    """
    Returns the weight fee based on weight category and quantity.

    :param weight_category: The weight category ('Very Small', 'Small', 'Medium', 'Large', 'XXL').
    :param quantity: The quantity of items.
    :return: Weight fee for the order.
    """
    if weight_category not in WEIGHT_CATEGORIES:
        return 0  # If invalid category, no weight fee
    weight_range = WEIGHT_CATEGORIES[weight_category]
    weight_fee = WEIGHT_FEE * (weight_range[1] - weight_range[0]) * quantity
    return weight_fee


def get_size_fee(size_category, quantity):
    """
    Returns the size fee based on size category and quantity.

    :param size_category: The size category ('Very Small', 'Small', 'Medium', 'Large', 'XXL').
    :param quantity: The quantity of items.
    :return: Size fee for the order.
    """
    if size_category not in SIZE_CATEGORIES:
        return 0  # If invalid category, no size fee
    size_range = SIZE_CATEGORIES[size_category]
    size_fee = SIZE_FEE * (size_range[1] - size_range[0]) * quantity
    return size_fee


def get_item_fee(quantity):
    """
    Get the item fee based on the quantity of items ordered.

    :param quantity: Quantity of items being ordered.
    :return: The delivery fee per item based on quantity.
    """
    for threshold, fee in QUANTITY_THRESHOLDS:
        if quantity <= threshold:
            return fee
    return BASE_ITEM_FEE  # Default fee for quantities beyond the largest threshold


def calculate_delivery_fee(selected_state, quantity, weight_category, size_category):
    """
    Calculates the delivery fee based on the selected state, warehouse city, quantity, weight category, and size category.

    :param selected_state: State where the delivery is going.
    :param quantity: Quantity of items being ordered.
    :param weight_category: Category of the item weight ('Very Small', 'Small', 'Medium', 'Large', 'XXL').
    :param size_category: Category of the item size ('Very Small', 'Small', 'Medium', 'Large', 'XXL').
    :return: The delivery fee in Naira.
    """
    # Ensure that the selected state is in the available states list
    if selected_state not in AVAILABLE_STATES:
        return f"Currently not delivering to {selected_state}"

    # Validate weight and size categories
    if weight_category not in WEIGHT_CATEGORIES:
        return f"Invalid weight category: {weight_category}"
    if size_category not in SIZE_CATEGORIES:
        return f"Invalid size category: {size_category}"

    # Get coordinates of the warehouse and the selected state
    warehouse_coord = state_coords.get(WAREHOUSE_CITY)  # Use the global warehouse city
    state_coord = state_coords.get(selected_state)

    if not warehouse_coord or not state_coord:
        return "Invalid warehouse city or selected state"

    # Calculate the distance between the warehouse and the selected state
    distance = calculate_distance(warehouse_coord, state_coord)

    # Basic delivery fee based on distance
    delivery_fee = BASE_FEE + (distance * FEE_PER_KM)

    # Weight-based delivery fee
    weight_fee = get_weight_fee(weight_category, quantity)

    # Size-based delivery fee
    size_fee = get_size_fee(size_category, quantity)

    # Calculate the item fee based on quantity
    item_fee = get_item_fee(quantity) * quantity  # Apply the calculated item fee

    # Calculate the total delivery fee
    total_delivery_fee = delivery_fee + weight_fee + size_fee + item_fee

    return f"Delivery fee for {selected_state} ({quantity} items): {total_delivery_fee:.2f} Naira"
