# traveler.py
# Implements traveler health, return timing, enemy marching, and siege calculations
# based on Shatpanchasika Chapters II, III, and V

from .shatpanchasika import get_sign, aspects_sign
from .astronomy import get_sign_name

# Nocturnal signs rising with backs (Prishtodaya) except Gemini
PRISHTODAYA_SIGNS = [0, 1, 3, 8, 9]  # Aries, Taurus, Cancer, Sagittarius, Capricorn

def check_malefic(planet_name, planet_data):
    """Check if planet is a malefic (Sun, Mars, Saturn, or Rahu/Ketu)."""
    # Waning Moon is also malefic, but for simple engine logic we use Sun, Mars, Saturn
    return planet_name in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]

def check_benefic(planet_name, planet_data):
    """Check if planet is a benefic (Mercury, Venus, Jupiter, or Moon if waxing)."""
    # In general horary, Jupiter, Venus, Mercury are benefics
    return planet_name in ["Jupiter", "Venus", "Mercury", "Moon"]

def evaluate_traveler_abroad(chart):
    """
    Evaluates travel, return of traveler, and war/siege questions
    using Shatpanchasika rules (Adhyayas II, III, V).
    """
    lagna_sign = chart.lagna_sign
    lagna_lon = chart.lagna_sidereal
    
    # 1. TRAVELER CONDITION (Adhyaya V Sloka 4)
    # Check malefic aspect on Prishtodaya Lagna
    is_prishtodaya = lagna_sign in PRISHTODAYA_SIGNS
    has_malefic_aspect_on_lagna = False
    
    # Check malefics
    malefics_in_3 = []
    malefics_in_6 = []
    malefics_in_kendras = []
    
    benefics_aspecting_3 = False
    benefics_aspecting_6 = False
    
    # Kendra houses: 1, 4, 7, 10
    kendra_signs = [lagna_sign, (lagna_sign + 3) % 12, (lagna_sign + 6) % 12, (lagna_sign + 9) % 12]
    house_3_sign = (lagna_sign + 2) % 12
    house_6_sign = (lagna_sign + 5) % 12
    
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        p_lon = p_data["longitude"]
        p_sign = get_sign(p_lon)
        
        # Check aspect on Lagna
        if check_malefic(p_name, p_data) and aspects_sign(p_lon, lagna_sign):
            has_malefic_aspect_on_lagna = True
            
        # Check occupancy of houses
        if p_sign == house_3_sign:
            if check_malefic(p_name, p_data):
                malefics_in_3.append(p_name)
        elif p_sign == house_6_sign:
            if check_malefic(p_name, p_data):
                malefics_in_6.append(p_name)
        elif p_sign in kendra_signs:
            if check_malefic(p_name, p_data):
                malefics_in_kendras.append(p_name)
                
        # Check benefic aspects
        if check_benefic(p_name, p_data):
            if aspects_sign(p_lon, house_3_sign):
                benefics_aspecting_3 = True
            if aspects_sign(p_lon, house_6_sign):
                benefics_aspecting_6 = True

    # Compile traveler condition verdict
    conditions = []
    if is_prishtodaya and has_malefic_aspect_on_lagna:
        conditions.append("Traveler is subjected to confinement, distress, or torture (Prishtodaya Lagna with malefic aspect - V.4)")
    if malefics_in_3 and not benefics_aspecting_3:
        conditions.append(f"Traveler has departed from their location to a further foreign country (Malefics {', '.join(malefics_in_3)} in 3rd without benefic aspect - V.4)")
    if malefics_in_6 and not benefics_aspecting_6:
        conditions.append(f"Traveler is lost, dead, or in grave danger (Malefics {', '.join(malefics_in_6)} in 6th without benefic aspect - V.4)")
    if malefics_in_kendras:
        conditions.append(f"Traveler is delayed by robbery, arrested, or captured by thieves (Malefics {', '.join(malefics_in_kendras)} in Kendras - V.4)")
        
    if not conditions:
        # Check if benefics are aspecting Lagna
        has_benefic_aspect_on_lagna = False
        for p_name, p_data in chart.planets.items():
            if check_benefic(p_name, p_data) and aspects_sign(p_data["longitude"], lagna_sign):
                has_benefic_aspect_on_lagna = True
        if has_benefic_aspect_on_lagna:
            traveler_status = "SAFE & PROSPEROUS — Traveler is well, safe, and enjoying success abroad."
        else:
            traveler_status = "STABLE — Traveler is safe, but progress is standard/slow."
    else:
        traveler_status = f"AFFLICTED — Warning: {', '.join(conditions)}"

    # 2. TIMING OF RETURN (Adhyaya V Sloka 5)
    # Search from house 1 (Lagna) to 12 for the first occupied house
    return_timing_desc = "Timing undetermined (No planet occupies any house)"
    return_days = None
    
    # Gather planetary occupancies by house (1-12)
    house_occupants = {h: [] for h in range(1, 13)}
    for p_name, p_data in chart.planets.items():
        if p_name in ["Rahu", "Ketu"]:
            continue
        p_sign = get_sign(p_data["longitude"])
        # House index (1 to 12)
        h_idx = ((p_sign - lagna_sign) % 12) + 1
        house_occupants[h_idx].append((p_name, p_data))
        
    # Find first occupied house
    first_occupied_house = None
    for h in range(1, 13):
        if house_occupants[h]:
            first_occupied_house = h
            break
            
    if first_occupied_house is not None:
        # Check the first planet found in this house
        p_name, p_data = house_occupants[first_occupied_house][0]
        is_retro = p_data.get("speed", 1.0) < 0
        if is_retro:
            return_days = first_occupied_house
            return_timing_desc = (
                f"Return is expected in {return_days} days. "
                f"Reason: Retrograde planet {p_name} is in House #{first_occupied_house} (Shatpanchasika V.5)."
            )
        else:
            return_days = first_occupied_house * 12
            return_timing_desc = (
                f"Return is expected in {return_days} days (approx. {return_days / 30.0:.1f} months). "
                f"Reason: Direct planet {p_name} is in House #{first_occupied_house} (Multiplier: 12x - Shatpanchasika V.5)."
            )

    # 3. ENEMY MARCH & ARRIVAL (Adhyaya II Slokas 6-8, 11)
    # Movable/Fixed/Dual Lagna and Moon Sign
    # Movable = 0, 3, 6, 9; Fixed = 1, 4, 7, 10; Dual = 2, 5, 8, 11
    is_movable_lagna = lagna_sign in [0, 3, 6, 9]
    is_fixed_lagna = lagna_sign in [1, 4, 7, 10]
    is_dual_lagna = lagna_sign in [2, 5, 8, 11]
    
    moon_lon = chart.planets["Moon"]["longitude"]
    moon_sign = get_sign(moon_lon)
    is_movable_moon = moon_sign in [0, 3, 6, 9]
    is_fixed_moon = moon_sign in [1, 4, 7, 10]
    is_dual_moon = moon_sign in [2, 5, 8, 11]
    
    enemy_verdict = "UNDETERMINED — Astrological factors are mixed."
    enemy_details = ""
    
    if is_movable_lagna and is_fixed_moon:
        enemy_verdict = "WILL NOT ARRIVE — The enemy will not march or reach."
        enemy_details = "Movable Lagna with Moon in a Fixed Sign (Shatpanchasika II.6)."
    elif is_fixed_lagna and is_movable_moon:
        enemy_verdict = "WILL ARRIVE — The enemy is marching and will reach to fight."
        enemy_details = "Fixed Lagna with Moon in a Movable Sign (Shatpanchasika II.6)."
    elif is_fixed_lagna and is_dual_moon:
        enemy_verdict = "RETREAT — The enemy will march a long distance but return without fighting."
        enemy_details = "Fixed Lagna with Moon in a Dual Sign (Shatpanchasika II.7)."
    elif is_dual_lagna and is_movable_moon:
        enemy_verdict = "MIDWAY RETURN — The enemy returns midway after coming halfway."
        enemy_details = "Dual Lagna with Moon in a Movable Sign (Shatpanchasika II.8)."
        
    # Check 4th house occupancy for armies (Sloka 11)
    house_4_sign = (lagna_sign + 3) % 12
    planets_in_4 = []
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        p_sign = get_sign(p_data["longitude"])
        if p_sign == house_4_sign:
            planets_in_4.append(p_name)
            
    # Sun & Moon in 4th -> no arrival
    if "Sun" in planets_in_4 and "Moon" in planets_in_4:
        enemy_verdict = "WILL NOT ARRIVE — Siege/army will not reach."
        enemy_details += " | Sun & Moon both occupy the 4th house (Shatpanchasika II.11)."
    elif any(x in planets_in_4 for x in ["Mercury", "Jupiter", "Venus"]) and not any(x in planets_in_4 for x in ["Sun", "Moon"]):
        enemy_verdict = "ARRIVING SOON — Siege/army will reach very rapidly!"
        enemy_details += " | Benefic (Mercury/Jupiter/Venus) occupies the 4th house (Shatpanchasika II.11)."

    # 4. SIEGE / WAR OUTCOME (Adhyaya III Slokas 1-2)
    # Citizens/Defenders (Pauras) = Houses 3, 4, 5, 6, 7, 8 (inclusive)
    # Besiegers/Invaders (Yayinas) = Houses 9, 10, 11, 12, 1, 2 (inclusive)
    paura_houses = [3, 4, 5, 6, 7, 8]
    yayina_houses = [9, 10, 11, 12, 1, 2]
    
    paura_benefics = 0
    paura_malefics = 0
    yayina_benefics = 0
    yayina_malefics = 0
    
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        p_sign = get_sign(p_data["longitude"])
        h_idx = ((p_sign - lagna_sign) % 12) + 1
        
        is_p_benefic = check_benefic(p_name, p_data)
        is_p_malefic = check_malefic(p_name, p_data)
        
        if h_idx in paura_houses:
            if is_p_benefic: paura_benefics += 1
            if is_p_malefic: paura_malefics += 1
        elif h_idx in yayina_houses:
            if is_p_benefic: yayina_benefics += 1
            if is_p_malefic: yayina_malefics += 1
            
    # Verdict based on strengths
    paura_score = paura_benefics - paura_malefics
    yayina_score = yayina_benefics - yayina_malefics
    
    if paura_score > yayina_score:
        siege_verdict = "VICTORY FOR CITIZENS / DEFENDERS — The home side / city will successfully defend itself."
    elif yayina_score > paura_score:
        siege_verdict = "VICTORY FOR BESIEGERS / INVADERS — The attackers / invaders will capture the city."
    else:
        siege_verdict = "PEACE / TREATY PROBABLE — Neither side can dominate. A compromise or treaty is indicated."

    return {
        "traveler_status": traveler_status,
        "return_timing_desc": return_timing_desc,
        "return_days": return_days,
        "enemy_verdict": enemy_verdict,
        "enemy_details": enemy_details,
        "siege_verdict": siege_verdict,
        "paura_score": paura_score,
        "yayina_score": yayina_score,
        "lagna_sign_name": get_sign_name(lagna_sign),
        "moon_sign_name": get_sign_name(moon_sign)
    }
