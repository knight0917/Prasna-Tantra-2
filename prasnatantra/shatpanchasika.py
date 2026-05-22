# Shatpanchasika Rules Engine
# Implements Prithuyasas's Shatpanchasika (translated by V. Subramanya Sastri)

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

PLANET_GENDERS = {
    "Sun": "Male",
    "Mars": "Male",
    "Jupiter": "Male",
    "Moon": "Female",
    "Venus": "Female",
    "Mercury": "Neuter",
    "Saturn": "Neuter"
}

WATERY_SIGNS = [3, 9, 10, 11]  # Cancer, Capricorn, Aquarius, Pisces (per commentary)
SIRSHODAYA_SIGNS = [2, 4, 5, 6, 7, 10]  # Gemini, Leo, Virgo, Libra, Scorpio, Aquarius

def get_sign(longitude):
    return int(longitude / 30.0) % 12

def get_navamsa_sign(longitude):
    sign = get_sign(longitude)
    deg_in_sign = longitude % 30.0
    if sign in [0, 3, 6, 9]:
        start_sign = sign
    elif sign in [1, 4, 7, 10]:
        start_sign = (sign + 8) % 12
    else:
        start_sign = (sign + 4) % 12
    nav_idx = int(deg_in_sign / (30.0 / 9.0))
    return (start_sign + nav_idx) % 12, nav_idx

def aspects_sign(planet_lon, target_sign):
    p_sign = get_sign(planet_lon)
    diff = (target_sign - p_sign) % 12
    # Tajaka aspects: 0 (conjunction), 2/10 (sextile), 3/9 (square), 4/8 (trine), 6 (opposition)
    return diff in [0, 2, 3, 4, 6, 8, 9, 10]

