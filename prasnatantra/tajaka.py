import math

# Deepthamsas (orbs of operation) in degrees
ORBS = {
    "Sun": 15.0,
    "Moon": 12.0,
    "Mars": 8.0,
    "Mercury": 7.0,
    "Jupiter": 9.0,
    "Venus": 7.0,
    "Saturn": 9.0
}

# Combustion limits in degrees from Sun
COMBUSTION_LIMITS = {
    "Moon": 12.0,
    "Mars": 12.0,
    "Mercury": 8.0,
    "Jupiter": 9.0,
    "Venus": 7.0,
    "Saturn": 9.0
}

def get_sign(longitude):
    return int(longitude / 30.0) % 12

def get_sign_distance(lon1, lon2):
    sign1 = get_sign(lon1)
    sign2 = get_sign(lon2)
    diff = (sign2 - sign1) % 12
    return diff

def evaluate_aspect_type(lon1, lon2):
    """
    Returns the Tajaka aspect type and its friendly/hostile classification,
    or None if no aspect exists.
    """
    diff_signs = get_sign_distance(lon1, lon2)
    
    # Tajaka aspects are based on sign-to-sign positions:
    # 0 signs diff: Conjunction (0°)
    # 2 or 10 signs diff: Sextile (60°)
    # 3 or 9 signs diff: Square (90°)
    # 4 or 8 signs diff: Trine (120°)
    # 6 signs diff: Opposition (180°)
    if diff_signs == 0:
        return {"type": "Conjunction", "angle": 0.0, "is_friendly": None, "strength": 1.0}
    elif diff_signs in [2, 10]:
        # 3rd/11th house: Sextile (secretly friendly)
        strength = 0.40 if diff_signs == 2 else 0.10
        return {"type": "Sextile", "angle": 60.0, "is_friendly": True, "strength": strength}
    elif diff_signs in [3, 9]:
        # 4th/10th house: Square (hostile)
        return {"type": "Square", "angle": 90.0, "is_friendly": False, "strength": 0.45}
    elif diff_signs in [4, 8]:
        # 5th/9th house: Trine (openly friendly)
        return {"type": "Trine", "angle": 120.0, "is_friendly": True, "strength": 0.75}
    elif diff_signs == 6:
        # 1st/7th house: Opposition (highly hostile)
        return {"type": "Opposition", "angle": 180.0, "is_friendly": False, "strength": 1.00}
    
    return None

def check_orb_validity(p1_name, lon1, p2_name, lon2, aspect_angle):
    """
    Checks if the distance between two planets is within their average combined orb limit.
    """
    orb1 = ORBS.get(p1_name, 9.0)
    orb2 = ORBS.get(p2_name, 9.0)
    max_orb = (orb1 + orb2) / 2.0
    
    # Calculate actual angular separation
    sep = abs(lon1 - lon2) % 360
    if sep > 180:
        sep = 360 - sep
        
    actual_diff = abs(sep - aspect_angle)
    return actual_diff <= max_orb, actual_diff

def determine_aspect_application(lon1, speed1, lon2, speed2, aspect_angle):
    """
    Returns True if the aspect is applying (Ithasala/Muthasila),
    False if it is separating (Easarapha/Musaripha).
    Uses a numerical forward step to determine if the angular separation
    between the planets is closing or opening relative to the exact aspect.
    """
    # Helper to calculate distance to exact aspect angle
    def get_aspect_distance(l1, l2):
        sep = abs(l1 - l2) % 360
        if sep > 180:
            sep = 360 - sep
        return abs(sep - aspect_angle)
        
    dist_current = get_aspect_distance(lon1, lon2)
    
    # Step forward 0.01 days (approx 15 mins)
    step = 0.01
    lon1_future = (lon1 + speed1 * step) % 360
    lon2_future = (lon2 + speed2 * step) % 360
    dist_future = get_aspect_distance(lon1_future, lon2_future)
    
    return dist_future < dist_current

