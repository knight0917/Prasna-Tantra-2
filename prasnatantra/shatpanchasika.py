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

    # Helper: occupants of a sign relative to Lagna
    def occupants(h_num):
        target_s = (chart.lagna_sign + h_num - 1) % 12
        return [p for p, data in chart.planets.items() if get_sign(data["longitude"]) == target_s]

    # Helper: planet aspects a specific house
    def planet_aspects_house(planet_name, h_num):
        target_s = (chart.lagna_sign + h_num - 1) % 12
        return aspects_sign(chart.planets[planet_name]["longitude"], target_s)

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

    # 2. House-specific evaluations
    # House 1: Health, Body, Undertakings, Thought reading
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

    # House 4: Real Estate, Mother, Rain
    elif house_num == 4:
        # Ch VII Sloka 3 & 4 Rain Prediction
        # VII-3: Venus and Saturn in 7th from Moon/Sun, or 4th/8th from Lagna, or 2nd/3rd
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
        # Moon in 3, 5, 7, 11, 6 aspected by Jup, Sun, Merc -> marriage happens
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

        # Ch V absent traveler return
        if "Moon" in occupants(8):
            malefic_in_kendra = False
            for h in [1, 4, 7, 10]:
                if any(p in occupants(h) for p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]):
                    malefic_in_kendra = True
                    break
            if not malefic_in_kendra:
                predictions.append({"category": "Traveler Return", "prediction": "Safe return of traveler.", "rule": "Ch. V Sl. 3"})
                score_adj += 20

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

        # VI-3 Recovery Soon indicators
        full_moon_lagna = is_moon_full and "Moon" in occupants(1)
        seershodaya_lagna_benefics = is_seershodaya and any(p in occupants(1) for p in benefics)
        benefic_in_11 = any(p in occupants(11) for p in benefics)
        
        if full_moon_lagna or seershodaya_lagna_benefics or benefic_in_11:
            predictions.append({"category": "Property Recovery", "prediction": "Recovery of the lost property will happen very soon.", "rule": "Ch. VI Sl. 3"})
            score_adj += 30
        else:
            predictions.append({"category": "Property Recovery", "prediction": "Recovery is unlikely or will take a long time.", "rule": "Ch. VI Sl. 3"})

        # VI-4 Direction of stolen item
        # Planet in Kendra check
        kendra_occupants = []
        for h in [1, 4, 7, 10]:
            kendra_occupants.extend(occupants(h))
        # strongest in Kendra
        dir_ref_sign = chart.lagna_sign
        if kendra_occupants:
            strong_k = get_strongest_planet({p: chart.planets[p] for p in kendra_occupants}, sun_lon)
            if strong_k:
                dir_ref_sign = get_sign(chart.planets[strong_k]["longitude"])
        
        directions = {
            0: "East", 4: "East", 8: "East",
            1: "South", 5: "South", 9: "South",
            2: "West", 6: "West", 10: "West",
            3: "North", 7: "North", 11: "North"
        }
        stolen_dir = directions.get(dir_ref_sign, "Unknown")
        
        # Distance in Yojanas (Navamsas passed from 5th Navamsa)
        # Navamsas are 0-indexed, so 5th Navamsa has index 4
        yojanas = max(1, abs(rising_nav_idx - 4))
        predictions.append({
            "category": "Theft Direction & Distance",
            "prediction": f"Property taken to the {stolen_dir}, approximately {yojanas} Yojana(s) away.",
            "rule": "Ch. VI Sl. 4"
        })

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

    return {
        "score_adjustment": score_adj,
        "details": details,
        "predictions": predictions
    }
