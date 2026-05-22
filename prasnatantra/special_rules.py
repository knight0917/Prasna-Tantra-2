from .tajaka import get_planet_relationship, get_planetary_avastha, check_combustion, detect_kamboola_yoga
from .astronomy import get_sign_name


SIGN_LORDS = {
    0: "Mars",      # Aries
    1: "Venus",     # Taurus
    2: "Mercury",   # Gemini
    3: "Moon",      # Cancer
    4: "Sun",       # Leo
    5: "Mercury",   # Virgo
    6: "Venus",     # Libra
    7: "Mars",      # Scorpio
    8: "Jupiter",   # Sagittarius
    9: "Saturn",    # Capricorn
    10: "Saturn",   # Aquarius
    11: "Jupiter"   # Pisces
}

def get_sign(lon):
    return int(lon / 30.0) % 12

def aspects_sign(planet_lon, target_sign):
    p_sign = get_sign(planet_lon)
    diff = (target_sign - p_sign) % 12
    # Tajaka aspects: conjunction (0), sextile (3, 11), square (4, 10), trine (5, 9), opposition (7)
    # Vedic aspects (or general sight): 1st, 3rd, 4th, 5th, 7th, 9th, 10th, 11th
    # So aspecting signs are 0, 2, 3, 4, 6, 8, 9, 10 (0-indexed offset: 2 is 3rd, 3 is 4th, 4 is 5th, 6 is 7th, etc.)
    return diff in [0, 2, 3, 4, 6, 8, 9, 10]

