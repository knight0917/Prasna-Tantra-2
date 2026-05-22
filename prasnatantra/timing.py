"""
Kalapinda Timing Method
Authoritative classical timing calculations from Prasna Tantra Chapter IV (Stanzas 15-19).
"""

import math

PLANETS = {
    1: "Sun",
    2: "Moon",
    3: "Mars",
    4: "Mercury",
    5: "Jupiter",
    6: "Venus",
    7: "Saturn"
}

GUNAKAS = {
    "Sun": 5,
    "Moon": 21,
    "Mars": 14,
    "Mercury": 9,
    "Jupiter": 8,
    "Venus": 11,
    "Saturn": 11
}

BENEFICS = {"Moon", "Mercury", "Jupiter", "Venus"}

TIME_UNITS = {
    "Sun": "days",
    "Mars": "days",
    "Moon": "fortnights",
    "Venus": "fortnights",
    "Jupiter": "months",
    "Mercury": "half-years",
    "Saturn": "years"
}

def calculate_equinoctial_shadow(latitude: float) -> float:
    """
    Calculates the equinoctial midday shadow length (Palabha) for a given latitude.
    Classically computed using a standard 12-digit gnomon (sanku):
    Shadow = 12 * tan(|latitude|)
    
    Args:
        latitude (float): Latitude of the query location in degrees.
        
    Returns:
        float: Midday shadow length.
    """
    if abs(latitude) >= 90.0:
        raise ValueError("Latitude must be strictly between -90 and 90 degrees.")
    return 12.0 * math.tan(math.radians(abs(latitude)))

def calculate_kalapinda_timing(lagna_longitude: float, latitude: float) -> dict:
    """
    Applies the Kalapinda timing method (Prasna Tantra Ch IV Stanzas 15-19).
    
    Args:
        lagna_longitude (float): Longitude of the Ascendant in degrees (0 to 360).
        latitude (float): Latitude of the query location in degrees.
        
    Returns:
        dict: Detailed result containing the intermediate steps and final timing.
    """
    # Step 1: Calculate Equinoctial Shadow
    shadow = calculate_equinoctial_shadow(latitude)
    
    # Step 2: Calculate Kalapinda in minutes of arc
    # Normalize longitude to [0, 360)
    lagna_longitude = lagna_longitude % 360.0
    kalapinda = int(round(lagna_longitude * 60.0))
    
    # Step 3: First Process
    # Multiply Kalapinda by shadow length and divide by 7
    product1 = kalapinda * shadow
    prod1_int = int(round(product1))
    rem1 = prod1_int % 7
    if rem1 == 0:
        rem1 = 7
        
    significant_planet = PLANETS[rem1]
    sig_gunaka = GUNAKAS[significant_planet]
    
    # Step 4: Second Process
    # Multiply Kalapinda by the concerned planetary factor
    product2 = kalapinda * sig_gunaka
    
    # Sum of Gunakas from Sun to the significant planet
    planet_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    idx_sig = planet_order.index(significant_planet)
    divisor = sum(GUNAKAS[p] for p in planet_order[:idx_sig + 1])
    
    # Divide product2 by divisor to get remainder y
    y = product2 % divisor
    
    # Step 5: Third Process
    # Deduct Gunakas sequentially
    current_y = y
    rising_planet = None
    leftover_points = None
    
    for p in planet_order:
        p_gunaka = GUNAKAS[p]
        if current_y >= p_gunaka:
            current_y -= p_gunaka
        else:
            rising_planet = p
            leftover_points = current_y
            break
            
    if rising_planet is None:
        rising_planet = "Saturn"
        leftover_points = current_y
        
    is_benefic = rising_planet in BENEFICS
    time_unit = TIME_UNITS[rising_planet]
    
    # Proportional fructification time
    unit_days = {
        "days": 1.0,
        "fortnights": 15.0,
        "months": 30.0,
        "half-years": 180.0,
        "years": 365.0
    }
    
    rising_gunaka = GUNAKAS[rising_planet]
    proportion = leftover_points / rising_gunaka if rising_gunaka > 0 else 0.0
    time_in_days = proportion * unit_days[time_unit]
    
    return {
        "latitude": latitude,
        "equinoctial_shadow": shadow,
        "lagna_longitude": lagna_longitude,
        "kalapinda": kalapinda,
        "first_process": {
            "product": product1,
            "remainder": rem1,
            "planet": significant_planet,
            "gunaka": sig_gunaka
        },
        "second_process": {
            "product": product2,
            "divisor": divisor,
            "remainder_y": y
        },
        "third_process": {
            "rising_planet": rising_planet,
            "is_benefic": is_benefic,
            "leftover_points": leftover_points,
            "rising_planet_gunaka": rising_gunaka
        },
        "timing": {
            "unit": time_unit,
            "value": leftover_points,
            "proportion": proportion,
            "time_in_days": time_in_days
        }
    }