def get_planet_relationship(p1_name, p1_data, p2_name, p2_data):
    """
    Evaluates the aspect, orb, and application status between two planets.
    """
    lon1, speed1 = p1_data["longitude"], p1_data["speed"]
    lon2, speed2 = p2_data["longitude"], p2_data["speed"]
    
    aspect = evaluate_aspect_type(lon1, lon2)
    if not aspect:
        return None
        
    in_orb, actual_diff = check_orb_validity(p1_name, lon1, p2_name, lon2, aspect["angle"])
    if not in_orb:
        return None
        
    is_applying = determine_aspect_application(lon1, speed1, lon2, speed2, aspect["angle"])
    
    return {
        "aspect_type": aspect["type"],
        "angle": aspect["angle"],
        "is_friendly": aspect["is_friendly"],
        "strength": aspect["strength"],
        "orb_diff": actual_diff,
        "is_applying": is_applying,
        "is_complete": actual_diff <= 1.0  # Poorna Ithasala if within 1 degree
    }

EXALTATION_SIGNS = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6
}
DEBILITATION_SIGNS = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11, "Jupiter": 9, "Venus": 5, "Saturn": 0
}
OWN_SIGNS = {
    "Sun": [4],
    "Moon": [3],
    "Mars": [0, 7],
    "Mercury": [2, 5],
    "Jupiter": [8, 11],
    "Venus": [1, 6],
    "Saturn": [9, 10]
}
FRIENDLY_SIGNS = {
    "Sun": [3, 0, 7, 8, 11],
    "Moon": [4, 2, 5],
    "Mars": [4, 3, 8, 11],
    "Mercury": [4, 1, 6],
    "Jupiter": [4, 3, 0, 7],
    "Venus": [2, 5, 9, 10],
    "Saturn": [2, 5, 1, 6]
}
INIMICAL_SIGNS = {
    "Sun": [1, 6, 9, 10],
    "Moon": [],
    "Mars": [2, 5],
    "Mercury": [3],
    "Jupiter": [2, 5, 1, 6],
    "Venus": [4, 3],
    "Saturn": [4, 3, 0, 7]
}
def check_combustion(planet_name, planet_lon, sun_lon):
    if planet_name == "Sun":
        return False
    limit = COMBUSTION_LIMITS.get(planet_name, 9.0)
    diff = abs(planet_lon - sun_lon) % 360
    if diff > 180:
        diff = 360 - diff
    return diff <= limit

EXALTATION_DEGREES = {
    "Sun": 10.0,
    "Moon": 33.0,
    "Mars": 298.0,
    "Mercury": 165.0,
    "Jupiter": 95.0,
    "Venus": 357.0,
    "Saturn": 200.0
}

def get_navamsa_sign_index(longitude):
    sign = get_sign(longitude)
    deg_in_sign = longitude % 30
    if sign in [0, 3, 6, 9]:
        start_sign = sign
    elif sign in [1, 4, 7, 10]:
        start_sign = (sign + 8) % 12
    else:
        start_sign = (sign + 4) % 12
    navamsa_idx = int(deg_in_sign / (30.0 / 9.0))
    return (start_sign + navamsa_idx) % 12

def calculate_varga_benefic_count(planet_name, longitude):
    if planet_name in ["Rahu", "Ketu"]:
        return 0
        
    varga_count = 0
    sign = get_sign(longitude)
    deg_in_sign = longitude % 30
    
    # 1. Rasi
    if sign in OWN_SIGNS.get(planet_name, []) or sign == EXALTATION_SIGNS.get(planet_name):
        varga_count += 1
        
    # 2. Hora
    is_odd = (sign % 2) != 0
    if is_odd:
        hora_sign = 4 if deg_in_sign < 15.0 else 3
    else:
        hora_sign = 3 if deg_in_sign < 15.0 else 4
    if hora_sign in OWN_SIGNS.get(planet_name, []) or hora_sign == EXALTATION_SIGNS.get(planet_name):
        varga_count += 1
        
    # 3. Drekkana
    if deg_in_sign < 10.0:
        drekkana_sign = sign
    elif deg_in_sign < 20.0:
        drekkana_sign = (sign + 4) % 12
    else:
        drekkana_sign = (sign + 8) % 12
    if drekkana_sign in OWN_SIGNS.get(planet_name, []) or drekkana_sign == EXALTATION_SIGNS.get(planet_name):
        varga_count += 1
        
    # 4. Navamsa
    nav_sign = get_navamsa_sign_index(longitude)
    if nav_sign in OWN_SIGNS.get(planet_name, []) or nav_sign == EXALTATION_SIGNS.get(planet_name):
        varga_count += 1
        
    # 5. Dwadasamsa
    dwad_idx = int(deg_in_sign / 2.5)
    dwad_sign = (sign + dwad_idx) % 12
    if dwad_sign in OWN_SIGNS.get(planet_name, []) or dwad_sign == EXALTATION_SIGNS.get(planet_name):
        varga_count += 1
        
    return varga_count