def evaluate_deity_curse(chart):
    """
    Evaluates the curse of deities (Stanzas 105-110)
    Based on planets occupying or afflicting the 12th house (loss/misfortune) or Lagna Lord.
    """
    lagna_sign = chart.lagna_sign
    twelfth_sign = (lagna_sign + 11) % 12
    lagnapathi = chart.lagnapathi
    
    curse_mappings = {
        "Sun": "Curse of Lord Shiva, or anger/dissatisfaction of father.",
        "Moon": "Curse of Goddess Durga (or Ganga), or anger of mother.",
        "Mars": "Curse of Lord Kartikeya (Subrahmanya), or sibling/blood-line disputes.",
        "Mercury": "Curse of Lord Vishnu, or maternal uncle/friend disputes.",
        "Jupiter": "Anger of spiritual preceptors (Guru), Brahmins, or curse of Rishis.",
        "Venus": "Curse of Goddess Yakshini or Lakshmi, or anger of wife/women.",
        "Saturn": "Curse of Lord Yama, ghosts/evil spirits (Pishachas), or servants/low-born.",
        "Rahu": "Curse of serpent deities (Nagas) or ancestors (Pitrus).",
        "Ketu": "Curse of Lord Ganesha or ancestral spirits."
    }
    
    predictions = []
    details = []
    score_adj = 0
    
    # 1. Check occupants of 12th house
    occ_12 = []
    for p, p_data in chart.planets.items():
        if get_sign(p_data["longitude"]) == twelfth_sign:
            occ_12.append(p)
            
    if occ_12:
        for p in occ_12:
            curse = curse_mappings.get(p, "General ancestral distress.")
            predictions.append({
                "category": "Deity Curse",
                "prediction": f"Indicator in 12th House: {p}. Cause: {curse}",
                "rule": f"Prasna Tantra Ch 3 St. 105 (Occupation of 12th by {p})"
            })
            details.append(f"Deity Curse: {p} in 12th house points to '{curse}'")
            score_adj -= 10
            
    # 2. Check afflicting planets of Lagna Lord (conjoining or hostile aspect)
    for p, p_data in chart.planets.items():
        if p == lagnapathi or p in ["Rahu", "Ketu"]:
            continue
        # Check aspect or conjunction with Lagna Lord
        rel = get_planet_relationship(p, p_data, lagnapathi, chart.planets[lagnapathi])
        if rel and not rel["is_friendly"]:
            curse = curse_mappings.get(p, "General planetary affliction.")
            predictions.append({
                "category": "Deity Curse",
                "prediction": f"Hostile aspect from {p} to Lagna Lord {lagnapathi}. Cause: {curse}",
                "rule": f"Prasna Tantra Ch 3 St. 108 (Hostile aspect on Lagnapathi by {p})"
            })
            details.append(f"Deity Curse: Hostile aspect from {p} to Lagna Lord {lagnapathi} points to '{curse}'")
            score_adj -= 5

    if not predictions:
        predictions.append({
            "category": "Deity Curse",
            "prediction": "No clear indications of deity curses. Misfortune is not due to divine wrath.",
            "rule": "Prasna Tantra Ch 3 St. 105-110"
        })
        details.append("Deity Curse: No significators found in the 12th house or afflicting Lagna Lord.")
        
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def evaluate_master_servant(chart):
    """
    Evaluates master-servant relations, job changes, and career stability
    based on Sri Neelakanta's Prasna Tantra Chapter III (Stanzas 56-61, 68-75).
    Lagna = Employee/Servant. 10th house = Employer/Master/Job.
    """
    lagna_sign = chart.lagna_sign
    lagnapathi = chart.lagnapathi
    tenth_lord = SIGN_LORDS[(lagna_sign + 9) % 12]
    
    sixth_lord = SIGN_LORDS[(lagna_sign + 5) % 12]
    twelfth_lord = SIGN_LORDS[(lagna_sign + 11) % 12]
    third_lord = SIGN_LORDS[(lagna_sign + 2) % 12]
    ninth_lord = SIGN_LORDS[(lagna_sign + 8) % 12]
    seventh_lord = SIGN_LORDS[(lagna_sign + 6) % 12]
    
    # Sign classifications: 0=Movable (Aries, Cancer, Libra, Capricorn), 1=Fixed (Taurus, Leo, Scorpio, Aquarius), 2=Common (Gemini, Virgo, Sagittarius, Pisces)
    chara_map = {
        0: [0, 3, 6, 9],    # Movable
        1: [1, 4, 7, 10],   # Fixed
        2: [2, 5, 8, 11]    # Common
    }
    
    def get_mobility(sign_idx):
        if sign_idx in chara_map[0]:
            return "Movable"
        elif sign_idx in chara_map[1]:
            return "Fixed"
        else:
            return "Common"
            
    lagna_mobility = get_mobility(lagna_sign)
    lagnapathi_sign = get_sign(chart.planets[lagnapathi]["longitude"])
    lagnapathi_mobility = get_mobility(lagnapathi_sign)
    
    lagnapathi_house = ((lagnapathi_sign - lagna_sign) % 12) + 1
    tenth_lord_sign = get_sign(chart.planets[tenth_lord]["longitude"])
    tenth_lord_house = ((tenth_lord_sign - lagna_sign) % 12) + 1
    
    predictions = []
    details = []
    score_adj = 0
    
    # 1. Sign Mobility Base Rules (Stanzas 111-112)
    if lagna_mobility == "Fixed" and lagnapathi_mobility == "Fixed":
        predictions.append({
            "category": "Employment Stability",
            "prediction": "The employee/servant will remain with the current master/job. Favorable stability.",
            "rule": "Prasna Tantra Ch 3 St. 111 (Fixed Lagna & Lord)"
        })
        details.append("Master-Servant: Both Lagna and Lagna Lord are in Fixed signs (indicating staying).")
        score_adj += 15
    elif lagna_mobility == "Movable" or lagnapathi_mobility == "Movable":
        predictions.append({
            "category": "Employment Stability",
            "prediction": "The employee/servant will change jobs or leave the current master/employer soon.",
            "rule": "Prasna Tantra Ch 3 St. 112 (Movable Lagna or Lord)"
        })
        details.append("Master-Servant: Lagna or Lagna Lord is in a Movable sign (indicating shifting).")
        score_adj -= 10
    else:
        predictions.append({
            "category": "Employment Stability",
            "prediction": "Mixed results. Employee will stay for now but will eventually change after some delay.",
            "rule": "Prasna Tantra Ch 3 St. 111-112 (Common sign influence)"
        })
        details.append("Master-Servant: Lagna/Lagna Lord under Common sign influence (mixed/delayed change).")
        
    # 2. Employer-Employee Relations Aspect Rules
    rel = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], tenth_lord, chart.planets[tenth_lord])
    if rel:
        if rel["is_friendly"]:
            details.append(f"Master-Servant: Friendly aspect ({rel['aspect_type']}) between employee lord ({lagnapathi}) and employer lord ({tenth_lord}) indicates harmony.")
            score_adj += 10
        else:
            details.append(f"Master-Servant: Hostile aspect ({rel['aspect_type']}) between employee lord ({lagnapathi}) and employer lord ({tenth_lord}) indicating friction.")
            score_adj -= 10
    else:
        details.append(f"Master-Servant: No aspect between employee lord ({lagnapathi}) and employer lord ({tenth_lord}).")

    # 3. Classical Job Change & Stability (Stanzas 56-58 & 72)
    rel_6 = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], sixth_lord, chart.planets[sixth_lord])
    rel_12 = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], twelfth_lord, chart.planets[twelfth_lord])
    
    in_kendra = lagnapathi_house in [1, 4, 7, 10]
    has_rel_6_12 = (rel_6 and rel_6["is_applying"]) or (rel_12 and rel_12["is_applying"])
    
    if in_kendra and has_rel_6_12:
        predictions.append({
            "category": "Job Change Forecast",
            "prediction": f"Querent will benefit from changing to a new master/employer. Change of service is indicated.",
            "rule": "Prasna Tantra Ch 3 St. 72 (Lagna Lord in Kendra having Ithasala with 6th/12th Lord)"
        })
        details.append(f"Job Change: Lagna Lord ({lagnapathi}) is in Kendra and has Ithasala with 6th/12th Lord.")
        if lagnapathi_mobility == "Movable":
            details.append("Job Change: Lagna Lord in Movable sign indicates change of city/location also.")
        score_adj += 15
    elif in_kendra and not has_rel_6_12:
        predictions.append({
            "category": "Job Change Forecast",
            "prediction": "No change of service/master is recommended. Staying with the current employer is beneficial.",
            "rule": "Prasna Tantra Ch 3 St. 56-58 (Lagna Lord in Kendra with no Ithasala with 6th/12th Lord)"
        })
        details.append("Job Change: Lagna Lord in Kendra has no Ithasala with 6th or 12th Lord (staying advised).")
        score_adj += 10

    # Retrograde and 3rd/9th house change (Stanzas 56-58 Notes)
    lagnapathi_retro = chart.planets[lagnapathi]["speed"] < 0
    rel_3 = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], third_lord, chart.planets[third_lord])
    rel_9 = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], ninth_lord, chart.planets[ninth_lord])
    has_rel_3_9 = (rel_3 and rel_3["is_applying"]) or (rel_9 and rel_9["is_applying"])
    
    if lagnapathi_retro and has_rel_3_9:
        predictions.append({
            "category": "Job Change Forecast",
            "prediction": "Querent will change over to a new master/position due to retrograde lord aspecting change houses.",
            "rule": "Prasna Tantra Ch 3 St. 56-58 Notes (Retrograde Lagna Lord with Ithasala to 3rd/9th Lord)"
        })
        details.append("Job Change: Retrograde Lagna Lord has Ithasala with 3rd or 9th Lord (indicating position change).")
        score_adj += 10

    # 4. Improvement in present job (Stanza 73)
    exalt_signs = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
    own_signs = {"Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5], "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]}
    
    is_own_exalted = (lagnapathi_sign in own_signs.get(lagnapathi, []) or lagnapathi_sign == exalt_signs.get(lagnapathi))
    rel_moon = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], "Moon", chart.planets["Moon"])
    
    if in_kendra and is_own_exalted and rel_moon and rel_moon["is_applying"]:
        predictions.append({
            "category": "Current Job Promotion",
            "prediction": "The querent will secure improvement, raises, or promotion in the present job itself.",
            "rule": "Prasna Tantra Ch 3 St. 73 (Lagna Lord in Kendra, own/exalted, in Ithasala with Moon)"
        })
        details.append("Job Promotion: Lagna Lord in Kendra (own/exalted sign) has Ithasala with Moon.")
        score_adj += 20

    # 5. Benefit under new employer (Stanza 74)
    seventh_lord_sign = get_sign(chart.planets[seventh_lord]["longitude"])
    seventh_lord_house = ((seventh_lord_sign - lagna_sign) % 12) + 1
    seventh_in_kendra = seventh_lord_house in [1, 4, 7, 10]
    seventh_own_exalted = (seventh_lord_sign in own_signs.get(seventh_lord, []) or seventh_lord_sign == exalt_signs.get(seventh_lord))
    rel_moon_7 = get_planet_relationship(seventh_lord, chart.planets[seventh_lord], "Moon", chart.planets["Moon"])
    
    if seventh_in_kendra and seventh_own_exalted and rel_moon_7 and rel_moon_7["is_applying"]:
        predictions.append({
            "category": "New Job Prospects",
            "prediction": "The querent will benefit immensely under a new employer (7th house represents next master).",
            "rule": "Prasna Tantra Ch 3 St. 74 (7th Lord in Kendra, own/exalted, in Ithasala with Moon)"
        })
        details.append("New Employer: 7th Lord in Kendra (own/exalted sign) has Ithasala with Moon.")
        score_adj += 20

    # 6. Cordial relations (Stanza 68 & 71)
    sirshodaya_signs = [2, 4, 5, 6, 7, 10]
    is_sirshodaya = lagna_sign in sirshodaya_signs
    
    benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
    # Check if any benefic occupies Lagna
    benefics_in_lagna = []
    for b in benefics:
        if b in chart.planets and get_sign(chart.planets[b]["longitude"]) == lagna_sign:
            benefics_in_lagna.append(b)
            
    if is_sirshodaya and benefics_in_lagna:
        details.append(f"Relations: Sirshodaya Lagna occupied by benefics ({', '.join(benefics_in_lagna)}) indicates cordial employer relations (Stanza 68).")
        score_adj += 10

    # Stanza 71: Moon & Benefics aspect/occupy Lagna and 7th
    moon_sign = get_sign(chart.planets["Moon"]["longitude"])
    moon_in_1_7 = moon_sign in [lagna_sign, (lagna_sign + 6) % 12]
    benefics_in_1_7 = any(get_sign(chart.planets[b]["longitude"]) in [lagna_sign, (lagna_sign + 6) % 12] for b in ["Jupiter", "Venus", "Mercury"])
    
    if moon_in_1_7 and benefics_in_1_7:
        predictions.append({
            "category": "Employer Goodwill",
            "prediction": "The employer will treat the querent with special kindness, goodwill, and friendliness.",
            "rule": "Prasna Tantra Ch 3 St. 71 (Moon and benefics occupying/aspecting Lagna/7th)"
        })
        details.append("Goodwill: Moon and benefics in Lagna/7th houses.")
        score_adj += 15

    # 7. Malefic afflictions (Stanzas 69-70)
    malefics = ["Sun", "Mars", "Saturn"]
    for m in malefics:
        m_sign = get_sign(chart.planets[m]["longitude"])
        m_house = ((m_sign - lagna_sign) % 12) + 1
        if m_house == 1:
            predictions.append({
                "category": "Employment Affliction",
                "prediction": f"Risk of loss of money at the hands of the employer due to malefic ({m}) in Lagna.",
                "rule": "Prasna Tantra Ch 3 St. 69"
            })
            details.append(f"Affliction: Malefic {m} in Lagna (Financial risk from employer).")
            score_adj -= 10
        elif m_house == 2:
            predictions.append({
                "category": "Employment Affliction",
                "prediction": f"Risk of mental distress/affliction from employer due to malefic ({m}) in 2nd house.",
                "rule": "Prasna Tantra Ch 3 St. 69"
            })
            details.append(f"Affliction: Malefic {m} in 2nd house (Mental distress/tension).")
            score_adj -= 10
        elif m_house == 7:
            predictions.append({
                "category": "Employment Affliction",
                "prediction": f"Friction and severe difficulties at work due to malefic ({m}) in 7th house.",
                "rule": "Prasna Tantra Ch 3 St. 69"
            })
            details.append(f"Affliction: Malefic {m} in 7th house (Interpersonal friction).")
            score_adj -= 10
        elif m_house == 8:
            predictions.append({
                "category": "Employment Affliction",
                "prediction": f"Severe professional setback or termination due to malefic ({m}) in 8th house.",
                "rule": "Prasna Tantra Ch 3 St. 69"
            })
            details.append(f"Affliction: Malefic {m} in 8th house (Severe setback risk).")
            score_adj -= 15

    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def evaluate_meals(chart):
    """
    Evaluates what taste/food the querent will receive (Stanzas 148-154)
    Based on elements of Lagna and Moon sign.
    """
    lagna_sign = chart.lagna_sign
    moon_lon = chart.planets["Moon"]["longitude"]
    moon_sign = get_sign(moon_lon)
    
    # 0, 4, 8 = Fire (Bitter/Pungent), 1, 5, 9 = Earth (Sweet/Solid grains), 2, 6, 10 = Air (Liquid/Sour), 3, 7, 11 = Water (Juicy/Salty/Milk)
    def get_element_food(sign_idx):
        if sign_idx in [0, 4, 8]:
            return "Fire", "Bitter/pungent taste, baked dishes, or hot food."
        elif sign_idx in [1, 5, 9]:
            return "Earth", "Sweet taste (madhura), solid grains, rice, wheat, or hearty food."
        elif sign_idx in [2, 6, 10]:
            return "Air", "Liquid/soup-like food, warm beverages, or sour taste (amla)."
        else:
            return "Water", "Juicy fruits, milk products, sweet pudding (payasam), or salty items."
            
    lagna_el, lagna_food = get_element_food(lagna_sign)
    moon_el, moon_food = get_element_food(moon_sign)
    
    predictions = []
    details = []
    score_adj = 0
    
    # Check benefic aspect on Lagna/Moon (Rich meal)
    benefics = ["Jupiter", "Venus"]
    sun_lon = chart.planets["Sun"]["longitude"]
    if not check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
        benefics.append("Mercury")
        
    benefic_aspect = False
    for b in benefics:
        if aspects_sign(chart.planets[b]["longitude"], lagna_sign) or aspects_sign(chart.planets[b]["longitude"], moon_sign):
            benefic_aspect = True
            break
            
    # Check malefic aspect
    malefics = ["Sun", "Mars", "Saturn"]
    malefic_aspect = False
    for m in malefics:
        if aspects_sign(chart.planets[m]["longitude"], lagna_sign) or aspects_sign(chart.planets[m]["longitude"], moon_sign):
            malefic_aspect = True
            break
            
    meal_nature = "Simple/Standard meal."
    if benefic_aspect and not malefic_aspect:
        meal_nature = "Rich, delicious, fresh, and abundant meal."
        score_adj += 15
        details.append("Meals: Benefics aspect Lagna/Moon (Excellent quality food).")
    elif malefic_aspect:
        meal_nature = "Dry, simple, stale food, or the meal may be delayed/missed."
        score_adj -= 10
        details.append("Meals: Malefics aspect Lagna/Moon (Dry/delayed food).")
        
    predictions.append({
        "category": "Dietary/Meals Query",
        "prediction": f"Lagna Sign ({lagna_el} element) indicates: {lagna_food} Moon Sign ({moon_el} element) indicates: {moon_food} Overall Quality: {meal_nature}",
        "rule": "Prasna Tantra Ch 3 St. 148-154"
    })
    
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def evaluate_sports(chart):
    """
    Evaluates sports/games outcomes (Stanzas 157-158)
    Lagna/Lord = Querent/Home Team. 7th house/Lord = Opponent/Away Team.
    """
    lagna_sign = chart.lagna_sign
    lagnapathi = chart.lagnapathi
    seventh_sign = (lagna_sign + 6) % 12
    seventh_lord = SIGN_LORDS[seventh_sign]
    
    l_lord_data = chart.planets[lagnapathi]
    s_lord_data = chart.planets[seventh_lord]
    sun_lon = chart.planets["Sun"]["longitude"]
    
    lagnapathi_avastha = get_planetary_avastha(lagnapathi, l_lord_data["longitude"], l_lord_data, sun_lon, chart.planets)
    seventh_lord_avastha = get_planetary_avastha(seventh_lord, s_lord_data["longitude"], s_lord_data, sun_lon, chart.planets)
    
    avastha_vals = {
        "Deeptha": 10, "Athiveerya": 9, "Suveerya": 8, "Swastha": 7, "Muditha": 6,
        "Neutral": 5, "Pariheena": 4, "Suptha": 3, "Nipeeditha": 2, "Deena": 1, "Mushita": 0
    }
    
    l_strength = avastha_vals.get(lagnapathi_avastha, 5)
    s_strength = avastha_vals.get(seventh_lord_avastha, 5)
    
    # Check occupants of 1st vs 7th
    occ_1 = []
    occ_7 = []
    for p, p_data in chart.planets.items():
        if p in ["Rahu", "Ketu"]:
            continue
        p_sign = get_sign(p_data["longitude"])
        if p_sign == lagna_sign:
            occ_1.append(p)
        elif p_sign == seventh_sign:
            occ_7.append(p)
            
    # Add strengths based on occupants
    for p in occ_1:
        if p in ["Jupiter", "Venus", "Moon", "Mercury"]:
            l_strength += 2
        else:
            l_strength -= 1
            
    for p in occ_7:
        if p in ["Jupiter", "Venus", "Moon", "Mercury"]:
            s_strength += 2
        else:
            s_strength -= 1
            
    predictions = []
    details = []
    score_adj = 0
    
    if l_strength > s_strength:
        predictions.append({
            "category": "Contest Outcome",
            "prediction": "The Querent (Home Team) is highly likely to win. Favorable strengths.",
            "rule": "Prasna Tantra Ch 3 St. 157 (Lagna lord stronger than 7th lord)"
        })
        details.append(f"Sports: Lagna Lord ({lagnapathi}) strength ({l_strength}) exceeds 7th Lord ({seventh_lord}) strength ({s_strength}).")
        score_adj += 20
    elif s_strength > l_strength:
        predictions.append({
            "category": "Contest Outcome",
            "prediction": "The Opponent (Away Team) is likely to win. Unfavorable strengths.",
            "rule": "Prasna Tantra Ch 3 St. 157 (7th lord stronger than Lagna lord)"
        })
        details.append(f"Sports: 7th Lord ({seventh_lord}) strength ({s_strength}) exceeds Lagna Lord ({lagnapathi}) strength ({l_strength}).")
        score_adj -= 20
    else:
        predictions.append({
            "category": "Contest Outcome",
            "prediction": "A closely contested game, potential tie or draw. Strengths are equal.",
            "rule": "Prasna Tantra Ch 3 St. 157-158"
        })
        details.append("Sports: Both Lagna Lord and 7th Lord are of equal strength.")
        
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def evaluate_disputes(chart):
    """
    Evaluates disputes & lawsuits (Stanzas 159-160)
    Lagna = Querent. 7th = Opponent. 10th = Judge. 4th = Final Verdict/Outcome.
    """
    lagna_sign = chart.lagna_sign
    lagnapathi = chart.lagnapathi
    seventh_sign = (lagna_sign + 6) % 12
    seventh_lord = SIGN_LORDS[seventh_sign]
    tenth_sign = (lagna_sign + 9) % 12
    tenth_lord = SIGN_LORDS[tenth_sign]
    fourth_sign = (lagna_sign + 3) % 12
    
    predictions = []
    details = []
    score_adj = 0
    
    # Rule 1: Lagna Lord retrograde or in 12th -> Lose or withdraw
    l_lord_data = chart.planets[lagnapathi]
    if l_lord_data["speed"] < 0:
        predictions.append({
            "category": "Legal Dispute Verdict",
            "prediction": "Querent is likely to withdraw the suit or face setback due to retrograde Lagna Lord.",
            "rule": "Prasna Tantra Ch 3 St. 159 (Lagna Lord retrograde)"
        })
        details.append(f"Disputes: Lagna Lord ({lagnapathi}) is retrograde.")
        score_adj -= 15
        
    l_lord_sign = get_sign(l_lord_data["longitude"])
    if l_lord_sign == (lagna_sign + 11) % 12:
        predictions.append({
            "category": "Legal Dispute Verdict",
            "prediction": "Querent faces defeat or loss as Lagna Lord is in the 12th house (loss).",
            "rule": "Prasna Tantra Ch 3 St. 159 (Lagna Lord in 12th)"
        })
        details.append("Disputes: Lagna Lord is in the 12th house.")
        score_adj -= 20
        
    # Rule 2: Judge aspect (10th lord) on 1st vs 7th lord
    rel_judge_querent = get_planet_relationship(tenth_lord, chart.planets[tenth_lord], lagnapathi, chart.planets[lagnapathi])
    rel_judge_opponent = get_planet_relationship(tenth_lord, chart.planets[tenth_lord], seventh_lord, chart.planets[seventh_lord])
    
    if rel_judge_querent and rel_judge_querent["is_friendly"]:
        details.append("Disputes: Judge (10th Lord) casts a friendly aspect on Querent (Lagna Lord).")
        score_adj += 15
    if rel_judge_opponent and rel_judge_opponent["is_friendly"]:
        details.append("Disputes: Judge (10th Lord) casts a friendly aspect on Opponent (7th Lord).")
        score_adj -= 15
        
    # Rule 3: 4th house (Verdict) occupancy
    occ_4 = []
    for p, p_data in chart.planets.items():
        if p in ["Rahu", "Ketu"]:
            continue
        if get_sign(p_data["longitude"]) == fourth_sign:
            occ_4.append(p)
            
    benefics_in_4 = [p for p in occ_4 if p in ["Jupiter", "Venus", "Moon", "Mercury"]]
    malefics_in_4 = [p for p in occ_4 if p in ["Sun", "Mars", "Saturn"]]
    
    if benefics_in_4:
        predictions.append({
            "category": "Verdict Outcome",
            "prediction": f"Final outcome favors compromise or peaceful settlement (Benefic in 4th: {', '.join(benefics_in_4)}).",
            "rule": "Prasna Tantra Ch 3 St. 160 (Benefic in 4th house)"
        })
        details.append("Disputes: Benefics in the 4th house promote compromise.")
        score_adj += 10
    if malefics_in_4:
        predictions.append({
            "category": "Verdict Outcome",
            "prediction": f"Verdict is hostile and contested (Malefic in 4th: {', '.join(malefics_in_4)}).",
            "rule": "Prasna Tantra Ch 3 St. 160 (Malefic in 4th house)"
        })
        details.append("Disputes: Malefics in the 4th house indicate a harsh final outcome.")
        score_adj -= 10
        
    if not predictions:
        predictions.append({
            "category": "Legal Dispute Verdict",
            "prediction": "A stable proceeding. Outcomes will follow normal legal course, check general house strength.",
            "rule": "Prasna Tantra Ch 3 St. 159-160"
        })
        details.append("Disputes: No direct retrograde or 4th house indicators found.")
        
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def evaluate_crops_trade(chart, house_num):
    """
    Evaluates Crops, Purchase/Sale & Trade (Stanzas 183-191, Ch 4 Sl 41-45)
    If house_num == 4 (Crops), house_num == 2 (Purchase/Sale), house_num == 10 (Trade/Prices).
    """
    lagna_sign = chart.lagna_sign
    lagnapathi = chart.lagnapathi
    
    predictions = []
    details = []
    score_adj = 0
    
    # 1. Purchase/Sale (House 2 / 11)
    if house_num == 2 or house_num == 11:
        # Purchaser = Lagna Lord, Seller = 2nd or 11th Lord
        second_lord = SIGN_LORDS[(lagna_sign + 1) % 12]
        eleventh_lord = SIGN_LORDS[(lagna_sign + 10) % 12]
        
        l_lord_data = chart.planets[lagnapathi]
        sec_lord_data = chart.planets[second_lord]
        sun_lon = chart.planets["Sun"]["longitude"]
        
        l_avastha = get_planetary_avastha(lagnapathi, l_lord_data["longitude"], l_lord_data, sun_lon, chart.planets)
        sec_avastha = get_planetary_avastha(second_lord, sec_lord_data["longitude"], sec_lord_data, sun_lon, chart.planets)
        
        avastha_vals = {
            "Deeptha": 10, "Athiveerya": 9, "Suveerya": 8, "Swastha": 7, "Muditha": 6,
            "Neutral": 5, "Pariheena": 4, "Suptha": 3, "Nipeeditha": 2, "Deena": 1, "Mushita": 0
        }
        
        if avastha_vals.get(l_avastha, 5) > avastha_vals.get(sec_avastha, 5):
            predictions.append({
                "category": "Commercial Transactions",
                "prediction": "Favorable purchase opportunity. The buyer (Lagna Lord) is stronger than the seller (2nd Lord).",
                "rule": "Prasna Tantra Ch 3 St. 183 (Lagna Lord stronger than 2nd Lord)"
            })
            details.append("Trade: Lagna Lord (buyer) is stronger than 2nd Lord (seller) (Favorable purchase).")
            score_adj += 15
        else:
            predictions.append({
                "category": "Commercial Transactions",
                "prediction": "Transaction favors the seller. Exercise caution to avoid overpaying.",
                "rule": "Prasna Tantra Ch 3 St. 183"
            })
            details.append("Trade: 2nd Lord (seller) is stronger than or equal to Lagna Lord (buyer).")
            score_adj -= 5
            
        # Sale opportunity (11th house occupancy)
        occ_11 = []
        for p, p_data in chart.planets.items():
            if p in ["Rahu", "Ketu"]:
                continue
            if get_sign(p_data["longitude"]) == (lagna_sign + 10) % 12:
                occ_11.append(p)
        if any(p in ["Jupiter", "Venus", "Moon"] for p in occ_11):
            predictions.append({
                "category": "Commercial Transactions",
                "prediction": "Excellent sale opportunity. Benefics occupying 11th house indicate profitable gains.",
                "rule": "Prasna Tantra Ch 3 St. 185 (Benefics in 11th house)"
            })
            details.append("Trade: Benefics occupy the 11th house (Excellent selling gains).")
            score_adj += 20
            
    # 2. Crops (House 4)
    elif house_num == 4:
        # Kendras: 1st (East), 4th (North), 7th (West), 10th (South)
        kendra_signs = [lagna_sign, (lagna_sign + 3) % 12, (lagna_sign + 6) % 12, (lagna_sign + 9) % 12]
        kendra_names = {0: "East", 1: "North", 2: "West", 3: "South"}
        
        for k_idx, k_sign in enumerate(kendra_signs):
            occ_k = []
            for p, p_data in chart.planets.items():
                if p in ["Rahu", "Ketu"]:
                    continue
                if get_sign(p_data["longitude"]) == k_sign:
                    occ_k.append(p)
            
            k_dir = kendra_names[k_idx]
            benefics_k = [p for p in occ_k if p in ["Jupiter", "Venus", "Moon"]]
            
            if benefics_k:
                predictions.append({
                    "category": "Agricultural Forecast",
                    "prediction": f"Crops will thrive exceptionally well in the {k_dir} direction due to benefic presence: {', '.join(benefics_k)}.",
                    "rule": f"Prasna Tantra Ch 3 St. 187 (Benefic in Kendra for direction {k_dir})"
                })
                details.append(f"Crops: Benefic in Kendra ({k_dir}) indicates thriving crops.")
                score_adj += 10
                
            if "Saturn" in occ_k:
                predictions.append({
                    "category": "Agricultural Forecast",
                    "prediction": f"Risk of crop failure or famine in the {k_dir} direction due to Saturn affliction.",
                    "rule": f"Prasna Tantra Ch 3 St. 188 (Saturn in Kendra for direction {k_dir})"
                })
                details.append(f"Crops: Saturn in Kendra ({k_dir}) indicates agricultural risk.")
                score_adj -= 15
            if "Sun" in occ_k:
                predictions.append({
                    "category": "Agricultural Forecast",
                    "prediction": f"Risk of crop destruction by governmental authorities or pests in the {k_dir} direction.",
                    "rule": f"Prasna Tantra Ch 3 St. 189 (Sun in Kendra for direction {k_dir})"
                })
                details.append(f"Crops: Sun in Kendra ({k_dir}) indicates loss from state/pests.")
                score_adj -= 10
            if "Mars" in occ_k:
                predictions.append({
                    "category": "Agricultural Forecast",
                    "prediction": f"Risk of crop destruction by fire or locusts in the {k_dir} direction.",
                    "rule": f"Prasna Tantra Ch 3 St. 189 (Mars in Kendra for direction {k_dir})"
                })
                details.append(f"Crops: Mars in Kendra ({k_dir}) indicates fire risk.")
                score_adj -= 12
                
    # 3. Trade and Prices (House 10 / general)
    else:
        # Check quadrants for benefics and Lagna strength
        occ_kendras = []
        kendra_signs = [lagna_sign, (lagna_sign + 3) % 12, (lagna_sign + 6) % 12, (lagna_sign + 9) % 12]
        for k_sign in kendra_signs:
            for p, p_data in chart.planets.items():
                if p in ["Rahu", "Ketu"]:
                    continue
                if get_sign(p_data["longitude"]) == k_sign:
                    occ_kendras.append(p)
                    
        benefics_k = [p for p in occ_kendras if p in ["Jupiter", "Venus", "Moon"]]
        malefics_k = [p for p in occ_kendras if p in ["Sun", "Mars", "Saturn"]]
        
        if len(benefics_k) >= 2:
            predictions.append({
                "category": "Market Trends",
                "prediction": "Moderate and stable trade prices will prevail in the market. Abundant supply.",
                "rule": "Prasna Tantra Ch 3 St. 42 (Benefics occupying quadrants)"
            })
            details.append("Trade: Multiple benefics occupy quadrants promoting stable prices.")
            score_adj += 15
        elif len(malefics_k) >= 2:
            predictions.append({
                "category": "Market Trends",
                "prediction": "High trade prices and inflation will rule. Risk of scarcity in markets.",
                "rule": "Prasna Tantra Ch 3 St. 42 (Malefics occupying quadrants)"
            })
            details.append("Trade: Multiple malefics occupy quadrants indicating market volatility.")
            score_adj -= 15

    if not predictions:
        predictions.append({
            "category": "Commercial Forecast",
            "prediction": "Stable market indicators. Trade transactions will follow general house strength.",
            "rule": "Prasna Tantra Ch 3 St. 183-191"
        })
        details.append("Trade: No specific planetary indicators found in Kendras.")
        
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def get_navamsa_sign(lon):
    """
    Computes the Navamsa sign for a given longitude (0 to 360 degrees).
    """
    sign_idx = int(lon / 30.0) % 12
    deg_in_sign = lon % 30.0
    nav_idx = int(deg_in_sign / (30.0 / 9.0))
    
    # Fire signs (Aries=0, Leo=4, Sagittarius=8) start at Aries (0)
    # Earth signs (Taurus=1, Virgo=5, Capricorn=9) start at Capricorn (9)
    # Air signs (Gemini=2, Libra=6, Aquarius=10) start at Libra (6)
    # Water signs (Cancer=3, Scorpio=7, Pisces=11) start at Cancer (3)
    if sign_idx in [0, 4, 8]:
        start_sign = 0
    elif sign_idx in [1, 5, 9]:
        start_sign = 9
    elif sign_idx in [2, 6, 10]:
        start_sign = 6
    else: # 3, 7, 11
        start_sign = 3
        
    return (start_sign + nav_idx) % 12

