# miscellaneous.py
# Implements pregnancy, marriage, thought reading, and rain predictions
# based on Shatpanchasika Chapter VII

from .shatpanchasika import get_sign, aspects_sign, get_navamsa_sign
from .astronomy import get_sign_name

WATERY_SIGNS = [3, 9, 10, 11]  # Cancer, Capricorn, Aquarius, Pisces

# Friendships for thought reading (Saturn/Venus enemy Sun, etc. per B.J. II-16)
PLANET_FRIENDS = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"]
}

PLANET_ENEMIES = {
    "Sun": ["Saturn", "Venus"],
    "Moon": [],
    "Mars": ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus": ["Sun", "Moon"],
    "Saturn": ["Sun", "Moon", "Mars"]
}

def evaluate_miscellaneous_query(chart):
    """
    Evaluates miscellaneous horary queries using Shatpanchasika rules (Adhyaya VII).
    """
    lagna_sign = chart.lagna_sign
    lagna_lon = chart.lagna_sidereal
    lagna_deg = lagna_lon % 30.0
    sun_lon = chart.planets["Sun"]["longitude"]
    moon_lon = chart.planets["Moon"]["longitude"]
    
    # 1. PREGNANCY & GENDER PREDICTION (Sloka 1 & 5)
    mercury_lon = chart.planets["Mercury"]["longitude"]
    mercury_sign = get_sign(mercury_lon)
    is_pregnant = (mercury_sign == lagna_sign)
    
    # Gender Rule 1: Saturn in odd house
    saturn_lon = chart.planets["Saturn"]["longitude"]
    saturn_sign = get_sign(saturn_lon)
    saturn_house = ((saturn_sign - lagna_sign) % 12) + 1
    # Odd houses: 3, 5, 7, 9, 11 (per text: odd house from Lagna = son)
    saturn_in_odd_house = saturn_house in [3, 5, 7, 9, 11]
    
    # Gender Rule 2: Rising Varga gender & aspects
    # Odd signs = Masculine, Even signs = Feminine
    is_lagna_masculine = lagna_sign in [0, 2, 4, 6, 8, 10]
    nav_sign, nav_idx = get_navamsa_sign(lagna_lon)
    is_nav_masculine = nav_sign in [0, 2, 4, 6, 8, 10]
    
    male_aspects = 0
    female_aspects = 0
    
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        p_lon = p_data["longitude"]
        if aspects_sign(p_lon, lagna_sign):
            if p_name in ["Sun", "Mars", "Jupiter"]:
                male_aspects += 1
            elif p_name in ["Moon", "Venus"]:
                female_aspects += 1
                
    # Combine gender votes
    gender_votes_male = 0
    gender_votes_female = 0
    
    if saturn_in_odd_house:
        gender_votes_male += 2
    else:
        gender_votes_female += 2
        
    if is_lagna_masculine and is_nav_masculine and male_aspects > female_aspects:
        gender_votes_male += 2
    elif not is_lagna_masculine and not is_nav_masculine and female_aspects > male_aspects:
        gender_votes_female += 2
    else:
        # Mixed factors
        gender_votes_male += 1
        gender_votes_female += 1
        
    if gender_votes_male > gender_votes_female:
        gender_verdict = "MALE CHILD (BOY) — Highly probable."
        gender_reason = "Saturn in an odd house and/or masculine Lagna/Varga indicators with male aspects."
    elif gender_votes_female > gender_votes_male:
        gender_verdict = "FEMALE CHILD (GIRL) — Highly probable."
        gender_reason = "Saturn in an even house and/or feminine Lagna/Varga indicators with female aspects."
    else:
        gender_verdict = "MIXED / TWINS — Astrological indicators are evenly balanced."
        gender_reason = "Saturn's house placement and Lagna/Varga genders show conflicting or balanced male/female parameters."

    pregnancy_status = (
        "CONCEIVED (PREGNANT) — Mercury is in the rising sign, confirming pregnancy (VII.5)."
        if is_pregnant else
        "NOT CONCEIVED / PENDING — Mercury is not occupying the Lagna (VII.5)."
    )

    # 2. MARRIAGE & BRIDE ACQUISITION (Sloka 1-2)
    # Saturn in even house -> succeeds (gets bride)
    saturn_in_even_house = saturn_house in [2, 4, 6, 8, 10, 12]
    
    # Moon in 3, 5, 7, 11, 6 aspected by Jupiter, Sun, Mercury
    moon_sign = get_sign(moon_lon)
    moon_house = ((moon_sign - lagna_sign) % 12) + 1
    moon_in_marriage_house = moon_house in [3, 5, 6, 7, 11]
    
    has_jupiter_aspect = aspects_sign(chart.planets["Jupiter"]["longitude"], moon_sign)
    has_sun_aspect = aspects_sign(chart.planets["Sun"]["longitude"], moon_sign)
    has_mercury_aspect = aspects_sign(mercury_lon, moon_sign)
    moon_aspected_by_three = has_jupiter_aspect and has_sun_aspect and has_mercury_aspect
    
    # Benefics in Trikona/Kendras
    benefic_in_kendra_trikona = False
    kendra_trikona_signs = [lagna_sign, (lagna_sign + 3) % 12, (lagna_sign + 4) % 12, (lagna_sign + 6) % 12, (lagna_sign + 8) % 12, (lagna_sign + 9) % 12]
    for b in ["Mercury", "Venus", "Jupiter"]:
        bsign = get_sign(chart.planets[b]["longitude"])
        if bsign in kendra_trikona_signs:
            benefic_in_kendra_trikona = True
            
    marriage_conditions = []
    marriage_succeeds = False
    
    if saturn_in_even_house:
        marriage_succeeds = True
        marriage_conditions.append("Saturn is posited in an even house, indicating acquisition of bride (VII.1)")
    if moon_in_marriage_house and moon_aspected_by_three:
        marriage_succeeds = True
        marriage_conditions.append("Moon is in a favorable house aspected by Jupiter, Sun, and Mercury (VII.2)")
    if benefic_in_kendra_trikona:
        marriage_succeeds = True
        marriage_conditions.append("Benefic planets occupy the Kendra / Trikona houses (VII.2)")
        
    if marriage_succeeds:
        marriage_verdict = "YES — High Marriage Success Probability"
        marriage_reason = " | ".join(marriage_conditions)
    else:
        marriage_verdict = "NO / DELAYED — Low Marriage Success / Impediments"
        marriage_reason = "Saturn is in an odd house and Moon/benefics do not meet the classical marriage conjunction/aspect conditions."

    # 3. THOUGHT READING (Sloka 7-8)
    # Find strongest planet to locate the house
    from .shatpanchasika import get_strongest_planet
    strongest_p = get_strongest_planet(chart.planets, sun_lon)
    
    if strongest_p:
        p_lon = chart.planets[strongest_p]["longitude"]
        p_sign = get_sign(p_lon)
        strongest_house = ((p_sign - lagna_sign) % 12) + 1
        
        house_significations = {
            1: "Self / Personal Identity / Physical Health",
            3: "Brothers / Siblings / Relatives",
            4: "Mother / Sister / Property / Vehicles / Domestic Happiness",
            5: "Children / Offspring / Creative projects / Speculation",
            6: "Enemies / Competitors / Debts / Illnesses",
            7: "Wife / Partner / Marriage / Public Relations",
            9: "Spiritual Path / Father / Long Travel / Virtue",
            10: "Preceptor / Teacher / Career / Status / Authority"
        }
        subject_thought = house_significations.get(strongest_house, "General affairs / Undetermined house significations")
        thought_desc = f"Thinking about: {subject_thought} (Strongest planet {strongest_p} occupies House #{strongest_house} - VII.7-8)"
    else:
        thought_desc = "Thinking about: Self / General affairs (Strongest planet undetermined)"
        
    # Navamsa-lord relationship for thought reading (Sloka 8)
    nav_lord = chart.planets.get(chart.lagnapathi, {}).get("longitude", 0.0) # Fallback
    # Check if a planet occupies the Lagna
    planets_in_lagna = []
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        if get_sign(p_data["longitude"]) == lagna_sign:
            planets_in_lagna.append(p_name)
            
    if planets_in_lagna:
        p_in_l = planets_in_lagna[0]
        # Identify relationship to the Navamsa lord (which is the lord of the rising Navamsa)
        nav_lord_sign = get_sign(nav_sign)
        from .shatpanchasika import SIGN_LORDS
        nav_lord_name = SIGN_LORDS[nav_lord_sign]
        
        if p_in_l == nav_lord_name:
            thought_relation = "Self (Lagna occupied by the Navamsa Lord - VII.8)"
        elif p_in_l in PLANET_FRIENDS.get(nav_lord_name, []):
            thought_relation = f"A Friend / Well-wisher (Lagna occupied by {p_in_l}, friend of Navamsa Lord {nav_lord_name} - VII.8)"
        elif p_in_l in PLANET_ENEMIES.get(nav_lord_name, []):
            thought_relation = f"An Enemy / Opponent (Lagna occupied by {p_in_l}, enemy of Navamsa Lord {nav_lord_name} - VII.8)"
        else:
            thought_relation = f"Neutral acquaintance (Lagna occupied by {p_in_l}, neutral to Navamsa Lord {nav_lord_name})"
    else:
        thought_relation = "Self / Close association (No planet occupies the rising sign - VII.8)"

    # 4. WEATHER & RAIN PREDICTION (Slokas 3-4)
    # A. Venus and Saturn in 7th from Moon/Sun
    venus_lon = chart.planets["Venus"]["longitude"]
    venus_sign = get_sign(venus_lon)
    sun_sign = get_sign(sun_lon)
    
    venus_from_moon = (venus_sign - moon_sign) % 12
    saturn_from_sun = (saturn_sign - sun_sign) % 12
    is_rain_yoga_a = (venus_from_moon == 6 and saturn_from_sun == 6)
    
    # B. Venus and Saturn in 4th and 8th from Lagna
    saturn_house = ((saturn_sign - lagna_sign) % 12) + 1
    venus_house = ((venus_sign - lagna_sign) % 12) + 1
    is_rain_yoga_b = (saturn_house in [4, 8] and venus_house in [4, 8] and saturn_house != venus_house)
    
    # C. Venus and Saturn in 2nd and 3rd from Lagna
    is_rain_yoga_c = (saturn_house in [2, 3] and venus_house in [2, 3] and saturn_house != venus_house)
    
    # D. Watery signs occupied by benefics in 1, 2, 3, 4, 7, 10
    watery_benefic_count = 0
    watery_houses_checked = [1, 2, 3, 4, 7, 10]
    for b in ["Mercury", "Venus", "Jupiter", "Moon"]:
        bsign = get_sign(chart.planets[b]["longitude"])
        bhouse = ((bsign - lagna_sign) % 12) + 1
        if bhouse in watery_houses_checked and bsign in WATERY_SIGNS:
            watery_benefic_count += 1
            
    # E. Moon in Lagna identical with a watery sign
    is_moon_in_watery_lagna = (moon_sign == lagna_sign and lagna_sign in WATERY_SIGNS)
    
    rain_reasons = []
    if is_rain_yoga_a:
        rain_reasons.append("Venus and Saturn occupy the 7th house from the Moon and Sun respectively (VII.3)")
    if is_rain_yoga_b:
        rain_reasons.append("Venus and Saturn occupy the 4th and 8th houses from the Lagna (VII.3)")
    if is_rain_yoga_c:
        rain_reasons.append("Venus and Saturn occupy the 2nd and 3rd houses from the Lagna (VII.3)")
    if watery_benefic_count >= 2:
        rain_reasons.append("Multiple benefic planets occupy watery signs in Kendra/Panapharas (VII.4)")
    if is_moon_in_watery_lagna:
        rain_reasons.append("Moon is posited in the Lagna identical with a watery sign (VII.4)")
        
    if rain_reasons:
        rain_verdict = "YES — High Probability of Rain / Wet weather"
        rain_reason_text = " | ".join(rain_reasons)
    else:
        rain_verdict = "NO — Dry / Unlikely Rain"
        rain_reason_text = "No classical water combinations or Venus-Saturn alignments are present."

    return {
        "pregnancy_status": pregnancy_status,
        "gender_verdict": gender_verdict,
        "gender_reason": gender_reason,
        "marriage_verdict": marriage_verdict,
        "marriage_reason": marriage_reason,
        "thought_desc": thought_desc,
        "thought_relation": thought_relation,
        "rain_verdict": rain_verdict,
        "rain_reason": rain_reason_text,
        "lagna_sign_name": get_sign_name(lagna_sign)
    }