def check_combustion(planet_name, planet_lon, sun_lon):
    if planet_name == "Sun":
        return False
    # Standard Tajaka combustion limits
    limits = {"Mars": 12.0, "Mercury": 8.0, "Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0}
    limit = limits.get(planet_name, 9.0)
    diff = abs(planet_lon - sun_lon) % 360
    if diff > 180:
        diff = 360 - diff
    return diff <= limit

def get_strongest_planet(planets_dict, sun_lon):
    # Rank based on simple sign strength and combustion
    best_p = None
    best_score = -100
    for name, data in planets_dict.items():
        if name in ["Rahu", "Ketu"]:
            continue
        lon = data["longitude"]
        sign = get_sign(lon)
        score = 0
        if check_combustion(name, lon, sun_lon):
            score -= 50
        if sign == (0 if name=="Sun" else 1 if name=="Moon" else 9 if name=="Mars" else 5 if name=="Mercury" else 3 if name=="Jupiter" else 11 if name=="Venus" else 6): # Exalted
            score += 30
        elif sign in ( [4] if name=="Sun" else [3] if name=="Moon" else [0,7] if name=="Mars" else [2,5] if name=="Mercury" else [8,11] if name=="Jupiter" else [1,6] if name=="Venus" else [9,10] ): # Own
            score += 20
        if score > best_score:
            best_score = score
            best_p = name
    return best_p

def evaluate_shatpanchasika(chart, house_num):
    """
    Evaluates Shatpanchasika rules based on the chart and target house.
    Returns a dict with score_adjustment, details, and predictions.
    """
    score_adj = 0
    details = []
    predictions = []

    # Calculate basic parameters
    sun_lon = chart.planets["Sun"]["longitude"]
    moon_lon = chart.planets["Moon"]["longitude"]
    moon_diff = (moon_lon - sun_lon) % 360
    is_moon_full = 108.0 <= moon_diff <= 240.0
    
    # Establish benefics list
    benefics = ["Jupiter", "Venus"]
    if not check_combustion("Mercury", chart.planets["Mercury"]["longitude"], sun_lon):
        benefics.append("Mercury")
    if is_moon_full:
        benefics.append("Moon")

    malefics = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]

    # Helper: occupants of a sign relative to Lagna
    def occupants(h_num):
        target_s = (chart.lagna_sign + h_num - 1) % 12
        return [p for p, data in chart.planets.items() if get_sign(data["longitude"]) == target_s]

    # Helper: planet aspects a specific house
    def planet_aspects_house(planet_name, h_num):
        target_s = (chart.lagna_sign + h_num - 1) % 12
        return aspects_sign(chart.planets[planet_name]["longitude"], target_s)

    # Helper: planet conjoins or aspects a specific sign
    def influences_sign(planet_name, target_sign):
        p_sign = get_sign(chart.planets[planet_name]["longitude"])
        if p_sign == target_sign:
            return True
        return aspects_sign(chart.planets[planet_name]["longitude"], target_sign)

    # 1. General Principles (Chapter I, Sloka 4)
    lagna_occupants = occupants(1)
    benefic_in_lagna = any(p in benefics for p in lagna_occupants)
    malefic_in_lagna = any(p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"] for p in lagna_occupants)
    
    rising_nav_sign, rising_nav_idx = get_navamsa_sign(chart.lagna_sidereal)
    rising_nav_owner = SIGN_LORDS[rising_nav_sign]
    rising_nav_benefic = rising_nav_owner in benefics

    is_seershodaya = chart.lagna_sign in SIRSHODAYA_SIGNS
    is_prishtodaya = chart.lagna_sign in [0, 1, 3, 8, 9]

    if benefic_in_lagna and rising_nav_benefic and is_seershodaya:
        score_adj += 30
        details.append("Shatpanchasika Ch. I Sl. 4: Benefic in Lagna, benefic Navamsa rising, and Seershodaya sign. Highly favorable for success.")
        predictions.append({"category": "General", "prediction": "Certain Success / Accomplishment of desires", "rule": "Ch. I Sl. 4"})
    elif malefic_in_lagna and not rising_nav_benefic and is_prishtodaya:
        score_adj -= 30
        details.append("Shatpanchasika Ch. I Sl. 4: Malefic in Lagna, malefic Navamsa rising, and Prishtodaya sign. Highly unfavorable.")
        predictions.append({"category": "General", "prediction": "Failure / Obstacles and defeat", "rule": "Ch. I Sl. 4"})
    else:
        score_adj += 5
        details.append("Shatpanchasika Ch. I Sl. 4: Mixed features in Lagna/Navamsa/Sign shape. Success after delay or struggles.")
        predictions.append({"category": "General", "prediction": "Success after difficulty", "rule": "Ch. I Sl. 4"})

    # Dhatu / Mula / Jeeva (Ch I Sloka 6-7)
    # Determine if subject of query is mineral, vegetable, or animal
    is_odd_lagna = (chart.lagna_sign % 2) != 0
    if is_odd_lagna:
        if rising_nav_idx in [0, 3, 6]:
            subject_kind = "Mineral (Dhatu)"
        elif rising_nav_idx in [1, 4, 7]:
            subject_kind = "Vegetable / Roots (Mula)"
        else:
            subject_kind = "Animal / Living Being (Jeeva)"
    else:
        if rising_nav_idx in [0, 3, 6]:
            subject_kind = "Animal / Living Being (Jeeva)"
        elif rising_nav_idx in [1, 4, 7]:
            subject_kind = "Vegetable / Roots (Mula)"
        else:
            subject_kind = "Mineral (Dhatu)"
            
    # Classify gender of query subject/thief/child (odd navamsa = male, even = female)
    subject_gender = "Male" if (rising_nav_sign % 2 != 0) else "Female"
    predictions.append({
        "category": "Query Object Identification",
        "prediction": f"The query relates to {subject_kind}. Sex/gender of subject is {subject_gender}.",
        "rule": "Ch. I Sl. 6-7"
    })

    # Method B (Stanza 25 / Ch I Sloka 6): Navamsa Aspect Rule
    trine_house_names = {0: "Lagna", 4: "5th house", 8: "9th house"}
    for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        if p_name not in chart.planets:
            continue
        p_lon = chart.planets[p_name]["longitude"]
        p_nav_sign, _ = get_navamsa_sign(p_lon)
        p_nav_owner = SIGN_LORDS[p_nav_sign]
        p_owns_its_nav = (p_nav_owner == p_name)
        
        # Check trine houses relative to rising_nav_sign (Lagna, 5th, 9th in Navamsa)
        for offset in [0, 4, 8]:
            target_nav_sign = (rising_nav_sign + offset) % 12
            diff = (target_nav_sign - p_nav_sign) % 12
            # Planet p_name aspects target_nav_sign in the Navamsa chart if Tajaka aspect exists
            if diff in [0, 2, 3, 4, 6, 8, 9, 10]:
                target_nav_owner = SIGN_LORDS[target_nav_sign]
                if p_owns_its_nav and target_nav_owner == p_name:
                    classification = "Mineral (Dhatu)"
                    rule_detail = f"{p_name} occupies its own Navamsa ({p_nav_sign}) and aspects its own Navamsa in {trine_house_names[offset]} of the Navamsa chart."
                    predictions.append({
                        "category": "Query Object Identification",
                        "prediction": f"Method B (Navamsa Aspect Rule): The query relates to {classification}. {rule_detail}",
                        "rule": "Ch. I Sl. 6 (Stanza 25)"
                    })
                elif not p_owns_its_nav and target_nav_owner == p_name:
                    classification = "Animal / Living Being (Jeeva)"
                    rule_detail = f"{p_name} does not occupy its own Navamsa and aspects its own Navamsa in {trine_house_names[offset]} of the Navamsa chart."
                    predictions.append({
                        "category": "Query Object Identification",
                        "prediction": f"Method B (Navamsa Aspect Rule): The query relates to {classification}. {rule_detail}",
                        "rule": "Ch. I Sl. 6 (Stanza 25)"
                    })
                elif not p_owns_its_nav and target_nav_owner != p_name:
                    classification = "Vegetable / Roots (Mula)"
                    rule_detail = f"{p_name} does not occupy its own Navamsa and aspects another planet's Navamsa in {trine_house_names[offset]} of the Navamsa chart."
                    predictions.append({
                        "category": "Query Object Identification",
                        "prediction": f"Method B (Navamsa Aspect Rule): The query relates to {classification}. {rule_detail}",
                        "rule": "Ch. I Sl. 6 (Stanza 25)"
                    })

    # 2. House-specific evaluations
    # House 1: Health, Body, Undertakings, Thought reading, Subject Description
    if house_num == 1:
        # Ch VII Sloka 7-8 Thought reading
        strongest_p = get_strongest_planet(chart.planets, sun_lon)
        # Find which house the strongest planet occupies
        strongest_p_house = 1
        for h in range(1, 13):
            if strongest_p in occupants(h):
                strongest_p_house = h
                break
        house_significations = {
            1: "the Querent's own body / self",
            3: "brothers / siblings",
            5: "children / issue",
            4: "mother or sister",
            6: "enemies / competitors",
            7: "wife / spouse / partner",
            9: "virtuous action / religious personage / father",
            10: "preceptor / boss / authority figure"
        }
        sig_thought = house_significations.get(strongest_p_house, "miscellaneous matters")
        
        # Check thought focus: self, friend, enemy (Ch VII Sloka 8)
        nav_owner = SIGN_LORDS[rising_nav_sign]
        # In Lagna check
        lagna_lord_is_nav_owner = chart.lagnapathi == nav_owner
        
        if lagna_lord_is_nav_owner:
            focus = "the querent themselves"
        else:
            focus = f"someone associated with the strongest planet in house {strongest_p_house} ({sig_thought})"
            
        predictions.append({
            "category": "Thought Reading",
            "prediction": f"The querist is currently thinking of: {focus}.",
            "rule": "Ch. VII Sl. 7-8"
        })

        # Rule 1: Adhyaya I Sloka 2 (Lagna fall/displacement)
        lagna_sign = chart.lagna_sign
        lagna_lord = SIGN_LORDS[lagna_sign]
        is_lord_or_benefic = influences_sign(lagna_lord, lagna_sign) or any(influences_sign(p, lagna_sign) for p in benefics)
        has_malefic_inf = any(influences_sign(p, lagna_sign) for p in malefics)
        
        displacement = False
        lagna_mobility = lagna_sign % 3  # 0=movable, 1=fixed, 2=dual
        if lagna_mobility == 0:  # Movable
            displacement = is_lord_or_benefic and not has_malefic_inf
        elif lagna_mobility == 1:  # Fixed
            displacement = has_malefic_inf
        elif lagna_mobility == 2:  # Dual
            has_lord = influences_sign(lagna_lord, lagna_sign)
            benefic_count = sum(1 for p in benefics if influences_sign(p, lagna_sign))
            malefic_count = sum(1 for p in malefics if influences_sign(p, lagna_sign))
            displacement = has_lord or (benefic_count > malefic_count)
            
        disp_pred = "Displacement / Transfer from current position/state" if displacement else "No displacement / Stays in current position/state"
        predictions.append({
            "category": "Displacement Status",
            "prediction": disp_pred,
            "rule": "Ch. I Sl. 2"
        })
        details.append(f"Shatpanchasika Ch. I Sl. 2: Lagna sign mobility is {['Movable', 'Fixed', 'Dual'][lagna_mobility]}. Displacement status: {disp_pred}.")
        if displacement:
            score_adj -= 10
        else:
            score_adj += 10

        # Rule 5: Adhyaya VII Sloka 6 (Subject Nature / Age)
        subject_descriptions = []
        if moon_diff < 120.0:
            moon_age = "young"
            moon_desc = "a young girl (not come of age / maiden) or young boy"
        elif moon_diff < 240.0:
            moon_age = "adolescent"
            moon_desc = "an adolescent maiden or youth"
        else:
            moon_age = "old"
            moon_desc = "an old woman or old man"
            
        if influences_sign("Moon", lagna_sign):
            subject_descriptions.append(f"Moon ({moon_age}): {moon_desc}")
        if influences_sign("Mercury", lagna_sign):
            subject_descriptions.append("Mercury: a young girl / unmarried maiden or young boy")
        if influences_sign("Saturn", lagna_sign):
            subject_descriptions.append("Saturn: an old/senile woman or old man")
        if influences_sign("Sun", lagna_sign) or influences_sign("Jupiter", lagna_sign):
            subject_descriptions.append("Sun/Jupiter: a woman recently delivered of a child or a father")
        if influences_sign("Mars", lagna_sign) or influences_sign("Venus", lagna_sign):
            subject_descriptions.append("Mars/Venus: a rough-bodied, robust, or cruel/hard-hearted person")
            
        if subject_descriptions:
            pred_desc = "; ".join(subject_descriptions)
        else:
            pred_desc = "No planet influences the Lagna to describe the subject's age/nature directly."
            
        predictions.append({
            "category": "Query Subject Description",
            "prediction": pred_desc,
            "rule": "Adh. VII Sl. 6"
        })
        details.append(f"Shatpanchasika Adh. VII Sl. 6: Query subject nature/age prediction: {pred_desc}.")

        # Adhyaya II Sloka 5 (Traveler starting success)
        if lagna_mobility == 0:  # Movable Lagna
            if benefic_in_lagna:
                predictions.append({"category": "Traveler Journey Success", "prediction": "Success and favorable outcome for the traveler's journey.", "rule": "Ch. II Sl. 5"})
                score_adj += 15
            elif malefic_in_lagna:
                predictions.append({"category": "Traveler Journey Success", "prediction": "Harm, obstacles, or defeat for the traveler.", "rule": "Ch. II Sl. 5"})
                score_adj -= 15
        elif lagna_mobility == 1:  # Fixed Lagna
            if malefic_in_lagna:
                strong_malefic = False
                for p in lagna_occupants:
                    if p in ["Sun", "Mars", "Saturn"]:
                        p_lon = chart.planets[p]["longitude"]
                        p_sign = get_sign(p_lon)
                        exalted_sign = 0 if p=="Sun" else 9 if p=="Mars" else 6
                        own_signs = [4] if p=="Sun" else [0,7] if p=="Mars" else [9,10]
                        if p_sign == exalted_sign or p_sign in own_signs:
                            strong_malefic = True
                pred_txt = "Favorable outcome for the traveler despite fixed Lagna and malefic presence"
                if strong_malefic:
                    pred_txt += " (Malefic in own or exalted sign makes it highly favorable)"
                predictions.append({"category": "Traveler Journey Success", "prediction": pred_txt, "rule": "Ch. II Sl. 5"})
                score_adj += 10

        # Adhyaya II Sloka 9 (King's march)
        if lagna_mobility == 0:  # Movable
            marching_planets = [p for p in lagna_occupants if p in ["Sun", "Saturn", "Mercury", "Venus"]]
            if marching_planets:
                retro_planets = [p for p in marching_planets if p != "Sun" and chart.planets[p].get("is_retrograde", False)]
                if retro_planets:
                    predictions.append({"category": "King March Status", "prediction": f"The king/leader does not move from headquarters (Retrograde planet {', '.join(retro_planets)} in Lagna).", "rule": "Ch. II Sl. 9"})
                else:
                    predictions.append({"category": "King March Status", "prediction": f"Quick march of the king/leader (Movable Lagna occupied by direct planet {', '.join(marching_planets)}).", "rule": "Ch. II Sl. 9"})

        # Adhyaya II Sloka 10 (Fixed Lagna aspected by Jupiter & Saturn)
        if lagna_mobility == 1:  # Fixed
            aspected_by_jup = planet_aspects_house("Jupiter", 1)
            aspected_by_sat = planet_aspects_house("Saturn", 1)
            if aspected_by_jup and aspected_by_sat:
                predictions.append({"category": "Fighter Movement Status", "prediction": "No prediction can be made regarding departure or arrival (Fixed Lagna aspected by both Jupiter and Saturn).", "rule": "Ch. II Sl. 10"})
            
            malefics_3_5_6 = []
            for h in [3, 5, 6]:
                for p in occupants(h):
                    if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]:
                        malefics_3_5_6.append(f"{p} in house {h}")
            if malefics_3_5_6:
                predictions.append({"category": "Conflict / War Prediction", "prediction": f"Conflict/war occurs (Malefics present: {', '.join(malefics_3_5_6)}).", "rule": "Ch. II Sl. 10"})
                score_adj -= 10
            
            malefics_4_sl10 = [p for p in occupants(4) if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]]
            if malefics_4_sl10:
                predictions.append({"category": "Conflict Outcome", "prediction": f"The enemy retreats (Malefic {', '.join(malefics_4_sl10)} in 4th house).", "rule": "Ch. II Sl. 10"})
                score_adj += 10

        # Adhyaya II Sloka 13 (Fighter movement status)
        if lagna_mobility == 1:  # Fixed Lagna
            if "Saturn" in lagna_occupants or "Jupiter" in lagna_occupants:
                predictions.append({"category": "Enemy Movement Status", "prediction": "The enemy stays in place.", "rule": "Ch. II Sl. 13"})
        elif lagna_mobility == 0:  # Movable Lagna
            if "Sun" in lagna_occupants or "Jupiter" in lagna_occupants:
                predictions.append({"category": "Enemy Movement Status", "prediction": "The enemy arrives.", "rule": "Ch. II Sl. 13"})

        # Adhyaya IV Slokas 3-4 (Lagna Moon)
        if "Moon" in lagna_occupants:
            predictions.append({"category": "General Outcome", "prediction": "Unfavorable results, anxiety or obstacles (Moon in Lagna).", "rule": "Ch. IV Sl. 3-4"})
            score_adj -= 10

    # House 3: Travels, Siblings, Enemy Marching
    elif house_num == 3 or house_num == 6:
        # Ch II rules: Marching and Returning
        lagna_chara = chart.lagna_sign % 3  # 0=movable, 1=fixed, 2=dual
        
        # II-1 & II-2 Lagna mobility
        if lagna_chara == 1:
            predictions.append({
                "category": "Travel / Conflict",
                "prediction": "No journey, enemy stays in position, no defeat, no retreat.",
                "rule": "Ch. II Sl. 1"
            })
        elif lagna_chara == 0:
            predictions.append({
                "category": "Travel / Conflict",
                "prediction": "Journey will occur, enemy marches, potential defeat or change in situation.",
                "rule": "Ch. II Sl. 2"
            })
        else:
            predictions.append({
                "category": "Travel / Conflict",
                "prediction": "Mixed results. Journey starts but faces delay, or partial movement.",
                "rule": "Ch. II Sl. 2"
            })

        # II-3 Malefics in 5th and 6th, or 4th
        malefics_5_6 = [p for p in occupants(5)+occupants(6) if p in ["Sun", "Mars", "Saturn"]]
        malefics_4 = [p for p in occupants(4) if p in ["Sun", "Mars", "Saturn"]]
        if malefics_5_6:
            predictions.append({
                "category": "Enemy Movement",
                "prediction": "The enemy will turn back midway without reaching.",
                "rule": "Ch. II Sl. 3"
            })
        if malefics_4:
            predictions.append({
                "category": "Enemy Movement",
                "prediction": "The enemy will be completely defeated and retreats.",
                "rule": "Ch. II Sl. 3"
            })

        # II-6, 7, 8 Moon position
        moon_s = get_sign(moon_lon)
        moon_chara = moon_s % 3
        if lagna_chara == 0 and moon_chara == 1:
            predictions.append({"category": "Enemy Arrival", "prediction": "The enemy will not arrive.", "rule": "Ch. II Sl. 6"})
        elif lagna_chara == 1 and moon_chara == 0:
            predictions.append({"category": "Enemy Arrival", "prediction": "The enemy will arrive shortly.", "rule": "Ch. II Sl. 6"})
        elif lagna_chara == 1 and moon_chara == 2:
            predictions.append({"category": "Enemy Arrival", "prediction": "The enemy will advance far and then return.", "rule": "Ch. II Sl. 7"})
            
        # II-11 Planets in 4th
        planets_in_4 = occupants(4)
        if "Sun" in planets_in_4 and "Moon" in planets_in_4:
            predictions.append({"category": "Enemy Arrival", "prediction": "The enemy army will not arrive.", "rule": "Ch. II Sl. 11"})
        elif any(p in planets_in_4 for p in ["Mercury", "Jupiter", "Venus"]):
            predictions.append({"category": "Enemy Arrival", "prediction": "The enemy army will arrive very soon.", "rule": "Ch. II Sl. 11"})

        # Ch III Victory/Defeat Town Siege
        defenders_benefics = 0
        attackers_benefics = 0
        for h in range(3, 9):
            defenders_benefics += sum(1 for p in occupants(h) if p in benefics)
        for h in [9, 10, 11, 12, 1, 2]:
            attackers_benefics += sum(1 for p in occupants(h) if p in benefics)
            
        if defenders_benefics > attackers_benefics:
            predictions.append({"category": "Conflict Outcome", "prediction": "Victory to the defenders / citizens.", "rule": "Ch. III Sl. 2"})
            score_adj += 15
        elif attackers_benefics > defenders_benefics:
            predictions.append({"category": "Conflict Outcome", "prediction": "Victory to the attackers / besiegers.", "rule": "Ch. III Sl. 2"})
            score_adj -= 10

        # Rule 5: Adhyaya VII Sloka 9 (Abroad Intentions & Travel)
        is_movable_lagna = (chart.lagna_sign % 3) == 0
        is_movable_nav = (rising_nav_sign % 3) == 0
        is_past_middle_nav = rising_nav_idx >= 5
        intends_travel = is_movable_lagna and is_movable_nav and is_past_middle_nav
        planets_in_6 = [p for p in occupants(6) if p in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]]
        
        travel_outcome = "No specific indication of travel or staying."
        if intends_travel:
            travel_outcome = "Querist intends to travel/go abroad."
            if planets_in_6:
                has_retro = any(chart.planets[p].get("is_retrograde", False) for p in planets_in_6)
                if has_retro:
                    travel_outcome += " Despite obstacles (planet in 6th), traveler still proceeds abroad due to retrograde motion."
                else:
                    travel_outcome += " Travel is dropped/cancelled due to direct planet in 6th house (fallen from 7th)."
            else:
                travel_outcome += " Travel is confirmed and will proceed."
        predictions.append({
            "category": "Travel Intentions",
            "prediction": travel_outcome,
            "rule": "Adh. VII Sl. 9"
        })
        details.append(f"Shatpanchasika Adh. VII Sl. 9: Travel prediction: {travel_outcome}.")

        # Adhyaya II Sloka 4 (Quadruped/Watery 4th house retreat)
        h4_sign = (chart.lagna_sign + 3) % 12
        if h4_sign in [3, 7, 10, 11]:
            predictions.append({"category": "Enemy Movement", "prediction": "The enemy is vanquished and retreats (4th house is a watery sign).", "rule": "Ch. II Sl. 4"})
            score_adj += 10

        # Adhyaya II Sloka 5 (Traveler success/failure on journey)
        lagna_mobility = chart.lagna_sign % 3
        lagna_occupants = occupants(1)
        benefic_in_lagna_loc = any(p in benefics for p in lagna_occupants)
        malefic_in_lagna_loc = any(p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"] for p in lagna_occupants)
        if lagna_mobility == 0:  # Movable
            if benefic_in_lagna_loc:
                predictions.append({"category": "Traveler Journey Success", "prediction": "Success and favorable outcome for the traveler's journey.", "rule": "Ch. II Sl. 5"})
                score_adj += 15
            elif malefic_in_lagna_loc:
                predictions.append({"category": "Traveler Journey Success", "prediction": "Harm, obstacles, or defeat for the traveler.", "rule": "Ch. II Sl. 5"})
                score_adj -= 15
        elif lagna_mobility == 1:  # Fixed
            if malefic_in_lagna_loc:
                strong_malefic = False
                for p in lagna_occupants:
                    if p in ["Sun", "Mars", "Saturn"]:
                        p_lon = chart.planets[p]["longitude"]
                        p_sign = get_sign(p_lon)
                        exalted_sign = 0 if p=="Sun" else 9 if p=="Mars" else 6
                        own_signs = [4] if p=="Sun" else [0,7] if p=="Mars" else [9,10]
                        if p_sign == exalted_sign or p_sign in own_signs:
                            strong_malefic = True
                pred_txt = "Favorable outcome for the traveler despite fixed Lagna and malefic presence"
                if strong_malefic:
                    pred_txt += " (Malefic in own or exalted sign makes it highly favorable)"
                predictions.append({"category": "Traveler Journey Success", "prediction": pred_txt, "rule": "Ch. II Sl. 5"})
                score_adj += 10

        # Adhyaya II Sloka 8 (Conflict and retreat)
        moon_sign = get_sign(moon_lon)
        moon_mobility = moon_sign % 3
        if moon_mobility == 0 and lagna_chara == 2:
            predictions.append({"category": "Enemy Movement", "prediction": "The enemy retreats halfway.", "rule": "Ch. II Sl. 8"})
            score_adj += 5
        elif lagna_chara == 0 and moon_mobility == 2:
            moon_has_malefic_inf = False
            for p in malefics:
                if influences_sign(p, moon_sign):
                    moon_has_malefic_inf = True
                    break
            if moon_has_malefic_inf:
                predictions.append({"category": "Conflict Outcome", "prediction": "Encounter and defeat (Lagna movable, Moon dual with malefic aspect).", "rule": "Ch. II Sl. 8"})
                score_adj -= 15

        # Adhyaya II Sloka 9 (King's march)
        if lagna_mobility == 0:
            marching_planets = [p for p in lagna_occupants if p in ["Sun", "Saturn", "Mercury", "Venus"]]
            if marching_planets:
                retro_planets = [p for p in marching_planets if p != "Sun" and chart.planets[p].get("is_retrograde", False)]
                if retro_planets:
                    predictions.append({"category": "King March Status", "prediction": f"The king/leader does not move from headquarters (Retrograde planet {', '.join(retro_planets)} in Lagna).", "rule": "Ch. II Sl. 9"})
                else:
                    predictions.append({"category": "King March Status", "prediction": f"Quick march of the king/leader (Movable Lagna occupied by direct planet {', '.join(marching_planets)}).", "rule": "Ch. II Sl. 9"})

        # Adhyaya II Sloka 10 (Fixed Lagna aspected by Jupiter & Saturn)
        if lagna_mobility == 1:
            aspected_by_jup = planet_aspects_house("Jupiter", 1)
            aspected_by_sat = planet_aspects_house("Saturn", 1)
            if aspected_by_jup and aspected_by_sat:
                predictions.append({"category": "Fighter Movement Status", "prediction": "No prediction can be made regarding departure or arrival (Fixed Lagna aspected by both Jupiter and Saturn).", "rule": "Ch. II Sl. 10"})
            
            malefics_3_5_6 = []
            for h in [3, 5, 6]:
                for p in occupants(h):
                    if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]:
                        malefics_3_5_6.append(f"{p} in house {h}")
            if malefics_3_5_6:
                predictions.append({"category": "Conflict / War Prediction", "prediction": f"Conflict/war occurs (Malefics present: {', '.join(malefics_3_5_6)}).", "rule": "Ch. II Sl. 10"})
                score_adj -= 10
            
            malefics_4_sl10 = [p for p in occupants(4) if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]]
            if malefics_4_sl10:
                predictions.append({"category": "Conflict Outcome", "prediction": f"The enemy retreats (Malefic {', '.join(malefics_4_sl10)} in 4th house).", "rule": "Ch. II Sl. 10"})
                score_adj += 10

        # Adhyaya II Sloka 12 (Enemy retreat signs)
        retreat_signs = [0, 1, 4, 8]
        if chart.lagna_sign in retreat_signs or h4_sign in retreat_signs:
            predictions.append({"category": "Enemy Movement", "prediction": "The enemy retreats (Lagna or 4th house is Aries, Taurus, Leo, or Sagittarius).", "rule": "Ch. II Sl. 12"})
            score_adj += 10

        # Adhyaya II Sloka 13 (Fighter movement status)
        if lagna_mobility == 1:
            if "Saturn" in lagna_occupants or "Jupiter" in lagna_occupants:
                predictions.append({"category": "Enemy Movement Status", "prediction": "The enemy stays in place.", "rule": "Ch. II Sl. 13"})
        elif lagna_mobility == 0:
            if "Sun" in lagna_occupants or "Jupiter" in lagna_occupants:
                predictions.append({"category": "Enemy Movement Status", "prediction": "The enemy arrives.", "rule": "Ch. II Sl. 13"})

        # Adhyaya III Sloka 1 (Governor victory)
        h10_occ = occupants(10)
        h1_occ = occupants(1)
        h7_occ = occupants(7)
        benefics_in_10_1_7 = any(p in benefics for p in h10_occ + h1_occ + h7_occ)
        if benefics_in_10_1_7:
            predictions.append({"category": "Siege Outcome", "prediction": "Victory to the governor/defenders (Benefic in 10th, 1st, or 7th).", "rule": "Ch. III Sl. 1"})
            score_adj += 15
        
        h9_occ = occupants(9)
        malefics_in_9 = [p for p in h9_occ if p in ["Mars", "Saturn"]]
        if malefics_in_9:
            predictions.append({"category": "Siege Outcome", "prediction": "Complete defeat of the governor/defenders (Mars or Saturn in 9th).", "rule": "Ch. III Sl. 1"})
            score_adj -= 20
            
        benefics_in_9 = [p for p in h9_occ if p in ["Mercury", "Jupiter", "Venus"] and p in benefics]
        if benefics_in_9:
            predictions.append({"category": "Siege Outcome", "prediction": "Splendid victory for the governor/defenders (Benefic in 9th).", "rule": "Ch. III Sl. 1"})
            score_adj += 20

        # Adhyaya III Sloka 3 (Besieger advantage & peace)
        h12_occ = occupants(12)
        h11_occ = occupants(11)
        malefics_12_10_11 = [p for p in h12_occ + h10_occ + h11_occ if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]]
        if malefics_12_10_11:
            predictions.append({"category": "Siege Outcome", "prediction": f"Advantage to the besiegers / bad for townsmen (Malefic {', '.join(malefics_12_10_11)} in 12th, 10th, or 11th).", "rule": "Ch. III Sl. 3"})
            score_adj -= 10
            
        biped_signs = [2, 5, 6, 8, 10]
        h1_sign = chart.lagna_sign
        h12_sign = (chart.lagna_sign + 11) % 12
        h11_sign = (chart.lagna_sign + 10) % 12
        
        benefic_in_1 = any(p in occupants(1) for p in benefics)
        benefic_in_12 = any(p in occupants(12) for p in benefics)
        benefic_in_11 = any(p in occupants(11) for p in benefics)
        
        if benefic_in_1 and benefic_in_12 and benefic_in_11 and (h1_sign in biped_signs) and (h12_sign in biped_signs) and (h11_sign in biped_signs):
            predictions.append({"category": "Siege Outcome", "prediction": "Peace is concluded between parties (Benefics in biped signs in 1st, 12th, and 11th).", "rule": "Ch. III Sl. 3"})
            score_adj += 15
            
        dual_signs = [2, 5, 8, 11]
        malefics_in_dual = []
        for name, data in chart.planets.items():
            if name in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]:
                p_sign = get_sign(data["longitude"])
                if p_sign in dual_signs:
                    malefics_in_dual.append(name)
        if malefics_in_dual:
            predictions.append({"category": "Conflict Status", "prediction": f"Continued war / conflict (Malefics {', '.join(malefics_in_dual)} in dual signs).", "rule": "Ch. III Sl. 3"})
            score_adj -= 10

        # Adhyaya III Slokas 4-5 (Kings' peace/war)
        kendra_planets = []
        for h in [1, 4, 7, 10]:
            h_sign = (chart.lagna_sign + h - 1) % 12
            for p in occupants(h):
                kendra_planets.append((p, h_sign))
                
        peace_found = False
        war_found = False
        for i in range(len(kendra_planets)):
            for j in range(i + 1, len(kendra_planets)):
                p1, s1 = kendra_planets[i]
                p2, s2 = kendra_planets[j]
                p1_lon = chart.planets[p1]["longitude"]
                p2_lon = chart.planets[p2]["longitude"]
                if aspects_sign(p1_lon, s2) and aspects_sign(p2_lon, s1):
                    if p1 in benefics and p2 in benefics and (s1 in biped_signs) and (s2 in biped_signs):
                        peace_found = True
                    if p1 in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"] and p2 in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]:
                        war_found = True
                        
        if peace_found:
            predictions.append({"category": "Conflict Status", "prediction": "Peace between kings/parties (Mutually aspecting benefics in biped signs in Kendras).", "rule": "Ch. III Sl. 4-5"})
            score_adj += 15
        elif war_found:
            predictions.append({"category": "Conflict Status", "prediction": "Continued war/conflict (Mutually aspecting malefics in Kendras).", "rule": "Ch. III Sl. 4-5"})
            score_adj -= 15

        h2_occ = occupants(2)
        h3_occ = occupants(3)
        jup_ven_in_2_3 = [p for p in h2_occ + h3_occ if p in ["Jupiter", "Venus"]]
        if jup_ven_in_2_3:
            predictions.append({"category": "Traveler Return", "prediction": f"Army/traveler returns soon (Jupiter/Venus {', '.join(jup_ven_in_2_3)} in 2nd or 3rd house).", "rule": "Ch. III Sl. 4-5"})
            score_adj += 15

    # House 4: Real Estate, Mother, Rain
    elif house_num == 4:
        # Ch VII Sloka 3 & 4 Rain Prediction
        ven_s = get_sign(chart.planets["Venus"]["longitude"])
        sat_s = get_sign(chart.planets["Saturn"]["longitude"])
        
        rel_to_moon = (ven_s - get_sign(moon_lon)) % 12 == 6 and (sat_s - get_sign(sun_lon)) % 12 == 6
        rel_to_lagna_4_8 = ven_s in [3, 7] and sat_s in [3, 7] # 4th and 8th
        rel_to_lagna_2_3 = ven_s in [1, 2] and sat_s in [1, 2] # 2nd and 3rd
        
        # VII-4: Benefics in 3, 2, 1, 4, 7, 10 in watery signs and bright half
        benefics_watery = False
        for h in [3, 2, 1, 4, 7, 10]:
            h_sign = (chart.lagna_sign + h - 1) % 12
            if h_sign in WATERY_SIGNS:
                if any(p in occupants(h) for p in benefics):
                    benefics_watery = True
                    break
        
        is_watery_lagna = chart.lagna_sign in WATERY_SIGNS
        
        if rel_to_moon or rel_to_lagna_4_8 or rel_to_lagna_2_3 or (benefics_watery and moon_diff < 180.0) or (is_watery_lagna and "Moon" in occupants(1)):
            predictions.append({
                "category": "Rain Prediction",
                "prediction": "Abundant rain is predicted (Auspicious weather/monsoon signs).",
                "rule": "Ch. VII Sl. 3-4"
            })
            score_adj += 20
        else:
            predictions.append({
                "category": "Rain Prediction",
                "prediction": "No immediate rain or dry/warm weather.",
                "rule": "Ch. VII Sl. 3-4"
            })

        # Rule 1: Adhyaya I Sloka 2 (Success or Prosperity / Hibuka significances)
        h4_sign = (chart.lagna_sign + 3) % 12
        h4_lord = SIGN_LORDS[h4_sign]
        h4_good = influences_sign(h4_lord, h4_sign) or any(influences_sign(p, h4_sign) for p in benefics)
        h4_pred = "Acquisition of houses / prosperity / success" if h4_good else "Decay of property / failure / loss"
        predictions.append({
            "category": "Property & Success",
            "prediction": h4_pred,
            "rule": "Ch. I Sl. 2"
        })
        details.append(f"Shatpanchasika Ch. I Sl. 2: 4th house (Hibuka) is aspected/occupied by its lord or a benefic: {h4_good}. Prediction: {h4_pred}.")
        if h4_good:
            score_adj += 15
        else:
            score_adj -= 15

    # House 5: Children, Pregnancy, Speculation
    elif house_num == 5:
        # Ch VII Sloka 1: Saturn in odd house -> boy, even house -> girl
        saturn_house = 1
        for h in range(1, 13):
            if "Saturn" in occupants(h):
                saturn_house = h
                break
        sat_boy = saturn_house in [3, 5, 7, 9, 11]
        
        # VII-5 child gender check
        lagna_varga_masc = (rising_nav_sign % 2) != 0
        lagna_varga_aspected_male = False
        for male_p in ["Sun", "Mars", "Jupiter"]:
            if aspects_sign(chart.planets[male_p]["longitude"], rising_nav_sign):
                lagna_varga_aspected_male = True
                break
                
        # Mercury in Lagna indicates pregnancy confirmation
        if "Mercury" in occupants(1):
            details.append("Shatpanchasika Ch. VII Sl. 5: Mercury is in the rising sign, confirming pregnancy (enceinte).")
            predictions.append({"category": "Pregnancy Status", "prediction": "Pregnancy confirmed.", "rule": "Ch. VII Sl. 5"})

        if (sat_boy or (lagna_varga_masc and lagna_varga_aspected_male)):
            predictions.append({"category": "Child Gender", "prediction": "Male child (Boy).", "rule": "Ch. VII Sl. 1, 5"})
        else:
            predictions.append({"category": "Child Gender", "prediction": "Female child (Girl).", "rule": "Ch. VII Sl. 1, 5"})

    # House 7: Marriage, Spouse, Partner, Traveler Return
    elif house_num == 7:
        # VII-1: Saturn in even house -> get bride, odd -> no
        saturn_house = 1
        for h in range(1, 13):
            if "Saturn" in occupants(h):
                saturn_house = h
                break
        get_bride = saturn_house in [2, 4, 6, 8, 10, 12]
        if get_bride:
            predictions.append({"category": "Marriage / Bride", "prediction": "Acquisition of a bride / partner is certain.", "rule": "Ch. VII Sl. 1"})
            score_adj += 15
        else:
            predictions.append({"category": "Marriage / Bride", "prediction": "Difficulties in finding a bride / partner.", "rule": "Ch. VII Sl. 1"})
            score_adj -= 10
            
        # VII-2 Marriage Yogas
        moon_h = 1
        for h in range(1, 13):
            if "Moon" in occupants(h):
                moon_h = h
                break
        if moon_h in [3, 5, 7, 11, 6]:
            aspects_all = True
            for p in ["Jupiter", "Sun", "Mercury"]:
                if not aspects_sign(chart.planets[p]["longitude"], get_sign(moon_lon)):
                    aspects_all = False
                    break
            if aspects_all:
                predictions.append({"category": "Marriage Timing", "prediction": "Marriage is confirmed and will take place soon.", "rule": "Ch. VII Sl. 2"})
                score_adj += 25

        # VII-10 Union partner type
        union_p = "unknown"
        if any(p in occupants(7) for p in ["Sun", "Venus", "Mars"]):
            union_p = "union with another man's wife / unavailable partner"
        elif "Jupiter" in occupants(7):
            union_p = "union with own wife / long-term partner"
        elif any(p in occupants(7) for p in ["Moon", "Mercury"]):
            union_p = "union with a courtezan / casual partner"
        elif "Saturn" in occupants(7):
            union_p = "union with a low-caste or forbidden woman"
            
        if union_p != "unknown":
            predictions.append({"category": "Union / Intimacy Details", "prediction": f"The query indicates {union_p}.", "rule": "Ch. VII Sl. 10"})

        # Rule 1: Adhyaya I Sloka 2 (Return from abroad / Jamitra significances)
        h7_sign = (chart.lagna_sign + 6) % 12
        h7_lord = SIGN_LORDS[h7_sign]
        h7_malefic = any(influences_sign(p, h7_sign) for p in malefics)
        h7_good = influences_sign(h7_lord, h7_sign) or any(influences_sign(p, h7_sign) for p in benefics)
        
        if h7_good:
            h7_pred = "Return of traveler from abroad / safe return soon"
            score_adj += 15
        elif h7_malefic:
            h7_pred = "No return from abroad / traveler remains in foreign place"
            score_adj -= 15
        else:
            h7_pred = "Traveler's return is delayed or uncertain"
            
        predictions.append({
            "category": "Traveler Return Status",
            "prediction": h7_pred,
            "rule": "Ch. I Sl. 2"
        })
        details.append(f"Shatpanchasika Ch. I Sl. 2: 7th house (Jamitra) has benefic influence: {h7_good}, malefic influence: {h7_malefic}. Prediction: {h7_pred}.")

        # Rule 3: Adhyaya V Slokas 1-5 (Absentee Return & Timing)
        all_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        planets_in_2_3_5 = all(any(p in occupants(h) for h in [2, 3, 5]) for p in all_planets)
        houses_2_3_5_have_benefics = (
            any(p in occupants(2) for p in benefics) and 
            any(p in occupants(3) for p in benefics) and 
            any(p in occupants(5) for p in benefics)
        )
        if planets_in_2_3_5 or houses_2_3_5_have_benefics:
            predictions.append({
                "category": "Traveler Return",
                "prediction": "Early return of the traveler from abroad (Condition: planets concentrated in 2nd, 3rd, and 5th houses).",
                "rule": "Adh. V Sl. 1"
            })
            score_adj += 20

        planet_in_6_7 = len(occupants(6)) > 0 or len(occupants(7)) > 0
        jupiter_in_kendra = any("Jupiter" in occupants(h) for h in [1, 4, 7, 10])
        merc_in_trikona = any("Mercury" in occupants(h) for h in [5, 9])
        ven_in_trikona = any("Venus" in occupants(h) for h in [5, 9])
        if (planet_in_6_7 and jupiter_in_kendra) or (merc_in_trikona and ven_in_trikona):
            predictions.append({
                "category": "Traveler Return",
                "prediction": "Quick return of the traveler home (Condition: planet in 6/7 with Jupiter in Kendra, or Mercury & Venus in Trikonas).",
                "rule": "Adh. V Sl. 2"
            })
            score_adj += 20

        moon_in_8 = "Moon" in occupants(8)
        malefics_in_kendra = any(any(p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"] for p in occupants(h)) for h in [1, 4, 7, 10])
        benefics_in_kendra = any(any(p in benefics for p in occupants(h)) for h in [1, 4, 7, 10])
        if moon_in_8 and not malefics_in_kendra:
            pred_txt = "Traveler returns home safely."
            if benefics_in_kendra:
                pred_txt += " Return will bring financial or material gain."
            predictions.append({
                "category": "Traveler Return",
                "prediction": pred_txt,
                "rule": "Adh. V Sl. 3"
            })
            score_adj += 20

        is_prishtodaya = chart.lagna_sign in [0, 1, 3, 8, 9]
        lagna_aspected_by_malefic = any(planet_aspects_house(p, 1) for p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"])
        if is_prishtodaya and lagna_aspected_by_malefic:
            predictions.append({
                "category": "Traveler Status",
                "prediction": "Traveler is subject to confinement, torture, or imprisonment.",
                "rule": "Adh. V Sl. 4"
            })
            score_adj -= 30
            
        malefics_in_3 = [p for p in occupants(3) if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]]
        benefics_aspect_3 = any(planet_aspects_house(p, 3) for p in benefics)
        if len(malefics_in_3) > 0 and not benefics_aspect_3:
            predictions.append({
                "category": "Traveler Status",
                "prediction": "Traveler has departed to a very distant foreign land.",
                "rule": "Adh. V Sl. 4"
            })
            score_adj -= 10
            
        malefics_in_6 = [p for p in occupants(6) if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]]
        if len(malefics_in_6) > 0:
            predictions.append({
                "category": "Traveler Status",
                "prediction": "Traveler is lost or dead.",
                "rule": "Adh. V Sl. 4"
            })
            score_adj -= 40
            
        malefics_in_kendra_any = any(any(p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"] for p in occupants(h)) for h in [1, 4, 7, 10])
        if malefics_in_kendra_any:
            predictions.append({
                "category": "Traveler Status",
                "prediction": "Traveler has been decoyed or captured by thieves.",
                "rule": "Adh. V Sl. 4"
            })
            score_adj -= 20

        physical_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        first_occupied_house = None
        for h in range(1, 13):
            occupants_h = [p for p in occupants(h) if p in physical_planets]
            if occupants_h:
                first_occupied_house = h
                break
        if first_occupied_house is not None:
            occupants_h = [p for p in occupants(first_occupied_house) if p in physical_planets]
            is_retro = any(chart.planets[p].get("is_retrograde", False) for p in occupants_h)
            if is_retro:
                timing_days = first_occupied_house
                timing_type = "Retrograde (direct count)"
            else:
                timing_days = first_occupied_house * 12
                timing_type = "Direct (multiplied by 12)"
                
            predictions.append({
                "category": "Traveler Return Timing",
                "prediction": f"Traveler will return in {timing_days} days (Based on first occupied house: {first_occupied_house}, planet movement: {timing_type}).",
                "rule": "Adh. V Sl. 5"
            })
            details.append(f"Shatpanchasika Adh. V Sl. 5: First occupied house is {first_occupied_house}. Planet is retrograde: {is_retro}. Return timing: {timing_days} days.")

        # Rule 5: Adhyaya VII Sloka 9 (Abroad Intentions & Travel)
        is_movable_lagna = (chart.lagna_sign % 3) == 0
        is_movable_nav = (rising_nav_sign % 3) == 0
        is_past_middle_nav = rising_nav_idx >= 5
        intends_travel = is_movable_lagna and is_movable_nav and is_past_middle_nav
        planets_in_6 = [p for p in occupants(6) if p in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]]
        
        travel_outcome = "No specific indication of travel or staying."
        if intends_travel:
            travel_outcome = "Querist intends to travel/go abroad."
            if planets_in_6:
                has_retro = any(chart.planets[p].get("is_retrograde", False) for p in planets_in_6)
                if has_retro:
                    travel_outcome += " Despite obstacles (planet in 6th), traveler still proceeds abroad due to retrograde motion."
                else:
                    travel_outcome += " Travel is dropped/cancelled due to direct planet in 6th house (fallen from 7th)."
            else:
                travel_outcome += " Travel is confirmed and will proceed."
        predictions.append({
            "category": "Travel Intentions",
            "prediction": travel_outcome,
            "rule": "Adh. VII Sl. 9"
        })
        details.append(f"Shatpanchasika Adh. VII Sl. 9: Travel prediction: {travel_outcome}.")

        # Adhyaya II Slokas 14-15 (Fighter return timing in months)
        strongest_p = get_strongest_planet(chart.planets, sun_lon)
        if strongest_p:
            strongest_p_house = 1
            for h in range(1, 13):
                if strongest_p in occupants(h):
                    strongest_p_house = h
                    break
            strong_p_lon = chart.planets[strongest_p]["longitude"]
            nav_sign, _ = get_navamsa_sign(strong_p_lon)
            nav_mobility = nav_sign % 3
            if nav_mobility == 0:
                return_months = strongest_p_house
            elif nav_mobility == 1:
                return_months = 2 * strongest_p_house
            else:
                return_months = 3 * strongest_p_house
                
            predictions.append({
                "category": "Fighter Return Timing",
                "prediction": f"Fighter returns within {return_months} months (Strongest planet {strongest_p} is in house {strongest_p_house}, Navamsa sign is {['movable', 'fixed', 'dual'][nav_mobility]}).",
                "rule": "Ch. II Sl. 14-15"
            })

        # Adhyaya II Sloka 16 (Retrograde return of fighter)
        h7_sign = (chart.lagna_sign + 6) % 12
        h7_lord = SIGN_LORDS[h7_sign]
        predictions.append({
            "category": "Fighter Return Timing",
            "prediction": f"Fighter returns when the 7th lord ({h7_lord}) begins retrograde motion.",
            "rule": "Ch. II Sl. 16"
        })

        # Adhyaya II Sloka 17 (Enemy arrival timing in days and intervening planet check)
        moon_h = 1
        for h in range(1, 13):
            if "Moon" in occupants(h):
                moon_h = h
                break
        
        planet_between = False
        if moon_h > 2:
            for h in range(2, moon_h):
                occ_h = [p for p in occupants(h) if p not in ["Rahu", "Ketu"]]
                if occ_h:
                    planet_between = True
                    break
                    
        if not planet_between:
            predictions.append({
                "category": "Fighter Arrival Timing",
                "prediction": f"Fighter/enemy arrives within {moon_h} days.",
                "rule": "Ch. II Sl. 17"
            })
        else:
            predictions.append({
                "category": "Fighter Arrival Timing",
                "prediction": "Fighter/enemy will not arrive (Planet between Lagna and Moon).",
                "rule": "Ch. II Sl. 17"
            })

    # House 8: Recovery of Stolen Goods, Death
    elif house_num == 8:
        # VI-1: Insider vs Outsider theft
        is_fixed_lagna = chart.lagna_sign in [1, 4, 7, 10]
        is_fixed_nav = rising_nav_sign in [1, 4, 7, 10]
        is_vargottama = chart.lagna_sign == rising_nav_sign
        
        if is_fixed_lagna or is_fixed_nav or is_vargottama:
            theft_type = "Stolen by an insider; property is still inside the house/premises."
            score_adj += 20
        else:
            theft_type = "Stolen by an outsider; property has been removed far from the premises."
            score_adj -= 10
            
        predictions.append({"category": "Theft / Lost Property", "prediction": theft_type, "rule": "Ch. VI Sl. 1"})

        # VI-2 Location of property inside house
        drekkana_idx = int((chart.lagna_sidereal % 30) / 10.0)
        locs = {0: "Near the gate / entrance", 1: "Middle of the house", 2: "Backyard / West area"}
        predictions.append({
            "category": "Theft / Lost Property Location",
            "prediction": f"Location: {locs.get(drekkana_idx, 'unknown')}.",
            "rule": "Ch. VI Sl. 2"
        })

        # Rule 2: Adhyaya I Sloka 5 vs Chapter VI Sloka 3 (Lost Article Recovery)
        full_moon_lagna = is_moon_full and "Moon" in occupants(1)
        aspected_by_jup_or_ven = planet_aspects_house("Jupiter", 1) or planet_aspects_house("Venus", 1)
        benefic_in_11 = any(p in occupants(11) for p in benefics)
        
        recovery_adh1_sl5 = (full_moon_lagna and aspected_by_jup_or_ven) or benefic_in_11
        
        has_benefic_occupant = any(p in occupants(1) for p in benefics)
        has_benefic_aspect = any(planet_aspects_house(p, 1) for p in benefics)
        occupied_and_aspected_by_benefics = has_benefic_occupant and has_benefic_aspect
        
        recovery_ch6_sl3 = full_moon_lagna or (is_seershodaya and occupied_and_aspected_by_benefics) or benefic_in_11
        
        if recovery_adh1_sl5:
            predictions.append({
                "category": "Property Recovery (Adh I Sl 5)",
                "prediction": "Lost property will be recovered / returned (Condition: Full Moon in Lagna aspected by Jupiter/Venus, or benefic in 11th).",
                "rule": "Adh. I Sl. 5"
            })
            score_adj += 20
        else:
            predictions.append({
                "category": "Property Recovery (Adh I Sl 5)",
                "prediction": "No recovery indicated under Adh. I Sl. 5 conditions.",
                "rule": "Adh. I Sl. 5"
            })
            
        if recovery_ch6_sl3:
            predictions.append({
                "category": "Property Recovery (Ch VI Sl 3)",
                "prediction": "Lost property will be recovered very soon (Condition: Full Moon in Lagna, or Sirshodaya Lagna with benefic presence/aspect, or benefic in 11th).",
                "rule": "Ch. VI Sl. 3"
            })
            score_adj += 20
        else:
            predictions.append({
                "category": "Property Recovery (Ch VI Sl 3)",
                "prediction": "Recovery of stolen property is unlikely soon under Ch. VI Sl. 3 conditions.",
                "rule": "Ch. VI Sl. 3"
            })

        # Rule 4: Theft Direction & Distance (Ch. VI Sloka 4 correction)
        kendra_occupants = []
        for h in [1, 4, 7, 10]:
            kendra_occupants.extend(occupants(h))
            
        stolen_dir = "Unknown"
        dir_ref_planet = None
        
        if kendra_occupants:
            strong_k = get_strongest_planet({p: chart.planets[p] for p in kendra_occupants}, sun_lon)
            if strong_k:
                dir_ref_planet = strong_k
                dir_map = {
                    "Sun": "East",
                    "Venus": "South-East",
                    "Mars": "South",
                    "Rahu": "South-West",
                    "Saturn": "West",
                    "Moon": "North-West",
                    "Mercury": "North",
                    "Jupiter": "North-East"
                }
                stolen_dir = dir_map.get(strong_k, "Unknown")
                
        if stolen_dir == "Unknown":
            # Fallback to Lagna sign triplicity
            triplicity_dirs = {
                0: "East", 4: "East", 8: "East",
                1: "South", 5: "South", 9: "South",
                2: "West", 6: "West", 10: "West",
                3: "North", 7: "North", 11: "North"
            }
            stolen_dir = triplicity_dirs.get(chart.lagna_sign, "Unknown")
            
        # Distance calculation
        if rising_nav_idx <= 4:
            yojanas = 0
        else:
            yojanas = rising_nav_idx - 4
            
        predictions.append({
            "category": "Theft Direction & Distance",
            "prediction": f"Property taken to the {stolen_dir} ({'based on planet ' + dir_ref_planet if dir_ref_planet else 'based on Lagna sign triplicity'}), approximately {yojanas} Yojana(s) away.",
            "rule": "Ch. VI Sl. 4"
        })
        details.append(f"Shatpanchasika Ch. VI Sl. 4: Kendra occupants: {kendra_occupants}. Strongest in Kendra: {dir_ref_planet}. Lagna sign: {chart.lagna_sign}. Rising Navamsa idx: {rising_nav_idx}. Stolen direction: {stolen_dir}. Distance: {yojanas} Yojanas.")

        # VI-5 Thief profile
        lagnapathi_planet = chart.lagnapathi
        ages = {
            "Sun": "Old (about 70 years old)",
            "Moon": "Boy/Girl (about 4-5 years old)",
            "Mars": "Young (about 8-9 years old)",
            "Mercury": "Celibate youth (about 12 years old)",
            "Jupiter": "Middle-aged (about 50 years old)",
            "Venus": "Adolescent (about 32 years old)",
            "Saturn": "Very old (about 80 years old)"
        }
        castes = {
            "Jupiter": "Brahmin", "Venus": "Brahmin",
            "Mars": "Kshatriya", "Sun": "Kshatriya",
            "Moon": "Vaisya",
            "Mercury": "Sudra",
            "Saturn": "Hybrid / Outcaste (Chandala)"
        }
        thief_age = ages.get(lagnapathi_planet, "Young adult")
        thief_caste = castes.get(lagnapathi_planet, "Unknown")
        predictions.append({
            "category": "Thief Profile",
            "prediction": f"Age of Thief: {thief_age}. Caste/Class: {thief_caste}.",
            "rule": "Ch. VI Sl. 5"
        })

        # Ch VII Sloka 11: Saturn in 8th conjoined with malefic -> death of traveler
        saturn_h = 1
        for h in range(1, 13):
            if "Saturn" in occupants(h):
                saturn_h = h
                break
        if saturn_h == 8:
            has_malefic = any(p in occupants(8) for p in ["Sun", "Mars"])
            has_benefic_aspect = False
            for b in ["Jupiter", "Venus", "Mercury"]:
                if aspects_sign(chart.planets[b]["longitude"], (chart.lagna_sign+7)%12):
                    has_benefic_aspect = True
                    break
            if has_malefic and not has_benefic_aspect:
                predictions.append({"category": "Traveler Danger", "prediction": "Critical: The traveler will die abroad.", "rule": "Ch. VII Sl. 11"})
                score_adj -= 40

        # Adhyaya VII Sloka 12 (Father's location)
        sun_in_8 = "Sun" in occupants(8)
        benefics_in_8 = [p for p in occupants(8) if p in benefics]
        aspected_by_benefic = any(aspects_sign(chart.planets[b]["longitude"], (chart.lagna_sign + 7) % 12) for b in benefics)
        
        if sun_in_8 and (benefics_in_8 or aspected_by_benefic):
            predictions.append({
                "category": "Father's Location",
                "prediction": "The father has quitted the foreign country and gone to another country.",
                "rule": "Ch. VII Sl. 12"
            })
            score_adj += 10
        elif sun_in_8:
            predictions.append({
                "category": "Father's Location",
                "prediction": "The father remains in the same foreign country/place (Sun in 8th without benefic conjunction/aspect).",
                "rule": "Ch. VII Sl. 12"
            })

    # House 9: Faith, Fortune, Sickness Abroad
    elif house_num == 9:
        # Ch VII Sloka 11: Saturn + malefic in 9th -> sickness
        saturn_h = 1
        for h in range(1, 13):
            if "Saturn" in occupants(h):
                saturn_h = h
                break
        if saturn_h == 9:
            has_malefic = any(p in occupants(9) for p in ["Sun", "Mars"])
            has_benefic_aspect = False
            for b in ["Jupiter", "Venus", "Mercury"]:
                if aspects_sign(chart.planets[b]["longitude"], (chart.lagna_sign+8)%12):
                    has_benefic_aspect = True
                    break
            if has_malefic and not has_benefic_aspect:
                predictions.append({"category": "Traveler Health", "prediction": "The traveler is suffering from severe illness in a foreign place.", "rule": "Ch. VII Sl. 11"})
                score_adj -= 20

        # Rule 5: Adhyaya VII Sloka 9 (Abroad Intentions & Travel)
        is_movable_lagna = (chart.lagna_sign % 3) == 0
        is_movable_nav = (rising_nav_sign % 3) == 0
        is_past_middle_nav = rising_nav_idx >= 5
        intends_travel = is_movable_lagna and is_movable_nav and is_past_middle_nav
        planets_in_6 = [p for p in occupants(6) if p in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]]
        
        travel_outcome = "No specific indication of travel or staying."
        if intends_travel:
            travel_outcome = "Querist intends to travel/go abroad."
            if planets_in_6:
                has_retro = any(chart.planets[p].get("is_retrograde", False) for p in planets_in_6)
                if has_retro:
                    travel_outcome += " Despite obstacles (planet in 6th), traveler still proceeds abroad due to retrograde motion."
                else:
                    travel_outcome += " Travel is dropped/cancelled due to direct planet in 6th house (fallen from 7th)."
            else:
                travel_outcome += " Travel is confirmed and will proceed."
        predictions.append({
            "category": "Travel Intentions",
            "prediction": travel_outcome,
            "rule": "Adh. VII Sl. 9"
        })

        # Adhyaya VII Sloka 12 (Father's location)
        sun_in_8 = "Sun" in occupants(8)
        benefics_in_8 = [p for p in occupants(8) if p in benefics]
        aspected_by_benefic = any(aspects_sign(chart.planets[b]["longitude"], (chart.lagna_sign + 7) % 12) for b in benefics)
        
        if sun_in_8 and (benefics_in_8 or aspected_by_benefic):
            predictions.append({
                "category": "Father's Location",
                "prediction": "The father has quitted the foreign country and gone to another country.",
                "rule": "Ch. VII Sl. 12"
            })
            score_adj += 10
        elif sun_in_8:
            predictions.append({
                "category": "Father's Location",
                "prediction": "The father remains in the same foreign country/place (Sun in 8th without benefic conjunction/aspect).",
                "rule": "Ch. VII Sl. 12"
            })

    # House 10: Absence from Home
    elif house_num == 10:
        # Rule 1: Adhyaya I Sloka 2 (Absence from home / Karma significances)
        h10_sign = (chart.lagna_sign + 9) % 12
        h10_lord = SIGN_LORDS[h10_sign]
        h10_movable = h10_sign % 3 == 0
        h10_malefic = any(influences_sign(p, h10_sign) for p in malefics)
        h10_good = influences_sign(h10_lord, h10_sign) or any(influences_sign(p, h10_sign) for p in benefics)
        
        if h10_movable and h10_malefic:
            h10_pred = "Absence from home / traveler stays away"
            score_adj -= 15
        elif h10_good:
            h10_pred = "No absence / traveler returns or remains at home"
            score_adj += 15
        else:
            h10_pred = "Uncertainty regarding absence/stay at home"
            
        predictions.append({
            "category": "Absence Status",
            "prediction": h10_pred,
            "rule": "Ch. I Sl. 2"
        })
        details.append(f"Shatpanchasika Ch. I Sl. 2: 10th house (Karma) is movable: {h10_movable}, has malefic influence: {h10_malefic}, benefic influence: {h10_good}. Prediction: {h10_pred}.")

    # House 11: Desires, Realization
    elif house_num == 11:
        # Ch IV Sloka 1: Benefics in Kendras & Trikonas, malefics not in Kendra/8th -> fulfillment
        benefics_in_kendra_trikona = True
        for h in [1, 4, 7, 10, 5, 9]:
            if not any(p in occupants(h) for p in benefics):
                benefics_in_kendra_trikona = False
                break
        malefics_in_kendra_8 = False
        for h in [1, 4, 7, 10, 8]:
            if any(p in occupants(h) for p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]):
                malefics_in_kendra_8 = True
                break
                
        if benefics_in_kendra_trikona and not malefics_in_kendra_8:
            predictions.append({"category": "Wishes Realization", "prediction": "Your wishes and desires will be fully realized.", "rule": "Ch. IV Sl. 1"})
            score_adj += 30
        else:
            predictions.append({"category": "Wishes Realization", "prediction": "Desires will face delay or mixed results.", "rule": "Ch. IV Sl. 1"})

        # Adhyaya IV Sloka 2 (Advancement of desires)
        benefics_in_3_5_7_11 = []
        malefics_in_3_5_7_11 = []
        for h in [3, 5, 7, 11]:
            for p in occupants(h):
                if p in benefics:
                    benefics_in_3_5_7_11.append(f"{p} in {h}th")
                elif p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]:
                    malefics_in_3_5_7_11.append(f"{p} in {h}th")
                    
        if benefics_in_3_5_7_11:
            pred_txt = f"Great gain and accomplishment of desired objects (Benefic present: {', '.join(benefics_in_3_5_7_11)})."
            lagna_is_biped = chart.lagna_sign in [2, 5, 6, 8, 10]
            benefic_in_lagna_11 = any(p in occupants(1) for p in benefics)
            if lagna_is_biped and benefic_in_lagna_11:
                pred_txt += " Highly favorable as Lagna is a biped sign with a benefic occupant."
                score_adj += 10
            predictions.append({"category": "Realization of Desires", "prediction": pred_txt, "rule": "Ch. IV Sl. 2"})
            score_adj += 15
        elif malefics_in_3_5_7_11:
            predictions.append({"category": "Realization of Desires", "prediction": f"Loss and failure to realize desires (Malefic present: {', '.join(malefics_in_3_5_7_11)}).", "rule": "Ch. IV Sl. 2"})
            score_adj -= 15

        # Adhyaya IV Slokas 3-4 (Position and wealth)
        h10_benefics = [p for p in occupants(10) if p in benefics]
        h7_benefics = [p for p in occupants(7) if p in benefics]
        if h10_benefics or h7_benefics:
            p_names = h10_benefics + h7_benefics
            predictions.append({"category": "Realization of Desires", "prediction": f"Acquisition of position, appointment, or honor (Benefic {', '.join(p_names)} in 10th or 7th).", "rule": "Ch. IV Sl. 3-4"})
            score_adj += 15
            
        h1_benefics = [p for p in occupants(1) if p in benefics]
        h2_benefics = [p for p in occupants(2) if p in benefics]
        h5_benefics = [p for p in occupants(5) if p in benefics]
        if h1_benefics or h2_benefics or h5_benefics:
            p_names = h1_benefics + h2_benefics + h5_benefics
            predictions.append({"category": "Realization of Desires", "prediction": f"Honor and wealth are indicated (Benefic {', '.join(p_names)} in 1st, 2nd, or 5th).", "rule": "Ch. IV Sl. 3-4"})
            score_adj += 15
            
        h12_malefics = [p for p in occupants(12) if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]]
        h11_malefics = [p for p in occupants(11) if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]]
        if h12_malefics or h11_malefics:
            predictions.append({"category": "Realization of Desires", "prediction": "Desires are unproductive or delayed (Malefic in 12th or 11th).", "rule": "Ch. IV Sl. 3-4"})
            score_adj -= 10
            
        if "Moon" in occupants(10):
            predictions.append({"category": "Realization of Desires", "prediction": "Auspicious outcome and realization of desires (Moon in the 10th house).", "rule": "Ch. IV Sl. 3-4"})
            score_adj += 15
            
        moon_house_num = None
        for h in [2, 3, 6, 7, 10, 11]:
            if "Moon" in occupants(h):
                moon_house_num = h
                break
        if moon_house_num is not None:
            if aspects_sign(chart.planets["Jupiter"]["longitude"], get_sign(moon_lon)):
                predictions.append({"category": "Gain Source", "prediction": f"Gain through women (Moon in {moon_house_num}th aspected by Jupiter).", "rule": "Ch. IV Sl. 3-4"})
                score_adj += 10
                
        malefics_1_3_5_8_9 = []
        for h in [1, 3, 5, 8, 9]:
            for p in occupants(h):
                if p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]:
                    malefics_1_3_5_8_9.append(f"{p} in {h}th")
        if malefics_1_3_5_8_9:
            predictions.append({"category": "Realization of Desires", "prediction": f"Failure, loss, or fear (Malefic present: {', '.join(malefics_1_3_5_8_9)}).", "rule": "Ch. IV Sl. 3-4"})
            score_adj -= 15

    return {
        "score_adjustment": score_adj,
        "details": details,
        "predictions": predictions
    }