def check_mrityu_yoga(chart):
    """
    Checks if Mrityu Yoga is present in the chart.
    Mrityu Yoga is defined as:
    - Lagna Lord in 8th house, or
    - 8th Lord in Lagna, or
    - Moon in the 8th house.
    """
    lagna_sign = chart.lagna_sign
    eighth_sign = (lagna_sign + 7) % 12
    
    lagnapathi = chart.lagnapathi
    eighth_lord = SIGN_LORDS[eighth_sign]
    
    lagnapathi_sign = get_sign(chart.planets[lagnapathi]["longitude"])
    eighth_lord_sign = get_sign(chart.planets[eighth_lord]["longitude"])
    moon_sign = get_sign(chart.planets["Moon"]["longitude"])
    
    is_mrityu = (lagnapathi_sign == eighth_sign) or (eighth_lord_sign == lagna_sign) or (moon_sign == eighth_sign)
    
    reasons = []
    if lagnapathi_sign == eighth_sign:
        reasons.append(f"Lagna Lord ({lagnapathi}) in the 8th house ({get_sign_name(eighth_sign)})")
    if eighth_lord_sign == lagna_sign:
        reasons.append(f"8th Lord ({eighth_lord}) in Lagna ({get_sign_name(lagna_sign)})")
    if moon_sign == eighth_sign:
        reasons.append(f"Moon in the 8th house ({get_sign_name(eighth_sign)})")
        
    return is_mrityu, ", ".join(reasons)

