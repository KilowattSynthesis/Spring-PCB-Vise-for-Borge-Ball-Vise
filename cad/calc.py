import math

def calculate_inscribed_rectangle_dimension(radius: float, known_side: float) -> float:
    """
    Calculate the missing side of a rectangle inscribed in a circle.

    Args:
        radius (float): Radius of the circle.
        known_side (float): Known side length of the rectangle (either 'a' or 'b').

    Returns:
        float: The missing side length of the rectangle.
    """
    # Calculate the square of the diameter
    diameter_squared = (2 * radius) ** 2
    
    # Check if the known side length is valid
    if known_side ** 2 >= diameter_squared:
        raise ValueError("Known side length is too large to fit within the circle.")
    
    # Calculate the missing side
    missing = math.sqrt(diameter_squared - known_side ** 2)
    
    print(f"The missing side is: {missing:.2f}")
    
    return missing
