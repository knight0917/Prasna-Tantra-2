# children.py
# Dedicated childbirth & progeny query evaluator based on Prasna Tantra Chapter III, Stanzas 79-91

from .shatpanchasika import get_sign, get_navamsa_sign, aspects_sign
from .astronomy import get_sign_name
from .tajaka import get_planet_relationship, get_planetary_avastha

# Traditional Vedic Sign Ownership
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon",
    4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars",
    8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"
}

# Sign Qualities
SIGN_QUALITIES = {
    0: "Movable", 3: "Movable", 6: "Movable", 9: "Movable",
    1: "Fixed", 4: "Fixed", 7: "Fixed", 10: "Fixed",
    2: "Common", 5: "Common", 8: "Common", 11: "Common"
}

# Planet genders
PLANET_GENDERS = {
    "Sun": "Male", "Mars": "Male", "Jupiter": "Male",
    "Moon": "Female", "Venus": "Female",
    "Mercury": "Mixed/Dual", "Saturn": "Mixed/Neutral"
}

def get_planet_score(planet_name, lon):
    sign = get_sign(lon)
    score = 10
    exaltations = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
    own_signs = {"Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5], "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]}
    
    if sign == exaltations.get(planet_name):
        score += 15
    elif sign in own_signs.get(planet_name, []):
        score += 10
    return score

