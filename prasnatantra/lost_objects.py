# Lost property / Missing Person recovery calculations based on Shatpanchasika Adhyaya VI
from .shatpanchasika import get_navamsa_sign, aspects_sign, get_sign
from .astronomy import get_sign_name

# Directions Map
PLANET_DIRECTIONS = {
    "Sun": "East",
    "Venus": "South-East",
    "Mars": "South",
    "Rahu": "South-West",
    "Saturn": "West",
    "Moon": "North-West",
    "Mercury": "North",
    "Jupiter": "North-East"
}

# Sign Directions
SIGN_DIRECTIONS = {
    0: "East", 4: "East", 8: "East",      # Aries, Leo, Sagittarius
    1: "South", 5: "South", 9: "South",   # Taurus, Virgo, Capricorn
    2: "West", 6: "West", 10: "West",     # Gemini, Libra, Aquarius
    3: "North", 7: "North", 11: "North"   # Cancer, Scorpio, Pisces
}

# Sign Colors
SIGN_COLORS = {
    0: "Red",
    1: "White",
    2: "Green",
    3: "Pink",
    4: "Grey",
    5: "Variegated",
    6: "Black",
    7: "Brown",
    8: "Gold / Yellow-Brown",
    9: "Mixed / Dark Grey",
    10: "Tawny / Dark",
    11: "Soiled / Fish-like Variegated"
}

# Sign Sizes
SIGN_SIZES = {
    0: "Short", 1: "Short", 10: "Short", 11: "Short",
    2: "Medium", 3: "Medium", 8: "Medium", 9: "Medium",
    4: "Long", 5: "Long", 6: "Long", 7: "Long"
}

# Sign Classifications (Dhatu/Moola/Jeeva)
# Movable = Dhatu (Mineral), Fixed = Moola (Root/Vegetation), Dual = Jeeva (Animal/Human)
SIGN_CLASSES = {
    0: "Dhatu (Mineral / Metal / Jewellery)",
    3: "Dhatu (Mineral / Metal / Jewellery)",
    6: "Dhatu (Mineral / Metal / Jewellery)",
    9: "Dhatu (Mineral / Metal / Jewellery)",
    
    1: "Moola (Vegetable / Plants / Paper / Wood)",
    4: "Moola (Vegetable / Plants / Paper / Wood)",
    7: "Moola (Vegetable / Plants / Paper / Wood)",
    10: "Moola (Vegetable / Plants / Paper / Wood)",
    
    2: "Jeeva (Animal / Human / Living / Leather)",
    5: "Jeeva (Animal / Human / Living / Leather)",
    8: "Jeeva (Animal / Human / Living / Leather)",
    11: "Jeeva (Animal / Human / Living / Leather)"
}

# Drekkana locations in house
DREKKANA_LOCATIONS = {
    0: "Near the entrance/gate of the house (1st Drekkana)",
    1: "In the middle of the house / living area / sanctuary (2nd Drekkana)",
    2: "In the backyard / west side of the house (3rd Drekkana)"
}

# Thief age mapping
PLANET_AGES = {
    "Moon": "Boy/Child (approx. 4-5 years old)",
    "Mercury": "Celibate Youth (approx. 12 years old)",
    "Venus": "Adolescent/Young Adult (approx. 32 years old)",
    "Mars": "Active Young Adult (approx. 20-25 years old)",
    "Jupiter": "Middle-aged Person (approx. 50 years old)",
    "Sun": "Elderly Person (approx. 70 years old)",
    "Saturn": "Very Old Person (approx. 80+ years old)"
}

# Thief caste/class mapping
PLANET_CLASSES = {
    "Jupiter": "Scholarly / Noble / Priest / Priestess",
    "Venus": "Scholarly / Respectable Person / Artist",
    "Sun": "Ruler / Warrior / Soldier / Administrator",
    "Mars": "Ruler / Officer / Guard / Aggressive Person",
    "Moon": "Trader / Merchant / Vaishya",
    "Mercury": "Artisan / Worker / Clerk / Servant",
    "Saturn": "Stranger / Outcast / Foreigner"
}