def evaluate_dreams(chart):
    """
    Evaluates queries on dreams (Prasna Tantra Ch 3 Stanzas 144-148).
    """
    lagna_sign = chart.lagna_sign
    sun_lon = chart.planets["Sun"]["longitude"]
    
    predictions = []
    details = []
    score_adj = 0
    
    # 1. Determine planet strengths and the strongest planet
    avastha_vals = {
        "Deeptha": 10, "Athiveerya": 9, "Suveerya": 8, "Swastha": 7, "Muditha": 6,
        "Neutral": 5, "Pariheena": 4, "Suptha": 3, "Nipeeditha": 2, "Deena": 1, "Mushita": 0
    }
    
    planet_strengths = {}
    weak_planets_count = 0
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p_data = chart.planets[p]
        p_avastha = get_planetary_avastha(p, p_data["longitude"], p_data, sun_lon, chart.planets)
        strength = avastha_vals.get(p_avastha, 5)
        # Adjust for combustion
        if p != "Sun" and check_combustion(p, p_data["longitude"], sun_lon):
            strength = max(0, strength - 3)
        planet_strengths[p] = strength
        if strength <= 3:
            weak_planets_count += 1
            
    # Strongest planet
    strongest_planet = max(planet_strengths, key=planet_strengths.get)
    strongest_strength = planet_strengths[strongest_planet]
    
    # Classical theme mapping
    theme_map = {
        "Sun": "A king, fire, weapon, or a bloody act.",
        "Moon": "White flower, white cloth, scent, or a woman.",
        "Mars": "Blood, flesh, pearl, or gold.",
        "Mercury": "Journeying in the heavens.",
        "Jupiter": "Money and the visit of relatives.",
        "Venus": "Bathing in a tank or river.",
        "Saturn": "Climbing elevated places such as hills, tall buildings, etc."
    }
    
    # 2. Check occupants of Lagna
    lagna_occupants = []
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        if get_sign(chart.planets[p]["longitude"]) == lagna_sign:
            lagna_occupants.append(p)
            
    # 3. Navamsa Lagna Lord
    nav_lagna_sign = get_navamsa_sign(chart.lagna_sidereal)
    nav_lord = SIGN_LORDS[nav_lagna_sign]
    
    details.append(f"Dreams: Lagna is {get_sign_name(lagna_sign)}. Navamsa Lagna is {get_sign_name(nav_lagna_sign)} (ruled by {nav_lord}).")
    details.append(f"Dreams: Strongest planet in chart is {strongest_planet} (Strength: {strongest_strength}).")
    
    # Process indicators
    if lagna_occupants:
        for p in lagna_occupants:
            theme = theme_map.get(p, "Ordinary dream.")
            predictions.append({
                "category": "Dream Indication",
                "prediction": f"Lagna occupant {p} indicates dreams of: {theme}",
                "rule": f"Prasna Tantra Ch 3 St. 144-146 (Occupant {p} in Lagna)"
            })
            details.append(f"Dream indication from Lagna occupant {p}: {theme}")
            
    # Stanza 146: "or of the nature of dream can be divined according to Navamsa Lagna."
    nav_theme = theme_map.get(nav_lord, "Ordinary dream.")
    predictions.append({
        "category": "Dream Indication",
        "prediction": f"Navamsa Lagna Lord {nav_lord} indicates dreams of: {nav_theme}",
        "rule": "Prasna Tantra Ch 3 St. 146 (Navamsa Lagna Lord)"
    })
    details.append(f"Dream indication from Navamsa Lagna Lord {nav_lord}: {nav_theme}")
    
    # Stanza 147: "Or the nature of the dream should be ascertained with reference to the strongest planet..."
    strong_theme = theme_map.get(strongest_planet, "Ordinary dream.")
    predictions.append({
        "category": "Dream Indication",
        "prediction": f"Strongest planet {strongest_planet} indicates dreams of: {strong_theme}",
        "rule": "Prasna Tantra Ch 3 St. 147 (Strongest Planet)"
    })
    details.append(f"Dream indication from Strongest Planet {strongest_planet}: {strong_theme}")
    
    # Stanza 147: "If all planets are weak, he will have evil dreams."
    if weak_planets_count == 7:
        predictions.append({
            "category": "Dream Quality",
            "prediction": "The querent will have evil/fearful dreams (all planets are weak).",
            "rule": "Prasna Tantra Ch 3 St. 147 (All planets weak)"
        })
        details.append("Dream quality: All planets are weak, signifying evil/inauspicious dreams.")
        score_adj -= 20
    elif strongest_strength <= 5: # relatively even/moderate
        predictions.append({
            "category": "Dream Quality",
            "prediction": "The querent will have ordinary or mundane dreams (planetary influences are evenly disposed).",
            "rule": "Prasna Tantra Ch 3 St. 147 (Evenly disposed)"
        })
        details.append("Dream quality: Planetary influences are evenly/moderately disposed, indicating ordinary dreams.")
    else:
        details.append("Dream quality: Influences are distinct, indicating vivid dreams of the indicated theme.")
        score_adj += 10
        
    # Stanza 148: "If the Sun is in the ascendant aspected by the Moon or if both the Sun and the Moon are in the ascendant..."
    sun_in_lagna = "Sun" in lagna_occupants
    moon_in_lagna = "Moon" in lagna_occupants
    
    moon_aspects_sun = aspects_sign(chart.planets["Moon"]["longitude"], lagna_sign)
    
    if (sun_in_lagna and moon_aspects_sun) or (sun_in_lagna and moon_in_lagna):
        predictions.append({
            "category": "Dream Quality",
            "prediction": "The querent will experience a bad dream/nightmare. Duration of the dream corresponds to the rising sign duration (approx. 2 hours).",
            "rule": "Prasna Tantra Ch 3 St. 148"
        })
        details.append("Dream quality: Sun and Moon combination indicates a nightmare/bad dream.")
        score_adj -= 15
        
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def evaluate_ships(chart):
    """
    Evaluates queries on ships, safe voyage, cargo, sinking, and transactions (Stanzas 172-180).
    """
    lagna_sign = chart.lagna_sign
    lagnapathi = chart.lagnapathi
    eighth_sign = (lagna_sign + 7) % 12
    eighth_lord = SIGN_LORDS[eighth_sign]
    seventh_sign = (lagna_sign + 6) % 12
    moon_sign = get_sign(chart.planets["Moon"]["longitude"])
    moon_lord = SIGN_LORDS[moon_sign]
    
    nav_lagna_sign = get_navamsa_sign(chart.lagna_sidereal)
    nav_lagnapathi = SIGN_LORDS[nav_lagna_sign]
    
    sun_lon = chart.planets["Sun"]["longitude"]
    
    predictions = []
    details = []
    score_adj = 0
    
    def planet_s(p):
        return get_sign(chart.planets[p]["longitude"])
        
    lagnapathi_sign = planet_s(lagnapathi)
    eighth_lord_sign = planet_s(eighth_lord)
    
    # 1. Profit from ship (Stanza 173)
    kendra_signs = [lagna_sign, (lagna_sign + 3) % 12, (lagna_sign + 6) % 12, (lagna_sign + 9) % 12]
    upachaya_signs = [(lagna_sign + 2) % 12, (lagna_sign + 5) % 12, (lagna_sign + 10) % 12] # 3rd, 6th, 11th
    
    benefics_in_kendra = []
    malefics_in_3_6_11 = []
    
    for p in ["Jupiter", "Venus", "Moon", "Mercury"]:
        if p == "Mercury" and check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
            continue
        if planet_s(p) in kendra_signs:
            benefics_in_kendra.append(p)
            
    for p in ["Sun", "Mars", "Saturn"]:
        if planet_s(p) in upachaya_signs:
            malefics_in_3_6_11.append(p)
            
    if benefics_in_kendra and malefics_in_3_6_11:
        predictions.append({
            "category": "Voyage Profit",
            "prediction": f"The ship brings gain and benefit. Benefics in quadrants: {', '.join(benefics_in_kendra)}. Malefics in 3/6/11: {', '.join(malefics_in_3_6_11)}.",
            "rule": "Prasna Tantra Ch 3 St. 173"
        })
        details.append("Voyage: Benefics in quadrants and malefics in 3/6/11 indicate profit.")
        score_adj += 15
        
    # 2. Voyage Safe & Cargo (Stanza 174)
    lagnapathi_retro = chart.planets[lagnapathi]["speed"] < 0
    nav_lagnapathi_retro = chart.planets[nav_lagnapathi]["speed"] < 0
    
    if lagnapathi_retro and nav_lagnapathi_retro:
        aspected_by_benefic = False
        aspected_by_malefic = False
        
        for b in ["Jupiter", "Venus", "Moon", "Mercury"]:
            if b == "Mercury" and check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
                continue
            if aspects_sign(chart.planets[b]["longitude"], lagnapathi_sign) or aspects_sign(chart.planets[b]["longitude"], planet_s(nav_lagnapathi)):
                aspected_by_benefic = True
                
        for m in ["Sun", "Mars", "Saturn"]:
            if aspects_sign(chart.planets[m]["longitude"], lagnapathi_sign) or aspects_sign(chart.planets[m]["longitude"], planet_s(nav_lagnapathi)):
                aspected_by_malefic = True
                
        if aspected_by_benefic:
            predictions.append({
                "category": "Voyage Arrival",
                "prediction": "The ship with merchandise (cargo) arrives safe (Lagna and Navamsa lords retrograde & aspected by benefics).",
                "rule": "Prasna Tantra Ch 3 St. 174"
            })
            details.append("Voyage: Retrograde lords aspected by benefics indicates safe arrival of ship with cargo.")
            score_adj += 15
        elif aspected_by_malefic:
            predictions.append({
                "category": "Voyage Arrival",
                "prediction": "The ship arrives but without any merchandise (lords retrograde & aspected by malefics).",
                "rule": "Prasna Tantra Ch 3 St. 174"
            })
            details.append("Voyage: Retrograde lords aspected by malefics indicates loss of merchandise.")
            score_adj -= 10
            
    # 3. Transaction Gain (Stanza 175)
    if lagnapathi_sign == lagna_sign and eighth_lord_sign == eighth_sign:
        predictions.append({
            "category": "Voyage Transaction",
            "prediction": "Gain will accrue in the transaction of the ship (lords in own signs).",
            "rule": "Prasna Tantra Ch 3 St. 175"
        })
        details.append("Voyage: Lagna Lord in Lagna and 8th Lord in 8th house indicate transactional gain.")
        score_adj += 15
        
    benefics_in_8 = []
    for b in ["Jupiter", "Venus", "Moon", "Mercury"]:
        if b == "Mercury" and check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
            continue
        if planet_s(b) == eighth_sign:
            avastha_vals = {
                "Deeptha": 10, "Athiveerya": 9, "Suveerya": 8, "Swastha": 7, "Muditha": 6,
                "Neutral": 5, "Pariheena": 4, "Suptha": 3, "Nipeeditha": 2, "Deena": 1, "Mushita": 0
            }
            p_data = chart.planets[b]
            p_avastha = get_planetary_avastha(b, p_data["longitude"], p_data, sun_lon, chart.planets)
            if avastha_vals.get(p_avastha, 5) >= 6:
                benefics_in_8.append(b)
                
    if benefics_in_8:
        predictions.append({
            "category": "Voyage Transaction",
            "prediction": f"Strong benefic {', '.join(benefics_in_8)} in the 8th house indicates gain and beneficial results.",
            "rule": "Prasna Tantra Ch 3 St. 175"
        })
        details.append(f"Voyage: Strong benefic {', '.join(benefics_in_8)} in the 8th house.")
        score_adj += 15
        
    # 4. Early Arrival (Stanza 176)
    is_mrityu, mrityu_reasons = check_mrityu_yoga(chart)
    if is_mrityu:
        predictions.append({
            "category": "Voyage Arrival",
            "prediction": f"The ship will arrive early due to Mrityu Yoga: {mrityu_reasons}.",
            "rule": "Prasna Tantra Ch 3 St. 176"
        })
        details.append(f"Voyage: Early arrival indicated by Mrityu Yoga ({mrityu_reasons}).")
        score_adj += 10
        
    # 5. Drowning of Commander (Stanza 177)
    rel_8_lagna = get_planet_relationship(eighth_lord, chart.planets[eighth_lord], lagnapathi, chart.planets[lagnapathi])
    rel_8_moon_lord = get_planet_relationship(eighth_lord, chart.planets[eighth_lord], moon_lord, chart.planets[moon_lord])
    rel_8_moon = get_planet_relationship(eighth_lord, chart.planets[eighth_lord], "Moon", chart.planets["Moon"])
    
    is_inimical_8 = False
    reasons_inimical_8 = []
    if rel_8_lagna and not rel_8_lagna["is_friendly"]:
        is_inimical_8 = True
        reasons_inimical_8.append("Lagna Lord")
    if rel_8_moon_lord and not rel_8_moon_lord["is_friendly"]:
        is_inimical_8 = True
        reasons_inimical_8.append("Moon Lord")
    if rel_8_moon and not rel_8_moon["is_friendly"]:
        is_inimical_8 = True
        reasons_inimical_8.append("Moon")
        
    if is_inimical_8:
        predictions.append({
            "category": "Voyage Safety",
            "prediction": f"The commander/owner of the ship will get drowned in the sea (8th Lord has hostile relationship with {', '.join(reasons_inimical_8)}).",
            "rule": "Prasna Tantra Ch 3 St. 177"
        })
        details.append(f"Voyage Danger: Hostile aspect from 8th Lord to {', '.join(reasons_inimical_8)} (Drowning hazard).")
        score_adj -= 25
        
    # 6. Sinking of Ship (Stanza 178)
    aspects_lagna = aspects_sign(chart.planets[lagnapathi]["longitude"], lagna_sign)
    aspects_8th = aspects_sign(chart.planets[eighth_lord]["longitude"], eighth_sign)
    
    if not aspects_lagna and not aspects_8th:
        predictions.append({
            "category": "Voyage Safety",
            "prediction": "It is certain that the ship in voyage will get sunk (Lagna Lord and 8th Lord do not aspect their respective houses).",
            "rule": "Prasna Tantra Ch 3 St. 178"
        })
        details.append("Voyage Danger: Neither Lagna Lord nor 8th Lord aspects its own house, indicating sinking.")
        score_adj -= 30
        
    # 7. Loss of cargo but ship safe (Stanza 179)
    if lagnapathi_sign == seventh_sign or eighth_lord_sign == seventh_sign:
        predictions.append({
            "category": "Voyage Safety",
            "prediction": "The merchandise will be lost, but the ship will return home safe (Lagna or 8th Lord in 7th house).",
            "rule": "Prasna Tantra Ch 3 St. 179"
        })
        details.append("Voyage: Lagna Lord or 8th Lord in the 7th house points to cargo loss but safe ship.")
        score_adj -= 10
        
    # 8. Mutual quarrels (Stanza 180)
    rel_lagna_moon_lord = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], moon_lord, chart.planets[moon_lord])
    if rel_lagna_moon_lord and not rel_lagna_moon_lord["is_friendly"]:
        predictions.append({
            "category": "Voyage Discord",
            "prediction": "The men on the ship will be involved in mutual quarrels and discord (mutual hostile aspect between Lagna Lord and Moon Lord).",
            "rule": "Prasna Tantra Ch 3 St. 180"
        })
        details.append("Voyage Discord: Hostile relationship between Lagna Lord and Chandra Lagna Lord.")
        score_adj -= 15
        
    if not predictions:
        predictions.append({
            "category": "Voyage Forecast",
            "prediction": "Standard safe voyage is indicated. No specific afflictions or major combinations detected.",
            "rule": "Prasna Tantra Ch 3 St. 172-180"
        })
        details.append("Voyage: General planetary placements indicate standard safety.")
        
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def evaluate_rumours(chart):
    """
    Evaluates queries on the truth of rumours or news (Stanzas 181-182).
    """
    lagna_sign = chart.lagna_sign
    lagnapathi = chart.lagnapathi
    moon_sign = get_sign(chart.planets["Moon"]["longitude"])
    sun_lon = chart.planets["Sun"]["longitude"]
    
    predictions = []
    details = []
    score_adj = 0
    
    # 1. Check if Lagna Lord is retrograde (unreliable)
    lagnapathi_retro = chart.planets[lagnapathi]["speed"] < 0
    if lagnapathi_retro:
        predictions.append({
            "category": "News Reliability",
            "prediction": f"The news or rumour is completely UNRELIABLE and false, regardless of whether it is good or bad (Lagna Lord {lagnapathi} is retrograde).",
            "rule": "Prasna Tantra Ch 3 St. 182"
        })
        details.append(f"Rumours: Lagna Lord ({lagnapathi}) is retrograde, indicating news is false/unreliable.")
        score_adj -= 30
        return {
            "predictions": predictions,
            "details": details,
            "score_adjustment": score_adj
        }
        
    # 2. Check support from benefics vs malefics
    kendra_signs = [lagna_sign, (lagna_sign + 3) % 12, (lagna_sign + 6) % 12, (lagna_sign + 9) % 12]
    
    lagnapathi_sign = get_sign(chart.planets[lagnapathi]["longitude"])
    lagnapathi_in_kendra = lagnapathi_sign in kendra_signs
    moon_in_kendra = moon_sign in kendra_signs
    
    benefic_score = 0
    malefic_score = 0
    
    # Check Lagna sign
    for b in ["Jupiter", "Venus", "Moon", "Mercury"]:
        if b == "Mercury" and check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
            continue
        if get_sign(chart.planets[b]["longitude"]) == lagna_sign or aspects_sign(chart.planets[b]["longitude"], lagna_sign):
            benefic_score += 1
            
    for m in ["Sun", "Mars", "Saturn"]:
        if get_sign(chart.planets[m]["longitude"]) == lagna_sign or aspects_sign(chart.planets[m]["longitude"], lagna_sign):
            malefic_score += 1
            
    # Check Lagna Lord
    for b in ["Jupiter", "Venus", "Moon", "Mercury"]:
        if b == "Mercury" and check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
            continue
        if b == lagnapathi:
            continue
        rel = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], b, chart.planets[b])
        if rel and rel["is_friendly"]:
            benefic_score += 1
            
    for m in ["Sun", "Mars", "Saturn"]:
        if m == lagnapathi:
            continue
        rel = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], m, chart.planets[m])
        if rel and not rel["is_friendly"]:
            malefic_score += 1
            
    # Check Moon
    for b in ["Jupiter", "Venus", "Mercury"]:
        if b == "Mercury" and check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
            continue
        rel = get_planet_relationship("Moon", chart.planets["Moon"], b, chart.planets[b])
        if rel and rel["is_friendly"]:
            benefic_score += 1
            
    for m in ["Sun", "Mars", "Saturn"]:
        rel = get_planet_relationship("Moon", chart.planets["Moon"], m, chart.planets[m])
        if rel and not rel["is_friendly"]:
            malefic_score += 1
            
    if lagnapathi_in_kendra:
        benefic_score += 1
    if moon_in_kendra:
        benefic_score += 1
        
    details.append(f"Rumours: Benefic score is {benefic_score}. Malefic score is {malefic_score}.")
    details.append(f"Rumours: Lagna Lord in Kendra: {lagnapathi_in_kendra}. Moon in Kendra: {moon_in_kendra}.")
    
    if benefic_score > malefic_score:
        predictions.append({
            "category": "News Reliability",
            "prediction": "Favourable news received is RELIABLE and true. The significators are supported by benefics or occupy quadrants.",
            "rule": "Prasna Tantra Ch 3 St. 181"
        })
        details.append("Rumours: Favourable news is reliable due to benefic support/quadrant placement.")
        score_adj += 20
    elif malefic_score > benefic_score:
        predictions.append({
            "category": "News Reliability",
            "prediction": "Evil or unfavourable news received is CORRECT. The significators are afflicted by malefics.",
            "rule": "Prasna Tantra Ch 3 St. 182"
        })
        details.append("Rumours: Unfavourable/evil news is correct due to malefic afflictions.")
        score_adj -= 20
    else:
        predictions.append({
            "category": "News Reliability",
            "prediction": "Mixed or inconclusive indicators. The rumour cannot be fully verified, but check subsequent developments.",
            "rule": "Prasna Tantra Ch 3 St. 181-182"
        })
        details.append("Rumours: Balanced influences indicate news is partially true or unconfirmed.")
        
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

