from .tajaka import get_planet_relationship, get_planetary_avastha, check_combustion

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
    Evaluates master-servant relations & job changes (Stanzas 111-118)
    Lagna = Servant/Employee. 10th house = Master/Employer/Job.
    """
    lagna_sign = chart.lagna_sign
    lagnapathi = chart.lagnapathi
    tenth_lord = SIGN_LORDS[(lagna_sign + 9) % 12]
    
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
    
    predictions = []
    details = []
    score_adj = 0
    
    # Rule: Fixed Lagna and Fixed Lagna Lord -> Stay/Loyal
    if lagna_mobility == "Fixed" and lagnapathi_mobility == "Fixed":
        predictions.append({
            "category": "Employment Stability",
            "prediction": "The employee/servant will remain with the current master/job. Favorable stability.",
            "rule": "Prasna Tantra Ch 3 St. 111 (Fixed Lagna & Lord)"
        })
        details.append("Master-Servant: Both Lagna and Lagna Lord are in Fixed signs (Staying).")
        score_adj += 15
    # Rule: Movable Lagna or Lord in movable sign -> Change
    elif lagna_mobility == "Movable" or lagnapathi_mobility == "Movable":
        predictions.append({
            "category": "Employment Stability",
            "prediction": "The employee/servant will change jobs or leave the current master/employer soon.",
            "rule": "Prasna Tantra Ch 3 St. 112 (Movable Lagna or Lord)"
        })
        details.append("Master-Servant: Lagna or Lagna Lord in Movable sign (Shifting).")
        score_adj -= 10
    else:
        predictions.append({
            "category": "Employment Stability",
            "prediction": "Mixed results. Employee will stay for now but will eventually change after some delay.",
            "rule": "Prasna Tantra Ch 3 St. 111-112 (Common sign influence)"
        })
        details.append("Master-Servant: Lagna/Lagna Lord under Common sign influence (Mixed/delayed change).")
        
    # Check relationship with 10th Lord (Employer)
    rel = get_planet_relationship(lagnapathi, chart.planets[lagnapathi], tenth_lord, chart.planets[tenth_lord])
    if rel:
        if rel["is_friendly"]:
            details.append(f"Master-Servant: Friendly aspect ({rel['aspect_type']}) between employee lord ({lagnapathi}) and employer lord ({tenth_lord}).")
            score_adj += 10
        else:
            details.append(f"Master-Servant: Hostile aspect ({rel['aspect_type']}) between employee lord ({lagnapathi}) and employer lord ({tenth_lord}) indicating friction.")
            score_adj -= 10
    else:
        details.append(f"Master-Servant: No aspect between employee lord ({lagnapathi}) and employer lord ({tenth_lord}).")
        
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