def get_planet_strength(planet_name, planet_data, sun_lon):
    """Simple heuristic for planet strength based on own-sign, exaltation, retrograde, combustion."""
    lon = planet_data["longitude"]
    sign = get_sign(lon)
    
    # Exaltation signs
    exaltations = {
        "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6
    }
    # Own signs
    own_signs = {
        "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5], "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]
    }
    
    strength = 10  # base strength
    
    if sign == exaltations.get(planet_name):
        strength += 5
    elif sign in own_signs.get(planet_name, []):
        strength += 3
        
    if planet_data.get("speed", 1.0) < 0:
        strength -= 2  # retrograde
        
    # check combustion
    from .tajaka import check_combustion
    if check_combustion(planet_name, lon, sun_lon):
        strength -= 4
        
    return strength

def evaluate_lost_property(chart):
    """
    Evaluates lost/stolen property queries using Shatpanchasika Adhyaya VI rules.
    """
    lagna_sign = chart.lagna_sign
    lagna_lon = chart.lagna_sidereal
    lagna_deg = lagna_lon % 30.0
    
    # 1. Navamsa and Vargottama calculations
    nav_sign, nav_idx = get_navamsa_sign(lagna_lon)
    is_fixed_lagna = lagna_sign in [1, 4, 7, 10]
    is_fixed_nav = nav_sign in [1, 4, 7, 10]
    is_vargottama = lagna_sign == nav_sign
    
    # Sloka 1: Stolen by insider or outsider
    if is_fixed_lagna or is_fixed_nav or is_vargottama:
        thief_source = "Insider (Family member, employee, or someone inside the querent's circle)"
        thief_loc_desc = "The item is still within the owner's premises / property."
        is_insider = True
    else:
        thief_source = "Outsider (Stranger or someone external)"
        thief_loc_desc = "The item has been removed from the premises."
        is_insider = False
        
    # Sloka 2: Location inside house based on Drekkana
    drekkana_idx = int(lagna_deg / 10.0)
    drekkana_loc = DREKKANA_LOCATIONS.get(drekkana_idx, "Unknown")
    
    # Sloka 3: Recovery status
    recovery_conditions = []
    recovered = False
    
    # A. Waxing/Full Moon in Lagna
    moon_lon = chart.planets["Moon"]["longitude"]
    sun_lon = chart.planets["Sun"]["longitude"]
    moon_sun_diff = (moon_lon - sun_lon) % 360.0
    is_waxing_moon = moon_sun_diff < 180.0
    moon_in_lagna = get_sign(moon_lon) == lagna_sign
    
    if moon_in_lagna and is_waxing_moon:
        recovered = True
        recovery_conditions.append("Waxing/Full Moon is present in the Lagna sign (Shatpanchasika VI.3)")
        
    # B. Sirshodaya sign rising, occupied and aspected by benefics
    sirshodaya_signs = [2, 4, 5, 6, 7, 10]  # Gemini, Leo, Virgo, Libra, Scorpio, Aquarius
    is_sirshodaya = lagna_sign in sirshodaya_signs
    
    benefics_in_lagna = []
    benefics_aspecting_lagna = []
    
    for b in ["Mercury", "Venus", "Jupiter"]:
        blon = chart.planets[b]["longitude"]
        bsign = get_sign(blon)
        if bsign == lagna_sign:
            benefics_in_lagna.append(b)
        elif aspects_sign(blon, lagna_sign):
            benefics_aspecting_lagna.append(b)
            
    if is_sirshodaya and benefics_in_lagna and benefics_aspecting_lagna:
        recovered = True
        recovery_conditions.append(
            f"Sirshodaya sign ({get_sign_name(lagna_sign)}) rising, "
            f"occupied by {', '.join(benefics_in_lagna)} and aspected by {', '.join(benefics_aspecting_lagna)} (Shatpanchasika VI.3)"
        )
        
    # C. Strong benefic in 11th house
    house_11_sign = (lagna_sign + 10) % 12
    benefics_in_11 = []
    for b in ["Mercury", "Venus", "Jupiter"]:
        blon = chart.planets[b]["longitude"]
        bsign = get_sign(blon)
        if bsign == house_11_sign:
            # check if strong
            strength = get_planet_strength(b, chart.planets[b], sun_lon)
            if strength >= 10:
                benefics_in_11.append(f"{b} (Strength: {strength})")
                
    if benefics_in_11:
        recovered = True
        recovery_conditions.append(
            f"Strong benefic planet in the 11th house: {', '.join(benefics_in_11)} (Shatpanchasika VI.3)"
        )
        
    # Verdict text
    if recovered:
        recovery_verdict = "YES — Highly Probable & Fast Recovery"
        recovery_reason = " | ".join(recovery_conditions)
    else:
        recovery_verdict = "NO — Recovery Unlikely / Extremely Delayed"
        recovery_reason = "None of the classical Shatpanchasika recovery conditions are met (full Moon in Lagna, benefic-associated Sirshodaya Lagna, or strong benefic in 11th)."

    # Sloka 4: Direction
    # Find planets in Kendras (1st, 4th, 7th, 10th houses/signs)
    kendra_signs = [lagna_sign, (lagna_sign + 3) % 12, (lagna_sign + 6) % 12, (lagna_sign + 9) % 12]
    kendra_planets = []
    
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:  # ignore Ketu, use Rahu
            continue
        p_sign = get_sign(p_data["longitude"])
        if p_sign in kendra_signs:
            strength = get_planet_strength(p_name, p_data, sun_lon)
            kendra_planets.append((p_name, strength))
            
    # Pick direction
    direction_source = ""
    if kendra_planets:
        # Sort by strength descending
        kendra_planets.sort(key=lambda x: x[1], reverse=True)
        strongest_p = kendra_planets[0][0]
        direction = PLANET_DIRECTIONS.get(strongest_p, "Unknown")
        direction_source = f"Strongest planet in Kendra: {strongest_p} ({direction})"
    else:
        # Use Lagna Sign direction
        direction = SIGN_DIRECTIONS.get(lagna_sign, "Unknown")
        direction_source = f"Lagna Sign ({get_sign_name(lagna_sign)}) direction"

    # Sloka 4: Distance
    # Navamsa Index of Lagna (0 to 8)
    # 5th Navamsa ends at 16°40'. So indices 0, 1, 2, 3, 4 represent <= 5th Navamsa.
    if nav_idx <= 4:
        distance_desc = "Within immediate premises (Item has not left the house or office)"
        distance_val = 0
    else:
        navs_past_5th = nav_idx - 4
        yojanas = navs_past_5th
        miles = yojanas * 8.5
        distance_desc = f"{yojanas} Yojana(s) away (approx. {miles:.1f} miles / {miles * 1.609:.1f} km)"
        distance_val = yojanas

    # Sloka 5: Thief Profile & Substance Description
    # Age & Caste from Lagna Lord
    lagna_lord = chart.lagnapathi
    thief_age = PLANET_AGES.get(lagna_lord, "Unknown")
    thief_class = PLANET_CLASSES.get(lagna_lord, "Unknown")
    
    # Substance from rising Navamsa sign classification
    substance_type = SIGN_CLASSES.get(nav_sign, "Unknown")
    color = SIGN_COLORS.get(lagna_sign, "Unknown")
    size = SIGN_SIZES.get(nav_sign, "Unknown")

    return {
        "thief_source": thief_source,
        "thief_loc_desc": thief_loc_desc,
        "is_insider": is_insider,
        "drekkana_location": drekkana_loc,
        "recovery_verdict": recovery_verdict,
        "recovery_reason": recovery_reason,
        "direction": direction,
        "direction_source": direction_source,
        "distance_desc": distance_desc,
        "distance_yojanas": distance_val,
        "thief_age": thief_age,
        "thief_class": thief_class,
        "substance_type": substance_type,
        "color": color,
        "size": size,
        "lagna_sign_name": get_sign_name(lagna_sign),
        "nav_sign_name": get_sign_name(nav_sign)
    }