def evaluate_sexual_matters(chart):
    """
    Evaluates queries on sexual matters, union, partner types, and timing (Chapter IV, Stanzas 35-40).
    """
    lagna_sign = chart.lagna_sign
    lagnapathi = chart.lagnapathi
    seventh_sign = (lagna_sign + 6) % 12
    seventh_lord = SIGN_LORDS[seventh_sign]
    
    sun_lon = chart.planets["Sun"]["longitude"]
    moon_lon = chart.planets["Moon"]["longitude"]
    moon_sign = get_sign(moon_lon)
    
    predictions = []
    details = []
    score_adj = 0
    
    def get_house_of_planet(p):
        p_sign = get_sign(chart.planets[p]["longitude"])
        return ((p_sign - lagna_sign) % 12) + 1
        
    lagnapathi_house = get_house_of_planet(lagnapathi)
    seventh_lord_house = get_house_of_planet(seventh_lord)
    
    # 1. Partner Type (Stanzas 35-36)
    occ_7 = []
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        if get_sign(chart.planets[p]["longitude"]) == seventh_sign:
            occ_7.append(p)
            
    partner_type = None
    rule_source = None
    
    if occ_7:
        if any(p in ["Mars", "Sun", "Venus"] for p in occ_7):
            partner_type = "intimacy with another partner (outside marriage / adultery)"
            rule_source = f"occupant {', '.join([p for p in occ_7 if p in ['Mars', 'Sun', 'Venus']])} in 7th"
            score_adj -= 10
        elif "Jupiter" in occ_7:
            partner_type = "intimacy with their own spouse"
            rule_source = "Jupiter in 7th"
            score_adj += 15
        elif any(p in ["Mercury", "Moon"] for p in occ_7):
            partner_type = "intimacy with a casual partner or prostitute"
            rule_source = f"occupant {', '.join([p for p in occ_7 if p in ['Mercury', 'Moon']])} in 7th"
            score_adj -= 5
        elif "Saturn" in occ_7:
            partner_type = "intimacy with an elderly or low-status/low-caste partner"
            rule_source = "Saturn in 7th"
            score_adj -= 10
    else:
        if seventh_lord in ["Mars", "Sun", "Venus"]:
            partner_type = "intimacy with another partner (outside marriage / adultery) indicated by 7th Lord"
            rule_source = f"7th Lord {seventh_lord}"
            score_adj -= 10
        elif seventh_lord == "Jupiter":
            partner_type = "intimacy with their own spouse indicated by 7th Lord"
            rule_source = "7th Lord Jupiter"
            score_adj += 15
        elif seventh_lord in ["Mercury", "Moon"]:
            partner_type = "intimacy with a casual partner or prostitute indicated by 7th Lord"
            rule_source = f"7th Lord {seventh_lord}"
            score_adj -= 5
        elif seventh_lord == "Saturn":
            partner_type = "intimacy with an elderly or low-status/low-caste partner indicated by 7th Lord"
            rule_source = "7th Lord Saturn"
            score_adj -= 10
            
    if partner_type:
        predictions.append({
            "category": "Partner Indication",
            "prediction": f"The query indicates {partner_type}.",
            "rule": f"Prasna Tantra Ch 4 St. 35-36 ({rule_source})"
        })
        details.append(f"Sexual: Partner type is {partner_type} based on {rule_source}.")
        
    # Partner Description
    age_char = None
    age_source = None
    rep_planet = occ_7[0] if occ_7 else seventh_lord
    
    if rep_planet == "Moon":
        moon_dist = (moon_lon - sun_lon) % 360
        if moon_dist < 48.0 or moon_dist > 312.0:
            age_char = "a young partner (Bala Moon)"
        else:
            age_char = "a mature partner"
        age_source = "Moon"
    elif rep_planet == "Mercury":
        age_char = "a young girl/partner"
        age_source = "Mercury"
    elif rep_planet == "Saturn":
        age_char = "an elderly partner"
        age_source = "Saturn"
    elif rep_planet in ["Sun", "Jupiter"]:
        age_char = "a partner in confinement (pregnant or recently delivered)"
        age_source = rep_planet
    elif rep_planet in ["Mars", "Venus"]:
        age_char = "a quarrelsome or highly passionate partner"
        age_source = rep_planet
        
    if age_char:
        predictions.append({
            "category": "Partner Description",
            "prediction": f"The partner is likely to be {age_char}.",
            "rule": f"Prasna Tantra Ch 4 St. 35-36 (Age/Mood by {age_source})"
        })
        details.append(f"Sexual: Partner description is '{age_char}' based on {age_source}.")
        
    # 2. Secretion and Pleasure (Stanzas 37-39)
    rel_moon_benefics = []
    rel_moon_malefics = []
    
    for b in ["Jupiter", "Venus", "Mercury"]:
        if b == "Mercury" and check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
            continue
        rel = get_planet_relationship("Moon", chart.planets["Moon"], b, chart.planets[b])
        if rel and rel["is_applying"]:
            rel_moon_benefics.append(b)
            
    for m in ["Sun", "Mars", "Saturn"]:
        rel = get_planet_relationship("Moon", chart.planets["Moon"], m, chart.planets[m])
        if rel and rel["is_applying"]:
            rel_moon_malefics.append(m)
            
    if rel_moon_benefics:
        predictions.append({
            "category": "Union Quality",
            "prediction": f"The union will be filled with pleasure, happiness, and joy (Moon in Ithasala with benefics: {', '.join(rel_moon_benefics)}).",
            "rule": "Prasna Tantra Ch 4 St. 37"
        })
        details.append(f"Sexual: Moon has applying Ithasala with benefics {', '.join(rel_moon_benefics)} indicating happy union.")
        score_adj += 15
    elif rel_moon_malefics:
        predictions.append({
            "category": "Union Quality",
            "prediction": f"The union will be marked by quarrels, angry exchanges, or distress (Moon in Ithasala with malefics: {', '.join(rel_moon_malefics)}).",
            "rule": "Prasna Tantra Ch 4 St. 38"
        })
        details.append(f"Sexual: Moon has applying Ithasala with malefics {', '.join(rel_moon_malefics)} indicating discordant union.")
        score_adj -= 15
        
    # Special Satisfaction Combination
    jup_in_1 = get_sign(chart.planets["Jupiter"]["longitude"]) == lagna_sign
    ven_in_7 = get_sign(chart.planets["Venus"]["longitude"]) == seventh_sign
    moon_in_4 = get_sign(chart.planets["Moon"]["longitude"]) == (lagna_sign + 3) % 12
    
    if jup_in_1 and ven_in_7 and moon_in_4:
        predictions.append({
            "category": "Union Quality",
            "prediction": "The secretion and union will bring complete satisfaction, ecstasy, and joy to the couple.",
            "rule": "Prasna Tantra Ch 4 St. 38 (Jupiter in Lagna, Venus in 7th, Moon in 4th)"
        })
        details.append("Sexual: Special configuration (Jup 1st, Ven 7th, Moon 4th) present for complete satisfaction.")
        score_adj += 20
        
    # Moon Kamboola with benefic
    kamboola_found = False
    for b in ["Jupiter", "Venus", "Mercury"]:
        if b == "Mercury" and check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
            continue
        k_yoga = detect_kamboola_yoga(lagnapathi, chart.planets[lagnapathi], b, chart.planets[b], chart.planets["Moon"])
        if k_yoga:
            kamboola_found = True
            break
            
    if kamboola_found:
        predictions.append({
            "category": "Union Quality",
            "prediction": "The partner's secretion will be fresh like a flower and of pleasant odour (Moon Kamboola Yoga with benefic).",
            "rule": "Prasna Tantra Ch 4 St. 39"
        })
        details.append("Sexual: Moon has Kamboola Yoga with a benefic, indicating pleasant/fresh secretion.")
        score_adj += 10
        
    # Moon in own house or exaltation
    if moon_sign == 3 or moon_sign == 1:
        predictions.append({
            "category": "Union Location",
            "prediction": "The union will take place in a grand place or mansion (Moon in own house or exaltation).",
            "rule": "Prasna Tantra Ch 4 St. 39"
        })
        details.append("Sexual: Moon in own house/exaltation indicates union in a grand place.")
        score_adj += 10
        
    # Moon in common sign
    if moon_sign in [2, 5, 8, 11]:
        predictions.append({
            "category": "Partner Verification",
            "prediction": "The union is with the querent's own spouse (Moon in a common sign).",
            "rule": "Prasna Tantra Ch 4 St. 39"
        })
        details.append("Sexual: Moon in a common sign indicates union is with spouse.")
        score_adj += 10
        
    # 3. Extra-marital, Menses & Timing
    if lagna_sign in [0, 3, 6, 9]:
        predictions.append({
            "category": "Partner Verification",
            "prediction": "The querent will have intimacy with a partner other than their own spouse (Movable Lagna).",
            "rule": "Prasna Tantra Ch 4 St. 40"
        })
        details.append("Sexual: Movable Lagna indicates partner other than spouse.")
        score_adj -= 5
        
    saturn_house = get_house_of_planet("Saturn")
    if saturn_house == 4:
        predictions.append({
            "category": "Partner Condition",
            "prediction": "The union will be with a partner who is in menses/period (Saturn in the 4th house).",
            "rule": "Prasna Tantra Ch 4 St. 40"
        })
        details.append("Sexual: Saturn in the 4th house indicates partner is in menses.")
        score_adj -= 10
        
    # Timing
    diurnal_signs = [4, 5, 6, 7, 10, 11]
    nocturnal_signs = [0, 1, 2, 3, 8, 9]
    
    if lagnapathi_house in [3, 8] and seventh_lord_house in [3, 8]:
        predictions.append({
            "category": "Union Timing",
            "prediction": "Union will occur both during the day and during the night (both lords in 3rd/8th house).",
            "rule": "Prasna Tantra Ch 4 St. 40"
        })
        details.append("Sexual Timing: Both Lagna Lord and 7th Lord in 3rd/8th house indicates union day and night.")
    else:
        timing_predicted = False
        if lagna_sign in diurnal_signs and lagnapathi_house in [3, 9]:
            predictions.append({
                "category": "Union Timing",
                "prediction": "Union will occur during the day (lord of diurnal Lagna sign in 3rd/9th house).",
                "rule": "Prasna Tantra Ch 4 St. 40"
            })
            details.append("Sexual Timing: Diurnal Lagna Lord in 3rd/9th indicates day union.")
            timing_predicted = True
        elif lagna_sign in nocturnal_signs and lagnapathi_house in [3, 9]:
            predictions.append({
                "category": "Union Timing",
                "prediction": "Union will occur during the night (lord of nocturnal Lagna sign in 3rd/9th house).",
                "rule": "Prasna Tantra Ch 4 St. 40"
            })
            details.append("Sexual Timing: Nocturnal Lagna Lord in 3rd/9th indicates night union.")
            timing_predicted = True
            
        if not timing_predicted:
            if seventh_sign in diurnal_signs and seventh_lord_house in [3, 9]:
                predictions.append({
                    "category": "Union Timing",
                    "prediction": "Union will occur during the day (lord of diurnal 7th sign in 3rd/9th house).",
                    "rule": "Prasna Tantra Ch 4 St. 40"
                })
                details.append("Sexual Timing: Diurnal 7th Lord in 3rd/9th indicates day union.")
            elif seventh_sign in nocturnal_signs and seventh_lord_house in [3, 9]:
                predictions.append({
                    "category": "Union Timing",
                    "prediction": "Union will occur during the night (lord of nocturnal 7th sign in 3rd/9th house).",
                    "rule": "Prasna Tantra Ch 4 St. 40"
                })
                details.append("Sexual Timing: Nocturnal 7th Lord in 3rd/9th indicates night union.")
                
    if not predictions:
        predictions.append({
            "category": "Union Forecast",
            "prediction": "Standard indications for union and intimacy. Check general 7th house and Venus disposition.",
            "rule": "Prasna Tantra Ch 4 St. 35-40"
        })
        details.append("Sexual: No specific planetary indicators triggered for timing or partner details.")
        
    return {
        "predictions": predictions,
        "details": details,
        "score_adjustment": score_adj
    }