def check_nipeeditha(planet_name, planet_lon, planets_dict):
    if planet_name in ["Rahu", "Ketu"] or not planets_dict:
        return False
        
    for malefic in ["Mars", "Saturn", "Rahu", "Ketu"]:
        if malefic == planet_name:
            continue
        if malefic not in planets_dict:
            continue
            
        m_lon = planets_dict[malefic]["longitude"]
        orb_p = COMBUSTION_LIMITS.get(planet_name, 7.0)
        orb_m = COMBUSTION_LIMITS.get(malefic, 9.0)
        max_orb = (orb_p + orb_m) / 2.0
        
        diff = abs(planet_lon - m_lon) % 360
        if diff > 180:
            diff = 360 - diff
        if diff <= max_orb:
            return True
            
    return False

def get_planetary_avastha(planet_name, planet_lon, planet_data, sun_lon, planets_dict=None):
    """
    Determines the Avastha of a planet based on Sri Neelakanta's Prasna Tantra:
    1. Mushita (Combust): Conjoined with Sun within combustion orb.
    2. Nipeeditha (Vanquished): Conjoined with a malefic within average orb.
    3. Athiveerya (High benefic divisions): In >= 3/5 own/exalted Shadvargas.
    4. Deeptha (Exalted): In exaltation sign.
    5. Deena (Debilitated): In debilitation sign.
    6. Swastha (Own house): In its own sign.
    7. Muditha (Friendly sign): In a friendly sign.
    8. Suptha (Inimical sign or Retrograde): In an inimical sign or retrograde.
    9. Suveerya (Ascending): Ascending towards exaltation.
    10. Pariheena (Descending): Descending towards debility.
    """
    if planet_name in ["Rahu", "Ketu"]:
        if planet_data.get("is_retrograde", False):
            return "Suptha"
        return "Swastha"
        
    # 1. Mushita (Combust) first
    if check_combustion(planet_name, planet_lon, sun_lon):
        return "Mushita"
        
    # 2. Nipeeditha (Vanquished)
    if check_nipeeditha(planet_name, planet_lon, planets_dict):
        return "Nipeeditha"
        
    sign = get_sign(planet_lon)
    
    # Calculate base avastha using Rashi parameters
    base_avastha = None
    exalt_sign = EXALTATION_SIGNS.get(planet_name)
    deb_sign = DEBILITATION_SIGNS.get(planet_name)
    
    if exalt_sign is not None and sign == exalt_sign:
        base_avastha = "Deeptha"
    elif deb_sign is not None and sign == deb_sign:
        base_avastha = "Deena"
    elif sign in OWN_SIGNS.get(planet_name, []):
        base_avastha = "Swastha"
    elif calculate_varga_benefic_count(planet_name, planet_lon) >= 3:
        base_avastha = "Athiveerya"
    elif planet_data.get("is_retrograde", False):
        base_avastha = "Suptha"
    elif sign in FRIENDLY_SIGNS.get(planet_name, []):
        base_avastha = "Muditha"
    elif sign in INIMICAL_SIGNS.get(planet_name, []):
        base_avastha = "Suptha"
    elif planet_name in EXALTATION_DEGREES:
        exalt = EXALTATION_DEGREES[planet_name]
        debility = (exalt + 180.0) % 360.0
        dist_from_deb = (planet_lon - debility) % 360.0
        if dist_from_deb < 180.0:
            base_avastha = "Suveerya"
        else:
            base_avastha = "Pariheena"
    else:
        base_avastha = "Suveerya"

    # Navamsa-based modifications
    nav_sign = get_navamsa_sign_index(planet_lon)
    
    is_vargottama = (sign == nav_sign)
    is_nav_exalted = (nav_sign == EXALTATION_SIGNS.get(planet_name))
    is_nav_own = (nav_sign in OWN_SIGNS.get(planet_name, []))
    is_nav_debilitated = (nav_sign == DEBILITATION_SIGNS.get(planet_name))
    
    # Check for benefic aspects/conjunctions in the Navamsa chart
    aspected_by_benefic_in_nav = False
    if planets_dict:
        for benefic in ["Jupiter", "Venus"]:
            if benefic == planet_name:
                continue
            if benefic in planets_dict:
                b_lon = planets_dict[benefic]["longitude"]
                b_nav_sign = get_navamsa_sign_index(b_lon)
                diff = (nav_sign - b_nav_sign) % 12
                # Tajaka aspect check in Navamsa: Conjunction (0), Sextile (2, 10), Square (3, 9), Trine (4, 8), Opposition (6)
                if diff in [0, 2, 3, 4, 6, 8, 9, 10]:
                    aspected_by_benefic_in_nav = True
                    break

    # Apply Navamsa dignity rules
    # 1. Debilitation in Navamsa: Demote to Deena (except if already Mushita/Nipeeditha)
    if is_nav_debilitated:
        base_avastha = "Deena"
        
    # 2. Vargottama: Promote to Swastha (or keep Deeptha)
    elif is_vargottama:
        if base_avastha == "Deeptha":
            base_avastha = "Deeptha"
        else:
            base_avastha = "Swastha"
        
    # 3. Exalted in Navamsa: Promote to Swastha/Deeptha
    elif is_nav_exalted:
        if base_avastha in ["Deeptha", "Athiveerya", "Swastha"]:
            base_avastha = "Deeptha"
        elif base_avastha == "Deena":
            base_avastha = "Muditha"  # cancelled debility
        else:
            base_avastha = "Swastha"
            
    # 4. Own Navamsa: Promote to Swastha/Pariheena
    elif is_nav_own:
        if base_avastha in ["Deeptha", "Athiveerya", "Swastha"]:
            pass
        elif base_avastha == "Deena":
            base_avastha = "Pariheena"  # partially cancelled debility
        else:
            base_avastha = "Swastha"

    # 5. Benefic Aspect in Navamsa: Protects and upgrades weak/sleepy states
    if aspected_by_benefic_in_nav:
        if base_avastha == "Deena":
            base_avastha = "Pariheena"
        elif base_avastha == "Pariheena":
            base_avastha = "Neutral"
        elif base_avastha == "Suptha":
            base_avastha = "Muditha"

    return base_avastha

