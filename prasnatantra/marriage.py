# marriage.py
# Dedicated marriage query evaluator based on Prasna Tantra Chapter III, Stanzas 65-78

from .shatpanchasika import get_sign, get_navamsa_sign, aspects_sign
from .astronomy import get_sign_name
from .tajaka import get_planet_relationship, get_planetary_avastha

# Traditional Vedic Sign Ownership
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon",
    4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars",
    8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"
}

# Sign Qualities: 0: Movable, 1: Fixed, 2: Common
SIGN_QUALITIES = {
    0: "Movable", 3: "Movable", 6: "Movable", 9: "Movable",
    1: "Fixed", 4: "Fixed", 7: "Fixed", 10: "Fixed",
    2: "Common", 5: "Common", 8: "Common", 11: "Common"
}

# Planet strengths helper
def get_planet_score(planet_name, lon):
    sign = get_sign(lon)
    score = 10
    
    # Exaltations
    exaltations = {
        "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6
    }
    # Own signs
    own_signs = {
        "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5], "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]
    }
    
    if sign == exaltations.get(planet_name):
        score += 15
    elif sign in own_signs.get(planet_name, []):
        score += 10
        
    return score

def evaluate_marriage_query(chart):
    """
    Evaluates marriage questions using Prasna Tantra Chapter III Stanzas 65-78 rules.
    """
    lagna_sign = chart.lagna_sign
    lagna_lon = chart.lagna_sidereal
    
    # Rulers and significators
    lagnapathi = SIGN_LORDS[lagna_sign]
    seventh_sign = (lagna_sign + 6) % 12
    karyesa = SIGN_LORDS[seventh_sign]
    
    lagnapathi_lon = chart.planets[lagnapathi]["longitude"]
    karyesa_lon = chart.planets[karyesa]["longitude"]
    
    # Venus (sig of marriage) and Moon (sig of mind/desire)
    venus_lon = chart.planets["Venus"]["longitude"]
    moon_lon = chart.planets["Moon"]["longitude"]
    
    # 1. Evaluate Strengths (Stanzas 65-66)
    seventh_house_strength = "Moderate"
    seventh_house_occupants = []
    seventh_house_benefics = []
    seventh_house_malefics = []
    
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        p_sign = get_sign(p_data["longitude"])
        if p_sign == seventh_sign:
            seventh_house_occupants.append(p_name)
            if p_name in ["Jupiter", "Venus", "Mercury", "Moon"]:
                seventh_house_benefics.append(p_name)
            else:
                seventh_house_malefics.append(p_name)
                
    # Aspects on 7th
    aspecting_7th_benefics = []
    aspecting_7th_malefics = []
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"] or p_name in seventh_house_occupants:
            continue
        if aspects_sign(p_data["longitude"], seventh_sign):
            if p_name in ["Jupiter", "Venus", "Mercury", "Moon"]:
                aspecting_7th_benefics.append(p_name)
            else:
                aspecting_7th_malefics.append(p_name)
                
    if (seventh_house_benefics or aspecting_7th_benefics) and not (seventh_house_malefics or aspecting_7th_malefics):
        seventh_house_strength = "Strong (Benefic associated)"
    elif (seventh_house_malefics or aspecting_7th_malefics) and not (seventh_house_benefics or aspecting_7th_benefics):
        seventh_house_strength = "Weak (Malefic afflicted)"
    
    # Lord and Venus strengths
    sun_lon = chart.planets["Sun"]["longitude"]
    karyesa_data = chart.planets[karyesa]
    karyesa_strength = get_planet_score(karyesa, karyesa_lon)
    karyesa_avastha = get_planetary_avastha(karyesa, karyesa_lon, karyesa_data, sun_lon, chart.planets)
    
    venus_data = chart.planets["Venus"]
    venus_strength = get_planet_score("Venus", venus_lon)
    venus_avastha = get_planetary_avastha("Venus", venus_lon, venus_data, sun_lon, chart.planets)
    
    # 2. Relationship Analysis (Stanzas 67-70)
    rel_1_7 = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], karyesa, chart.planets[karyesa])
    
    marriage_succeeds = False
    marriage_conditions = []
    
    if rel_1_7 and rel_1_7["is_applying"] and rel_1_7["is_friendly"]:
        marriage_succeeds = True
        marriage_conditions.append(f"Ascendant Lord ({lagnapathi}) and 7th Lord ({karyesa}) have friendly applying aspect ({rel_1_7['aspect_type']}) (Stanza 67/69)")
    elif rel_1_7 and rel_1_7["aspect_type"] == "Conjunction" and rel_1_7["is_applying"]:
        marriage_succeeds = True
        marriage_conditions.append(f"Ascendant Lord ({lagnapathi}) and 7th Lord ({karyesa}) are in applying Conjunction (Stanza 67)")
        
    if "Strong" in seventh_house_strength:
        marriage_conditions.append("Seventh house is strong and supported by benefics (Stanza 66/68)")
        if not marriage_conditions:
            marriage_succeeds = True
            
    # Obstacles check
    saturn_lon = chart.planets["Saturn"]["longitude"]
    saturn_sign = get_sign(saturn_lon)
    saturn_influences_7 = (saturn_sign == seventh_sign) or aspects_sign(saturn_lon, seventh_sign)
    
    mars_lon = chart.planets["Mars"]["longitude"]
    mars_sign = get_sign(mars_lon)
    mars_influences_7 = (mars_sign == seventh_sign) or aspects_sign(mars_lon, seventh_sign)
    
    obstacles_desc = "None"
    if saturn_influences_7 and mars_influences_7:
        obstacles_desc = "Severe quarrels and friction indicated by Mars and Saturn afflicting the 7th house (Stanza 73)"
    elif saturn_influences_7:
        obstacles_desc = "Delay in union/marriage due to Saturn's cold influence on the 7th house (Stanza 72)"
    elif mars_influences_7:
        obstacles_desc = "Aggression, disputes or sudden arguments indicated by Mars influencing the 7th house (Stanza 70/73)"
        
    # 3. Spouse Personality & Appearance Profile (Stanza 71)
    # Determine dominant planet influencing the 7th house
    influencing_planet = None
    influence_reason = ""
    
    if seventh_house_occupants:
        # Sort by strength
        occ_strengths = []
        for occ in seventh_house_occupants:
            occ_strengths.append((occ, get_planet_score(occ, chart.planets[occ]["longitude"])))
        occ_strengths.sort(key=lambda x: x[1], reverse=True)
        influencing_planet = occ_strengths[0][0]
        influence_reason = f"Occupies the 7th house ({influencing_planet})"
    elif aspecting_7th_benefics or aspecting_7th_malefics:
        all_aspecting = aspecting_7th_benefics + aspecting_7th_malefics
        aspect_strengths = []
        for asp in all_aspecting:
            aspect_strengths.append((asp, get_planet_score(asp, chart.planets[asp]["longitude"])))
        aspect_strengths.sort(key=lambda x: x[1], reverse=True)
        influencing_planet = aspect_strengths[0][0]
        influence_reason = f"Strongest planet aspecting the 7th house ({influencing_planet})"
    else:
        influencing_planet = karyesa
        influence_reason = f"7th Lord ({karyesa}) as no planets occupy or aspect the 7th house"
        
    spouse_profiles = {
        "Sun": {
            "personality": "Proud, noble, authoritative, independent, and high-minded.",
            "appearance": "Dignified carriage, honey-colored eyes, prominent forehead, regal appearance.",
            "status": "High status, government connected, or belongs to an influential family."
        },
        "Moon": {
            "personality": "Emotional, highly sensitive, nurturing, caring, but prone to changing moods.",
            "appearance": "Round attractive face, fair skin, beautiful eyes, gentle and pleasant expression.",
            "status": "Involved in mercantile, hospitality, public welfare, or domestic arts."
        },
        "Mars": {
            "personality": "Passionate, courageous, active, quick-tempered, highly energetic, and competitive.",
            "appearance": "Athletic build, sharp/martial features, active stance, youthful expression.",
            "status": "Signifies police, army officers, technical workers, builders, or active sportspeople."
        },
        "Mercury": {
            "personality": "Intelligent, highly communicative, witty, adaptable, clever, and intellectually curious.",
            "appearance": "Youthful/juvenile appearance, slender build, active eyes, highly expressive face.",
            "status": "Involved in trade, writing, education, accounts, or communication systems."
        },
        "Jupiter": {
            "personality": "Wise, respectable, deeply moral, generous, supportive, religious, and calm.",
            "appearance": "Stately/large frame, golden/honey eyes, calm and trustworthy expression.",
            "status": "Signifies scholars, teachers, religious heads, advisors, or legal professionals."
        },
        "Venus": {
            "personality": "Extremely romantic, loving, peaceful, artistic, beauty-loving, and diplomatic.",
            "appearance": "Very attractive, charming, curl-haired, bright and pleasing eyes.",
            "status": "Involved in luxury, arts, entertainment, music, or design."
        },
        "Saturn": {
            "personality": "Mature, serious, highly disciplined, reserved, pragmatic, and serious-minded.",
            "appearance": "Older looking, tall/bony frame, dark complexion, serious or tired eyes.",
            "status": "Hardworking employee, farmer, manual laborer, or a highly reserved professional."
        },
        "Rahu": {
            "personality": "Unconventional, secretive, highly ambitious, obsessive, or adventurous.",
            "appearance": "Unusual or exotic appearance, deep/intense gaze, distinctive marks.",
            "status": "Foreigner, outsider, non-traditional background, or technology related."
        },
        "Ketu": {
            "personality": "Introverted, spiritual, eccentric, detached, or mysterious.",
            "appearance": "Distinctive/atypical look, quiet presence, simple or unconventional dress.",
            "status": "Spiritual seeker, philosopher, or belongs to a secluded circle."
        }
    }
    
    profile = spouse_profiles.get(influencing_planet, {
        "personality": "Balanced, standard qualities.",
        "appearance": "Standard features.",
        "status": "General background."
    })
    
    # 4. Love vs. Traditional (Stanzas 75-76)
    # Check 5th lord (romance) and 7th lord connection
    fifth_sign = (lagna_sign + 4) % 12
    fifth_lord = SIGN_LORDS[fifth_sign]
    
    rel_5_7 = get_planet_relationship(fifth_lord, chart.planets[fifth_lord], karyesa, chart.planets[karyesa])
    
    is_love_marriage = False
    marriage_type_details = ""
    
    if rel_5_7 and rel_5_7["is_applying"] and rel_5_7["is_friendly"]:
        is_love_marriage = True
        marriage_type_details = f"Love / Romantic Alliance. Reason: Friendly applying aspect ({rel_5_7['aspect_type']}) between 5th Lord ({fifth_lord}) and 7th Lord ({karyesa}) (Stanza 75)."
    elif aspects_sign(venus_lon, fifth_sign):
        is_love_marriage = True
        marriage_type_details = f"Romantic Union. Reason: Venus (marriage significator) aspects the 5th house of romance/desires."
    else:
        marriage_type_details = "Traditional / Arranged Alliance. Reason: Family-related houses (2nd, 9th) dominate and there is no friendly 5th-7th lord Ithasala (Stanza 76)."
        
    # 5. Timing of Marriage (Stanzas 77-78)
    lagna_quality = SIGN_QUALITIES[lagna_sign]
    karyesa_quality = SIGN_QUALITIES[get_sign(karyesa_lon)]
    
    # Quality details
    timing_quality_desc = ""
    if lagna_quality == "Movable" or karyesa_quality == "Movable":
        timing_quality_desc = "Quick union/marriage indicated due to Movable sign influence (Stanza 78)."
        time_unit = "weeks"
    elif lagna_quality == "Common" or karyesa_quality == "Common":
        timing_quality_desc = "Moderate timing/some delays indicated due to Common sign influence (Stanza 78)."
        time_unit = "months"
    else:
        timing_quality_desc = "Prolonged waiting period/significant delay indicated due to Fixed sign influence (Stanza 78)."
        time_unit = "years"
        
    timing_desc = "Timing undetermined (No direct applying aspect between 1st and 7th lords)"
    time_val = None
    
    if rel_1_7 and rel_1_7["is_applying"]:
        deg_diff = abs(lagnapathi_lon - karyesa_lon) % 360
        if deg_diff > 180:
            deg_diff = 360 - deg_diff
            
        time_val = round(deg_diff)
        if time_val == 0:
            time_val = 1
            
        timing_desc = f"Union expected in approx. {time_val} {time_unit} (based on significators separating/applying gap of {deg_diff:.1f}° under {lagna_quality}/{karyesa_quality} signs)."
        
    # Compile final verdict
    if marriage_succeeds:
        verdict = "YES — High Marriage Success Probability"
        reason = " | ".join(marriage_conditions)
    else:
        verdict = "NO / DELAYED — Impediments / Low Success Probability"
        reason = "No favorable applying aspect between Ascendant Lord and 7th Lord, or 7th house is heavily afflicted."
        if obstacles_desc != "None":
            reason += f" | Obstacles: {obstacles_desc}"
            
    return {
        "verdict": verdict,
        "reason": reason,
        "seventh_house_strength": seventh_house_strength,
        "karyesa_avastha": karyesa_avastha,
        "karyesa_strength": karyesa_strength,
        "venus_avastha": venus_avastha,
        "venus_strength": venus_strength,
        "spouse_personality": profile["personality"],
        "spouse_appearance": profile["appearance"],
        "spouse_status": profile["status"],
        "spouse_influencing_planet": influencing_planet,
        "spouse_influence_reason": influence_reason,
        "marriage_type": "Love Marriage" if is_love_marriage else "Arranged / Traditional",
        "marriage_type_details": marriage_type_details,
        "timing_desc": timing_desc,
        "timing_quality_desc": timing_quality_desc,
        "obstacles": obstacles_desc
    }
