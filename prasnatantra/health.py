# health.py
# Dedicated health, illness & recovery query evaluator based on Prasna Tantra Chapter III, Stanzas 15-26

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

# Bodily System Significations (Stanzas 18-19)
DISEASE_SIGNIFICATIONS = {
    "Sun": "Fever, cardiac strains, vision issues, inflammatory heat-related symptoms, or vitality exhaustion.",
    "Moon": "Fluid retention (edema), cold/phlegmatic disorders, mental anxiety/stress, or sleep disturbances.",
    "Mars": "Blood disorders, injuries/cuts, surgical intervention, high fevers, burns, or acute infections.",
    "Mercury": "Nervous exhaustion, skin ailments/allergies, speech/memory issues, or respiratory strain.",
    "Jupiter": "Diabetes, liver/gallbladder imbalances, metabolic issues, or digestive blockages.",
    "Venus": "Hormonal imbalances, reproductive or kidney/urinary tract complaints, or glandular issues.",
    "Saturn": "Chronic joint pain/arthritis, paralysis, long-term blockages, bone weakness, or physical exhaustion.",
    "Rahu": "Mysterious toxicities, food poisoning, psychological disturbances, rare infections, or misdiagnosis risk.",
    "Ketu": "Sudden mysterious ailments, phantom pains, nerve shocks, or difficult-to-diagnose symptoms."
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

def evaluate_health_query(chart):
    """
    Evaluates health status, disease recovery, diagnosis of illness, hospitalization risk, 
    and timing of recovery using Prasna Tantra rules (Chapter III, Stanzas 15-26).
    """
    lagna_sign = chart.lagna_sign
    lagna_lon = chart.lagna_sidereal
    lagnapathi = SIGN_LORDS[lagna_sign]
    lagnapathi_lon = chart.planets[lagnapathi]["longitude"]
    
    # 6th House (Disease)
    sixth_sign = (lagna_sign + 5) % 12
    sixth_lord = SIGN_LORDS[sixth_sign]
    sixth_lord_lon = chart.planets[sixth_lord]["longitude"]
    
    # 8th House (Danger / Chronicity)
    eighth_sign = (lagna_sign + 7) % 12
    eighth_lord = SIGN_LORDS[eighth_sign]
    eighth_lord_lon = chart.planets[eighth_lord]["longitude"]
    
    # 12th House (Hospitalization)
    twelfth_sign = (lagna_sign + 11) % 12
    twelfth_lord = SIGN_LORDS[twelfth_sign]
    twelfth_lord_lon = chart.planets[twelfth_lord]["longitude"]
    
    # Sun and Moon longitudes
    sun_lon = chart.planets["Sun"]["longitude"]
    moon_lon = chart.planets["Moon"]["longitude"]
    moon_sign = get_sign(moon_lon)
    
    # 1. Vitality Assessment (Stanza 15)
    lagna_lord_data = chart.planets[lagnapathi]
    lagna_lord_strength = get_planet_score(lagnapathi, lagnapathi_lon)
    lagna_lord_avastha = get_planetary_avastha(lagnapathi, lagnapathi_lon, lagna_lord_data, sun_lon, chart.planets)
    
    moon_data = chart.planets["Moon"]
    moon_avastha = get_planetary_avastha("Moon", moon_lon, moon_data, sun_lon, chart.planets)
    moon_combust = check_combustion("Moon", moon_lon, sun_lon)
    
    # Check malefic aspects on Moon
    moon_malefic_aspects = []
    for m in ["Mars", "Saturn", "Rahu", "Ketu"]:
        if m in chart.planets:
            m_lon = chart.planets[m]["longitude"]
            if get_sign(m_lon) == moon_sign or aspects_sign(m_lon, moon_sign):
                moon_malefic_aspects.append(m)
                
    moon_afflicted = moon_combust or len(moon_malefic_aspects) >= 2
    
    vitality_score = 0
    if lagna_lord_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"]:
        vitality_score += 40
    if moon_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"] and not moon_afflicted:
        vitality_score += 40
    if not check_combustion(lagnapathi, lagnapathi_lon, sun_lon):
        vitality_score += 20
        
    if vitality_score >= 80:
        vitality_rating = "Excellent / High Vitality"
    elif vitality_score >= 50:
        vitality_rating = "Moderate / Stable Vitality"
    else:
        vitality_rating = "Weak / Compromised Vitality"

    # 2. Disease Severity Assessment (Stanza 16, 23)
    # Check occupants/aspects of 6th, 8th, 12th houses
    def analyze_house_influence(h_sign, h_lord=None):
        benefics = []
        malefics = []
        for p, p_data in chart.planets.items():
            p_s = get_sign(p_data["longitude"])
            is_ben = p in ["Jupiter", "Venus", "Mercury", "Moon"]
            if p == "Mercury" and check_combustion("Mercury", p_data["longitude"], sun_lon):
                is_ben = False
                
            if p_s == h_sign or aspects_sign(p_data["longitude"], h_sign):
                if is_ben:
                    benefics.append(p)
                else:
                    if p != h_lord:
                        malefics.append(p)
        return benefics, malefics

    ben_6th, mal_6th = analyze_house_influence(sixth_sign, sixth_lord)
    ben_8th, mal_8th = analyze_house_influence(eighth_sign, eighth_lord)
    ben_12th, mal_12th = analyze_house_influence(twelfth_sign, twelfth_lord)

    # 6th lord avastha
    sixth_lord_data = chart.planets[sixth_lord]
    sixth_lord_avastha = get_planetary_avastha(sixth_lord, sixth_lord_lon, sixth_lord_data, sun_lon, chart.planets)
    
    is_6th_afflicted = len(mal_6th) >= 2 or sixth_lord_avastha in ["Deena", "Mushita", "Nipeeditha"]
    is_8th_afflicted = len(mal_8th) >= 2 or eighth_lord in ["Mars", "Saturn"]
    is_12th_afflicted = len(mal_12th) >= 2
    
    # Severity Verdict
    if (is_6th_afflicted or is_8th_afflicted or len(mal_6th) >= 1) and (vitality_rating == "Weak / Compromised Vitality"):
        severity_level = "Severe / Dangerous Ailment"
    elif is_6th_afflicted or is_8th_afflicted:
        severity_level = "Moderate / Ailment with setbacks"
    else:
        severity_level = "Mild / Manageable illness"
        
    # Hospitalization Risk (Stanza 23)
    # Check if 6th, 8th and 12th house/lords are heavily tied with malefics
    hospitalization_score = 0
    if len(mal_12th) >= 1:
        hospitalization_score += 30
    if twelfth_sign == get_sign(sixth_lord_lon) or twelfth_sign == get_sign(eighth_lord_lon):
        hospitalization_score += 40
    if check_combustion(lagnapathi, lagnapathi_lon, sun_lon):
        hospitalization_score += 30
        
    if hospitalization_score >= 70:
        hosp_risk = "High Risk of Confinement / Hospitalization"
    elif hospitalization_score >= 40:
        hosp_risk = "Medium Risk / Short Clinic Stay"
    else:
        hosp_risk = "Low Risk / Home Rest"

    # 3. Diagnosis & Bodily System affected (Stanzas 18-19)
    # Determine the primary planetary significator of disease:
    # 1. Planets occupying/aspecting 6th house
    # 2. 6th Lord itself
    # Choose the most malefic planet or 6th lord itself
    primary_diseasing_planet = sixth_lord
    malefics_influencing_6th = [m for m in ["Saturn", "Mars", "Rahu", "Ketu", "Sun"] if m in mal_6th]
    if malefics_influencing_6th:
        primary_diseasing_planet = malefics_influencing_6th[0] # Prefer most malefic
    elif len(ben_6th) > 0:
        primary_diseasing_planet = ben_6th[0]
        
    disease_nature = DISEASE_SIGNIFICATIONS.get(primary_diseasing_planet, "General physical fatigue and minor organic strain.")

    # 4. Recovery Promised conditions (Stanza 15, 17, 20-22, 24-25)
    recovery_promised = False
    recovery_reasons = []
    
    # Stanza 15/20: Strong Lagna, Lagna Lord and Moon with benefic aspects
    benefics_aspecting_lagna = [b for b in ["Jupiter", "Venus", "Mercury"] if b in analyze_house_influence(lagna_sign)[0]]
    if (vitality_rating in ["Excellent / High Vitality", "Moderate / Stable Vitality"]) and benefics_aspecting_lagna:
        if not check_combustion(lagnapathi, lagnapathi_lon, sun_lon):
            recovery_promised = True
            recovery_reasons.append("Ascendant and Moon are strong with benefic aspects, indicating swift recovery (Stanza 15/20)")
        
    # Stanza 21: 6th lord is weak while Lagna lord is strong
    sixth_lord_weak = sixth_lord_avastha in ["Deena", "Mushita", "Nipeeditha", "Suptha"]
    lagna_lord_strong = lagna_lord_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"]
    if sixth_lord_weak and lagna_lord_strong:
        recovery_promised = True
        recovery_reasons.append("Lagna Lord is strong while the 6th Lord (disease significator) is weak, indicating disease is diminishing (Stanza 21)")
        
    # Stanza 25: Lagna Lord in applying aspect with benefics
    for b in ["Jupiter", "Venus"]:
        rel_1_b = get_planet_relationship(lagnapathi, lagna_lord_data, b, chart.planets[b])
        if rel_1_b and rel_1_b["is_applying"] and rel_1_b["is_friendly"]:
            if not check_combustion(lagnapathi, lagnapathi_lon, sun_lon) and not check_combustion(b, chart.planets[b]["longitude"], sun_lon):
                recovery_promised = True
                recovery_reasons.append(f"Lagna Lord ({lagnapathi}) is in friendly applying aspect (Ithasala) with benefic {b} (Stanza 25)")
            
    # Stanza 17: Benefics occupy/aspect 6th house
    if len(ben_6th) >= 2:
        if not check_combustion(lagnapathi, lagnapathi_lon, sun_lon):
            recovery_promised = True
            recovery_reasons.append("Benefics occupy or aspect the 6th house, providing relief and cure (Stanza 17)")

    # 5. Timing of Recovery (Stanza 26)
    lagna_quality = SIGN_QUALITIES[lagna_sign]
    if lagna_quality == "Movable":
        recovery_speed = "Quick recovery expected."
        time_unit = "Days/Weeks"
    elif lagna_quality == "Common":
        recovery_speed = "Moderate recovery speed, with possible variable symptoms."
        time_unit = "Weeks/Months"
    else:
        recovery_speed = "Prolonged recovery/chronic ailment requiring patience."
        time_unit = "Months/Years"
        
    timing_desc = "Recovery timing undetermined."
    
    # Calculate degree gap between Lagna Lord and nearest benefic/Moon for timing
    closest_ben = None
    min_gap = 360.0
    for b in ["Jupiter", "Venus", "Moon"]:
        rel = get_planet_relationship(lagnapathi, lagna_lord_data, b, chart.planets[b])
        if rel and rel["is_applying"] and rel["orb_diff"] < min_gap:
            min_gap = rel["orb_diff"]
            closest_ben = b
            
    if closest_ben and min_gap < 360.0:
        time_val = round(min_gap)
        if time_val == 0:
            time_val = 1
        timing_desc = f"Recovery/Relief expected in approx. {time_val} {time_unit} (based on degrees difference of {min_gap:.1f}° with {closest_ben} under {lagna_quality} Lagna)."

    # Final Verdict
    if recovery_promised:
        verdict = "YES — Recovery Promised"
        reason = " | ".join(recovery_reasons)
    else:
        # Check if severely danger
        if severity_level == "Severe / Dangerous Ailment" or is_8th_afflicted:
            verdict = "NO / CHRONIC — High Obstacles / Slow recovery"
            reason = "Significators are severely afflicted, 8th lord dominates, and vitality is low. Consult physician immediately."
        else:
            verdict = "MAYBE — Slow recovery with obstacles"
            reason = "No clean recovery yogas. Vitality is moderate; treatment will yield results gradually over time."
            
    # Remedial Advice
    remedial_map = {
        "Sun": "Practice breathing exercises (Pranayama) and solar meditation. Stay hydrated and avoid excess heat.",
        "Moon": "Maintain strict fluid/sleep schedule, practice emotional grounding, and avoid damp environments.",
        "Mars": "Take rest, prevent physical exertion, avoid heat, and consume soothing, anti-inflammatory food.",
        "Mercury": "Practice mental rest, reduce screen time, avoid anxious overthinking, and consume warm herbal tea.",
        "Jupiter": "Follow dietary adjustments to regulate sugar/liver health. Avoid rich, sweet, or heavy foods.",
        "Venus": "Maintain urinary hygiene, hormonal wellness, and stay hydrated with soothing juices.",
        "Saturn": "Seek chronic joint care, gentle stretching, keep joints warm, and ensure absolute rest.",
        "Rahu": "Seek a secondary medical opinion to avoid misdiagnosis, and eliminate toxic food/environments.",
        "Ketu": "Practice spiritual grounding, keep warm, and seek specific medical diagnoses for nerve discomfort."
    }
    remedial_advice = remedial_map.get(primary_diseasing_planet, "Follow medical instructions, ensure absolute rest, and maintain general wellness.")

    return {
        "verdict": verdict,
        "reason": reason,
        "disease_nature": disease_nature,
        "disease_significator": primary_diseasing_planet,
        "vitality_status": vitality_rating,
        "severity_level": severity_level,
        "hospitalization_risk": hosp_risk,
        "recovery_timing": recovery_speed,
        "timing_desc": timing_desc,
        "remedial_advice": remedial_advice,
        "lagna_lord_avastha": lagna_lord_avastha,
        "sixth_lord_avastha": sixth_lord_avastha,
        "is_moon_afflicted": moon_afflicted
    }