def detect_nakta_yoga(p1_name, p1_data, p2_name, p2_data, planets_dict):
    """
    Nakta Yoga: Lagnapathi (p1) and Karyesa (p2) have no aspect,
    but a faster planet (e.g. Moon) translates light by having
    applying Ithasala with both of them.
    """
    direct_rel = get_planet_relationship(p1_name, p1_data, p2_name, p2_data)
    if direct_rel:
        return None  # Direct aspect exists, Nakta not needed
        
    # Find a faster intermediate planet that aspects both in an applying manner
    # Planet speeds: Moon > Mercury > Venus > Sun > Mars > Jupiter > Saturn
    # Standard order of speeds
    speed_order = ["Moon", "Mercury", "Venus", "Sun", "Mars", "Jupiter", "Saturn"]
    
    p1_idx = speed_order.index(p1_name) if p1_name in speed_order else 99
    p2_idx = speed_order.index(p2_name) if p2_name in speed_order else 99
    faster_idx_limit = min(p1_idx, p2_idx)
    
    possible_nakta = []
    for name, data in planets_dict.items():
        if name in [p1_name, p2_name]:
            continue
            
        # The translating planet must be faster than both target planets
        if name in speed_order:
            translator_idx = speed_order.index(name)
            if translator_idx >= faster_idx_limit:
                continue # Translator is not faster than both targets
                
        rel1 = get_planet_relationship(name, data, p1_name, p1_data)
        rel2 = get_planet_relationship(name, data, p2_name, p2_data)
        
        if rel1 and rel2 and rel1["is_applying"] and rel2["is_applying"]:
            possible_nakta.append({
                "translator": name,
                "relationship_with_p1": rel1,
                "relationship_with_p2": rel2
            })
            
    return possible_nakta if possible_nakta else None

