# wealth.py
# Dedicated wealth & financial query evaluator based on Prasna Tantra Chapter IV, Stanzas 1-6 & Chapter II, Stanzas 19-28

from .shatpanchasika import get_sign, aspects_sign
from .astronomy import get_sign_name
from .tajaka import get_planet_relationship, get_planetary_avastha, check_combustion

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

def evaluate_wealth_query(chart):
    """
    Evaluates wealth, financial transactions, accumulated assets, gains, and lost wealth recovery 
    using Prasna Tantra rules (Chapter IV, Stanzas 1-6 & Chapter II, Stanzas 19-28).
    """
    lagna_sign = chart.lagna_sign
    lagna_lon = chart.lagna_sidereal
    
    lagnapathi = SIGN_LORDS[lagna_sign]
    lagnapathi_lon = chart.planets[lagnapathi]["longitude"]
    
    # 2nd House (Accumulated wealth)
    second_sign = (lagna_sign + 1) % 12
    second_lord = SIGN_LORDS[second_sign]
    second_lord_lon = chart.planets[second_lord]["longitude"]
    
    # 11th House (Incoming gains)
    eleventh_sign = (lagna_sign + 10) % 12
    eleventh_lord = SIGN_LORDS[eleventh_sign]
    eleventh_lord_lon = chart.planets[eleventh_lord]["longitude"]
    
    # Sun and Moon longitudes
    sun_lon = chart.planets["Sun"]["longitude"]
    moon_lon = chart.planets["Moon"]["longitude"]
    
    # 1. Strengths of Significators (Stanzas 19-20)
    second_lord_data = chart.planets[second_lord]
    second_lord_strength = get_planet_score(second_lord, second_lord_lon)
    second_lord_avastha = get_planetary_avastha(second_lord, second_lord_lon, second_lord_data, sun_lon, chart.planets)
    
    eleventh_lord_data = chart.planets[eleventh_lord]
    eleventh_lord_strength = get_planet_score(eleventh_lord, eleventh_lord_lon)
    eleventh_lord_avastha = get_planetary_avastha(eleventh_lord, eleventh_lord_lon, eleventh_lord_data, sun_lon, chart.planets)
    
    lagnapathi_data = chart.planets[lagnapathi]
    lagnapathi_avastha = get_planetary_avastha(lagnapathi, lagnapathi_lon, lagnapathi_data, sun_lon, chart.planets)
    
    # Combustion & Nipeeditaha
    combust_2nd = check_combustion(second_lord, second_lord_lon, sun_lon)
    combust_11th = check_combustion(eleventh_lord, eleventh_lord_lon, sun_lon)
    
    # Occupants of 2nd and 11th Houses (Stanza 2, 21-22)
    occ_2nd_benefics = []
    occ_2nd_malefics = []
    occ_11th_benefics = []
    occ_11th_malefics = []
    
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        p_sign = get_sign(p_data["longitude"])
        is_benefic = p_name in ["Jupiter", "Venus", "Mercury", "Moon"]
        # Mercury combust check
        if p_name == "Mercury" and check_combustion("Mercury", p_data["longitude"], sun_lon):
            is_benefic = False
            
        if p_sign == second_sign:
            if is_benefic:
                occ_2nd_benefics.append(p_name)
            else:
                if p_name != second_lord:
                    occ_2nd_malefics.append(p_name)
        elif p_sign == eleventh_sign:
            if is_benefic:
                occ_11th_benefics.append(p_name)
            else:
                if p_name != eleventh_lord:
                    occ_11th_malefics.append(p_name)
                
    # Aspects on 2nd and 11th Houses
    asp_2nd_benefics = []
    asp_2nd_malefics = []
    asp_11th_benefics = []
    asp_11th_malefics = []
    
    for p_name, p_data in chart.planets.items():
        if p_name in ["Ketu"]:
            continue
        p_sign = get_sign(p_data["longitude"])
        is_benefic = p_name in ["Jupiter", "Venus", "Mercury", "Moon"]
        if p_name == "Mercury" and check_combustion("Mercury", p_data["longitude"], sun_lon):
            is_benefic = False
            
        if p_sign != second_sign and aspects_sign(p_data["longitude"], second_sign):
            if is_benefic:
                asp_2nd_benefics.append(p_name)
            else:
                if p_name != second_lord:
                    asp_2nd_malefics.append(p_name)
        if p_sign != eleventh_sign and aspects_sign(p_data["longitude"], eleventh_sign):
            if is_benefic:
                asp_11th_benefics.append(p_name)
            else:
                if p_name != eleventh_lord:
                    asp_11th_malefics.append(p_name)
                
    # 2. Financial Yogas / Connections (Chapter IV Stanza 3, Chapter II Stanza 23)
    rel_1_2 = get_planet_relationship(lagnapathi, lagnapathi_data, second_lord, second_lord_data)
    rel_1_11 = get_planet_relationship(lagnapathi, lagnapathi_data, eleventh_lord, eleventh_lord_data)
    rel_2_11 = get_planet_relationship(second_lord, second_lord_data, eleventh_lord, eleventh_lord_data)
    
    wealth_promised = False
    wealth_conditions = []
    
    # Lagna Lord and 2nd/11th Lord relations
    if rel_1_2 and rel_1_2["is_applying"] and rel_1_2["is_friendly"]:
        wealth_promised = True
        wealth_conditions.append(f"Ascendant Lord ({lagnapathi}) and 2nd Lord ({second_lord}) are in friendly applying aspect ({rel_1_2['aspect_type']}) (Ch II Stanza 20)")
    elif rel_1_2 and rel_1_2["aspect_type"] == "Conjunction" and rel_1_2["is_applying"]:
        wealth_promised = True
        wealth_conditions.append(f"Ascendant Lord ({lagnapathi}) and 2nd Lord ({second_lord}) are in applying Conjunction (Ch II Stanza 20)")
        
    if rel_1_11 and rel_1_11["is_applying"] and rel_1_11["is_friendly"]:
        wealth_promised = True
        wealth_conditions.append(f"Ascendant Lord ({lagnapathi}) and 11th Lord ({eleventh_lord}) are in friendly applying aspect ({rel_1_11['aspect_type']}) (Ch IV Stanza 1)")
        
    # 2nd Lord and 11th Lord connection (Stanza 3: "combine favourably")
    if rel_2_11 and rel_2_11["is_applying"] and rel_2_11["is_friendly"]:
        wealth_promised = True
        wealth_conditions.append(f"2nd Lord ({second_lord}) and 11th Lord ({eleventh_lord}) are in friendly applying aspect ({rel_2_11['aspect_type']}) (Ch IV Stanza 3)")
    elif rel_2_11 and rel_2_11["aspect_type"] == "Conjunction" and rel_2_11["is_applying"]:
        wealth_promised = True
        wealth_conditions.append(f"2nd Lord ({second_lord}) and 11th Lord ({eleventh_lord}) are conjoined (Ch IV Stanza 3)")
        
    # Benefic placement condition
    if (occ_2nd_benefics or asp_2nd_benefics) and (occ_11th_benefics or asp_11th_benefics):
        wealth_promised = True
        wealth_conditions.append("Both 2nd and 11th houses receive benefic placement or aspects (Ch IV Stanza 2)")
        
    # 3. Accumulated Wealth Status
    if combust_2nd or second_lord_avastha in ["Deena", "Mushita", "Nipeeditha", "Suptha"] or occ_2nd_malefics:
        acc_wealth_status = "Weak/Afflicted. The 2nd house or its lord suffers from malefic placement or a weak planetary state, suggesting financial tightness, drainage of savings, or expenses (Ch II Stanza 22)."
    else:
        acc_wealth_status = "Strong/Stable. The 2nd house is well-fortified, indicating good savings, increase of asset values, or receipt of pending dues (Ch II Stanza 19)."
        
    # 4. Incoming Gains Status
    if combust_11th or eleventh_lord_avastha in ["Deena", "Mushita", "Nipeeditha", "Suptha"] or occ_11th_malefics:
        gains_status = "Delayed/Restricted. Incoming profits or business gains face delays and setbacks due to malefic influence on the 11th house/lord (Ch IV Stanza 6)."
    else:
        gains_status = "Prosperous. Favorable planetary configurations signify continuous flow of income and realization of financial desires (Ch IV Stanza 5)."

    # 5. Lost Wealth & Valuables Recovery (Ch II Stanza 24-26)
    lost_recovery_promised = False
    lost_recovery_reason = ""
    
    # Stanza 26: Moon applies to significator (2nd lord)
    rel_moon_2nd = get_planet_relationship("Moon", chart.planets["Moon"], second_lord, second_lord_data)
    
    if second_lord_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"] and (asp_2nd_benefics or occ_2nd_benefics):
        lost_recovery_promised = True
        lost_recovery_reason = "2nd Lord is strong and aspected/joined by benefics, promising recovery (Ch II Stanza 24)."
    elif rel_moon_2nd and rel_moon_2nd["is_applying"] and rel_moon_2nd["is_friendly"]:
        lost_recovery_promised = True
        lost_recovery_reason = "Moon is in friendly applying aspect (Ithasala) with the 2nd Lord, indicating quick recovery (Ch II Stanza 26)."
        
    if not lost_recovery_promised:
        if occ_2nd_malefics or asp_2nd_malefics or second_lord_avastha in ["Deena", "Mushita", "Nipeeditha"]:
            lost_recovery_verdict = "NO — Recovery Highly Doubtful"
            lost_recovery_reason = "Severe malefic affliction to the 2nd house and its lord indicates permanent loss or high resistance to retrieval (Ch II Stanza 25)."
        else:
            lost_recovery_verdict = "MAYBE — Slow / Difficult recovery"
            lost_recovery_reason = "No clear recovery yoga exists, but the 2nd house is not severely damaged. Recovery depends on active search."
    else:
        lost_recovery_verdict = "YES — Recovery Promised"

    # 6. Family & Speech Outcomes (Ch II Stanza 27-28)
    if occ_2nd_benefics or asp_2nd_benefics:
        family_speech_desc = "Harmony & Pleasant Speech. Benefic aspects to the 2nd house ensure sweet speech, pleasant discussions, and mutual understanding in the family (Ch II Stanza 27)."
    elif occ_2nd_malefics or asp_2nd_malefics:
        family_speech_desc = "Friction & Dispute. Malefic influences on the 2nd house can cause harsh language, misunderstandings, and argument loops within the household (Ch II Stanza 28)."
    else:
        family_speech_desc = "Neutral/Stable domestic relations."

    # 7. Financial Timing of Gains
    lagna_quality = SIGN_QUALITIES[lagna_sign]
    second_lord_quality = SIGN_QUALITIES[get_sign(second_lord_lon)]
    
    if lagna_quality == "Movable":
        time_unit = "Days/Weeks"
        timing_quality_desc = "Rapid fructification of wealth/gains (Movable Ascendant)."
    elif lagna_quality == "Common":
        time_unit = "Weeks/Months"
        timing_quality_desc = "Moderate timing or sequential progression of gains (Common Ascendant)."
    else:
        time_unit = "Months/Years"
        timing_quality_desc = "Delayed gains or slow accumulation of long-term investments (Fixed Ascendant)."
        
    timing_desc = "Timing undetermined (No direct applying aspect between significators)"
    
    # Calculate degree difference for timing if there is an applying relationship
    active_rel = None
    if rel_1_2 and rel_1_2["is_applying"]:
        active_rel = (rel_1_2, second_lord)
    elif rel_1_11 and rel_1_11["is_applying"]:
        active_rel = (rel_1_11, eleventh_lord)
    elif rel_2_11 and rel_2_11["is_applying"]:
        active_rel = (rel_2_11, eleventh_lord)
        
    if active_rel:
        rel_obj, lord_name = active_rel
        deg_diff = rel_obj["orb_diff"]
        time_val = round(deg_diff)
        if time_val == 0:
            time_val = 1
        timing_desc = f"Financial gains/outcome expected in approx. {time_val} {time_unit} (based on degrees difference of {deg_diff:.1f}° with {lord_name})."
        
    # Final verdict
    if wealth_promised and not (combust_2nd or combust_11th):
        verdict = "YES — High Financial Prosperity"
        reason = " | ".join(wealth_conditions)
    else:
        # Check if severely afflicted
        if combust_2nd or combust_11th:
            verdict = "NO — Financial Pressures / Impediments"
            reason = f"Significators are weak/combust (combust_2nd={combust_2nd}, combust_11th={combust_11th}), indicating financial blocks."
        else:
            verdict = "MAYBE — Moderate Gains / Obstacles"
            reason = "No direct wealth yogas detected. Financial improvements will be slow and require significant personal effort."
            
    return {
        "verdict": verdict,
        "reason": reason,
        "accumulated_wealth_status": acc_wealth_status,
        "incoming_gains_status": gains_status,
        "lost_wealth_recovery_verdict": lost_recovery_verdict,
        "lost_wealth_recovery_reason": lost_recovery_reason,
        "family_speech_influence": family_speech_desc,
        "timing_desc": timing_desc,
        "timing_quality_desc": timing_quality_desc,
        "second_lord_avastha": second_lord_avastha,
        "second_lord_strength": second_lord_strength,
        "eleventh_lord_avastha": eleventh_lord_avastha,
        "eleventh_lord_strength": eleventh_lord_strength
    }