def evaluate_children_query(chart):
    """
    Evaluates childbirth, progeny, and pregnancy queries using Prasna Tantra rules (Stanzas 79-91).
    """
    lagna_sign = chart.lagna_sign
    lagna_lon = chart.lagna_sidereal
    
    # 5th House details
    fifth_sign = (lagna_sign + 4) % 12
    lagnapathi = SIGN_LORDS[lagna_sign]
    karyesa = SIGN_LORDS[fifth_sign]
    
    lagnapathi_lon = chart.planets[lagnapathi]["longitude"]
    karyesa_lon = chart.planets[karyesa]["longitude"]
    
    # Jupiter (putrakaraka) and Moon
    jupiter_lon = chart.planets["Jupiter"]["longitude"]
    moon_lon = chart.planets["Moon"]["longitude"]
    
    # 1. Progeny indicators strength (Stanzas 79-80)
    jupiter_data = chart.planets["Jupiter"]
    jupiter_strength = get_planet_score("Jupiter", jupiter_lon)
    sun_lon = chart.planets["Sun"]["longitude"]
    jupiter_avastha = get_planetary_avastha("Jupiter", jupiter_lon, jupiter_data, sun_lon, chart.planets)
    
    karyesa_data = chart.planets[karyesa]
    karyesa_avastha = get_planetary_avastha(karyesa, karyesa_lon, karyesa_data, sun_lon, chart.planets)
    
    # Occupants of 5th
    fifth_house_occupants = []
    fifth_house_benefics = []
    fifth_house_malefics = []
    
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        p_sign = get_sign(p_data["longitude"])
        if p_sign == fifth_sign:
            fifth_house_occupants.append(p_name)
            if p_name in ["Jupiter", "Venus", "Mercury", "Moon"]:
                fifth_house_benefics.append(p_name)
            else:
                fifth_house_malefics.append(p_name)
                
    # Aspects on 5th
    aspecting_5th_benefics = []
    aspecting_5th_malefics = []
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"] or p_name in fifth_house_occupants:
            continue
        if aspects_sign(p_data["longitude"], fifth_sign):
            if p_name in ["Jupiter", "Venus", "Mercury", "Moon"]:
                aspecting_5th_benefics.append(p_name)
            else:
                aspecting_5th_malefics.append(p_name)
                
    # 2. Childbirth Success / Conjunction Verdict (Stanzas 81-84)
    rel_1_5 = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], karyesa, chart.planets[karyesa])
    
    birth_promised = False
    birth_conditions = []
    
    if rel_1_5 and rel_1_5["is_applying"] and rel_1_5["is_friendly"]:
        birth_promised = True
        birth_conditions.append(f"Ascendant Lord ({lagnapathi}) and 5th Lord ({karyesa}) are in friendly applying aspect ({rel_1_5['aspect_type']}) (Stanza 81)")
    elif rel_1_5 and rel_1_5["aspect_type"] == "Conjunction" and rel_1_5["is_applying"]:
        birth_promised = True
        birth_conditions.append(f"Ascendant Lord ({lagnapathi}) and 5th Lord ({karyesa}) are in applying Conjunction (Stanza 81)")
        
    if jupiter_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"] and (fifth_house_benefics or aspecting_5th_benefics):
        birth_promised = True
        birth_conditions.append("Jupiter is strong, and the 5th house receives benefic influence (Stanza 82)")
        
    # Delay check (Stanza 83/89)
    saturn_lon = chart.planets["Saturn"]["longitude"]
    saturn_sign = get_sign(saturn_lon)
    saturn_influences_5 = (saturn_sign == fifth_sign) or aspects_sign(saturn_lon, fifth_sign)
    
    obstacles_desc = "None"
    if saturn_influences_5:
        obstacles_desc = "Delay or obstruction in childbirth indicated by Saturn's slow influence on the 5th house/lord (Stanza 83/89)"
        
    # Benefic recovery check (Stanza 84)
    benefic_support = False
    if obstacles_desc != "None" and (fifth_house_benefics or aspecting_5th_benefics):
        benefic_support = True
        birth_promised = True
        birth_conditions.append("Initial delays are overcome because benefics aspect the 5th house/lord (Stanza 84)")
        
    # 3. Child Gender Evaluation (Stanza 85)
    # Odd signs = Masculine, Even signs = Feminine
    male_votes = 0
    female_votes = 0
    
    # Sign of 5th house
    if fifth_sign in [0, 2, 4, 6, 8, 10]:
        male_votes += 1
    else:
        female_votes += 1
        
    # Sign of 5th lord
    karyesa_sign = get_sign(karyesa_lon)
    if karyesa_sign in [0, 2, 4, 6, 8, 10]:
        male_votes += 1
    else:
        female_votes += 1
        
    # Lord gender
    if PLANET_GENDERS.get(karyesa) == "Male":
        male_votes += 1.5
    elif PLANET_GENDERS.get(karyesa) == "Female":
        female_votes += 1.5
        
    # Influencing planets
    all_influencing = fifth_house_occupants + aspecting_5th_benefics + aspecting_5th_malefics
    for p in all_influencing:
        if PLANET_GENDERS.get(p) == "Male":
            male_votes += 1
        elif PLANET_GENDERS.get(p) == "Female":
            female_votes += 1
            
    if male_votes > female_votes:
        gender_verdict = "MALE CHILD (BOY) — Highly probable."
        gender_reason = f"Masculine indicators dominate (Odd signs, male planets, or male aspects: Male score {male_votes:.1f} vs Female score {female_votes:.1f})"
    elif female_votes > male_votes:
        gender_verdict = "FEMALE CHILD (GIRL) — Highly probable."
        gender_reason = f"Feminine indicators dominate (Even signs, female planets, or female aspects: Female score {female_votes:.1f} vs Male score {male_votes:.1f})"
    else:
        gender_verdict = "MIXED / TWINS — Balanced indicators."
        gender_reason = f"Male and female parameters are equally balanced (Score {male_votes:.1f} - {female_votes:.1f})"
        
    # 4. Progeny Welfare (Stanza 86-87)
    if fifth_house_malefics or aspecting_5th_malefics:
        welfare_status = "Anxiety/Suffering. Malefics occupy or aspect the 5th house, indicating possible health concerns, educational blocks, or anxiety for the child (Stanza 87)."
    else:
        welfare_status = "Good Health & Prosperity. Only benefics influence the 5th house, indicating intelligence, vitality, and academic success for the child (Stanza 86)."
        
    # 5. Progeny Multiplicity (Stanza 88)
    has_multi_aspects = (len(fifth_house_benefics) + len(aspecting_5th_benefics)) >= 2
    is_jupiter_moon_connected = aspects_sign(jupiter_lon, get_sign(moon_lon)) or (get_sign(jupiter_lon) == get_sign(moon_lon))
    
    multiplicity_status = "Single child / standard progeny indicated."
    if has_multi_aspects or (is_jupiter_moon_connected and jupiter_strength >= 15):
        multiplicity_status = "Multiple children/larger family indicated due to multiple benefic aspects and strong Jupiter connection (Stanza 88)."
        
    # 6. Childbirth Timing (Stanza 90-91)
    lagna_quality = SIGN_QUALITIES[lagna_sign]
    karyesa_quality = SIGN_QUALITIES[karyesa_sign]
    
    timing_quality_desc = ""
    if lagna_quality == "Movable" or karyesa_quality == "Movable":
        timing_quality_desc = "Quick outcome/childbirth soon (Stanza 91)."
        time_unit = "months"
    elif lagna_quality == "Common" or karyesa_quality == "Common":
        timing_quality_desc = "Moderate timing/standard duration (Stanza 91)."
        time_unit = "months"
    else:
        timing_quality_desc = "Delayed outcome/long waiting period (Stanza 91)."
        time_unit = "years"
        
    timing_desc = "Timing undetermined (No direct applying aspect between significators)"
    time_val = None
    
    if rel_1_5 and rel_1_5["is_applying"]:
        deg_diff = abs(lagnapathi_lon - karyesa_lon) % 360
        if deg_diff > 180:
            deg_diff = 360 - deg_diff
            
        time_val = round(deg_diff)
        if time_val == 0:
            time_val = 1
            
        # For pregnancy, degree diff is often mapped to months/weeks
        timing_desc = f"Delivery/Conception expected in approx. {time_val} {time_unit} (based on degrees difference of {deg_diff:.1f}° under {lagna_quality}/{karyesa_quality} signs)."
        
    # Final verdict
    if birth_promised:
        verdict = "YES — Favorable Progeny Prospects"
        reason = " | ".join(birth_conditions)
    else:
        verdict = "NO / DELAYED — Low Progeny Prospects / Impediments"
        reason = "No favorable applying aspect between Lagnapathi and 5th Lord, and Jupiter is not favorably posited."
        if obstacles_desc != "None":
            reason += f" | Obstacles: {obstacles_desc}"
            
    return {
        "verdict": verdict,
        "reason": reason,
        "progeny_welfare": welfare_status,
        "progeny_multiplicity": multiplicity_status,
        "gender_verdict": gender_verdict,
        "gender_reason": gender_reason,
        "timing_desc": timing_desc,
        "timing_quality_desc": timing_quality_desc,
        "obstacles": obstacles_desc,
        "jupiter_avastha": jupiter_avastha,
        "jupiter_strength": jupiter_strength,
        "karyesa_avastha": karyesa_avastha
    }