def detect_yamaya_yoga(p1_name, p1_data, p2_name, p2_data, planets_dict):
    """
    Yamaya Yoga: Lagnapathi (p1) and Karyesa (p2) have no aspect,
    but a slower intermediate planet translates light by having
    applying Ithasala with both of them.
    """
    direct_rel = get_planet_relationship(p1_name, p1_data, p2_name, p2_data)
    if direct_rel:
        return None
        
    speed_order = ["Moon", "Mercury", "Venus", "Sun", "Mars", "Jupiter", "Saturn"]
    p1_idx = speed_order.index(p1_name) if p1_name in speed_order else -1
    p2_idx = speed_order.index(p2_name) if p2_name in speed_order else -1
    slower_idx_limit = max(p1_idx, p2_idx)
    
    possible_yamaya = []
    for name, data in planets_dict.items():
        if name in [p1_name, p2_name]:
            continue
            
        # The translating planet must be slower than both target planets
        if name in speed_order:
            translator_idx = speed_order.index(name)
            if translator_idx <= slower_idx_limit:
                continue
                
        rel1 = get_planet_relationship(name, data, p1_name, p1_data)
        rel2 = get_planet_relationship(name, data, p2_name, p2_data)
        
        if rel1 and rel2 and rel1["is_applying"] and rel2["is_applying"]:
            possible_yamaya.append({
                "translator": name,
                "relationship_with_p1": rel1,
                "relationship_with_p2": rel2
            })
            
    return possible_yamaya if possible_yamaya else None

def detect_kamboola_yoga(p1_name, p1_data, p2_name, p2_data, Moon_data):
    """
    Kamboola Yoga: Lagnapathi (p1) and Karyesa (p2) are in applying Ithasala,
    and the Moon is also in applying Ithasala with either or both of them.
    """
    direct_rel = get_planet_relationship(p1_name, p1_data, p2_name, p2_data)
    if not direct_rel or not direct_rel["is_applying"]:
        return None
        
    rel_moon_p1 = get_planet_relationship("Moon", Moon_data, p1_name, p1_data)
    rel_moon_p2 = get_planet_relationship("Moon", Moon_data, p2_name, p2_data)
    
    if (rel_moon_p1 and rel_moon_p1["is_applying"]) or (rel_moon_p2 and rel_moon_p2["is_applying"]):
        return {
            "relationship_p1_p2": direct_rel,
            "relationship_moon_p1": rel_moon_p1,
            "relationship_moon_p2": rel_moon_p2
        }
    return None

def detect_gairikamboola_yoga(p1_name, p1_data, p2_name, p2_data, Moon_data, planets_dict):
    """
    Gairikamboola Yoga: A compromised Kamboola Yoga.
    Lagnapathi (p1) and Karyesa (p2) are in applying Ithasala,
    and the Moon is in applying Ithasala with either or both of them (Kamboola conditions),
    but the Moon is afflicted:
    1. Moon is combust (within 12 degrees of the Sun).
    2. Moon is debilitated (in Scorpio, sign index 7).
    3. Moon is conjoined or aspected by Mars or Saturn.
    """
    kamboola = detect_kamboola_yoga(p1_name, p1_data, p2_name, p2_data, Moon_data)
    if not kamboola:
        return None
        
    # Check if Moon is afflicted
    # 1. Combustion check (Moon combustion limit 12 degrees)
    sun_lon = planets_dict["Sun"]["longitude"] if "Sun" in planets_dict else 0.0
    moon_lon = Moon_data["longitude"]
    moon_combust = check_combustion("Moon", moon_lon, sun_lon)
    
    # 2. Debilitated in Scorpio (sign index 7)
    moon_sign = get_sign(moon_lon)
    moon_debilitated = (moon_sign == 7)
    
    # 3. Conjoined or aspected by Mars or Saturn
    moon_afflicted_by_malefics = False
    for malefic in ["Mars", "Saturn"]:
        if malefic in planets_dict:
            rel = get_planet_relationship("Moon", Moon_data, malefic, planets_dict[malefic])
            if rel:
                moon_afflicted_by_malefics = True
                break
                
    if moon_combust or moon_debilitated or moon_afflicted_by_malefics:
        return {
            "relationship_p1_p2": kamboola["relationship_p1_p2"],
            "relationship_moon_p1": kamboola["relationship_moon_p1"],
            "relationship_moon_p2": kamboola["relationship_moon_p2"],
            "afflictions": {
                "combust": moon_combust,
                "debilitated": moon_debilitated,
                "malefic_aspect": moon_afflicted_by_malefics
            }
        }
    return None
