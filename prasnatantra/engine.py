from datetime import datetime, timedelta
from .astronomy import calculate_lagna, get_planetary_positions, get_house_cusps, get_sign_name
from .tajaka import get_planet_relationship, detect_nakta_yoga, detect_yamaya_yoga, detect_kamboola_yoga, get_planetary_avastha, check_combustion
from .shatpanchasika import evaluate_shatpanchasika
from .special_rules import (
    evaluate_deity_curse,
    evaluate_master_servant,
    evaluate_meals,
    evaluate_sports,
    evaluate_disputes,
    evaluate_crops_trade
)

# Traditional Vedic Sign Ownership
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

# Sirshodaya Rasis (signs rising by head - highly favorable)
SIRSHODAYA_SIGNS = [2, 4, 5, 6, 7, 10]  # Gemini, Leo, Virgo, Libra, Scorpio, Aquarius

class PrasnaChart:
    def __init__(self, local_datetime, lat_str, lon_str, tz_offset_hours):
        """
        local_datetime: datetime object
        lat_str: Latitude, e.g. "12:58:18"
        lon_str: Longitude, e.g. "77:35:41"
        tz_offset_hours: float (e.g. 5.5 for IST)
        """
        self.local_time = local_datetime
        # Calculate UTC time
        self.utc_time = local_datetime - timedelta(hours=tz_offset_hours)
        self.utc_str = self.utc_time.strftime("%Y/%m/%d %H:%M:%S")
        
        self.latitude = lat_str
        self.longitude = lon_str
        self.tz_offset = tz_offset_hours
        
        # 1. Calculate Lagna & Astronomy
        lagna_data = calculate_lagna(self.utc_str, lat_str, lon_str)
        self.lagna_sidereal = lagna_data["sidereal"]
        self.lagna_tropical = lagna_data["tropical"]
        self.ayanamsha = lagna_data["ayanamsha"]
        self.lst = lagna_data["lst"]
        
        # 2. Get house cusps (Whole Sign)
        self.houses = get_house_cusps(self.lagna_sidereal)
        self.lagna_sign = self.houses[1]["sign"]
        self.lagnapathi = SIGN_LORDS[self.lagna_sign]
        
        # 3. Get planetary positions
        self.planets = get_planetary_positions(self.utc_str, self.ayanamsha)
        
        # 4. Check sincerity
        self.sincerity = self._check_sincerity()

    def _check_sincerity(self, ref_sign=None):
        """
        Evaluates the query's sincerity based on Tajaka rules relative to a reference sign.
        """
        if ref_sign is None:
            ref_sign = self.lagna_sign
            
        lagna_lord = SIGN_LORDS[ref_sign]
        seventh_lord = SIGN_LORDS[(ref_sign + 6) % 12]
        
        reasons_insincere = []
        reasons_sincere = []
        
        # Quadrants relative to ref_sign
        quadrants = [
            ref_sign, 
            (ref_sign + 3) % 12, 
            (ref_sign + 6) % 12, 
            (ref_sign + 9) % 12
        ]
        
        # Rule a: Moon conjoining reference sign, Saturn in a quadrant, Mercury combust
        moon_in_lagna = get_sign(self.planets["Moon"]["longitude"]) == ref_sign
        sat_in_quadrant = get_sign(self.planets["Saturn"]["longitude"]) in quadrants
        merc_combust = abs(self.planets["Mercury"]["longitude"] - self.planets["Sun"]["longitude"]) % 360 <= 8.0
        
        if moon_in_lagna and sat_in_quadrant and merc_combust:
            reasons_insincere.append("Moon conjoins reference sign, Saturn in quadrant, and Mercury combust.")
            
        # Rule b: Mars and Mercury aspect Moon conjoining reference sign
        rel_mars_moon = get_planet_relationship("Mars", self.planets["Mars"], "Moon", self.planets["Moon"])
        rel_merc_moon = get_planet_relationship("Mercury", self.planets["Mercury"], "Moon", self.planets["Moon"])
        if moon_in_lagna and rel_mars_moon and rel_merc_moon:
            reasons_insincere.append("Mars and Mercury aspect the Moon conjoining reference sign.")
            
        # Rule c: Malefic conjoins reference sign (without benefic aspect)
        malefics_in_lagna = []
        for p in ["Sun", "Mars", "Saturn"]:
            if get_sign(self.planets[p]["longitude"]) == ref_sign:
                malefics_in_lagna.append(p)
        if malefics_in_lagna:
            reasons_insincere.append(f"Malefics conjoin reference sign: {', '.join(malefics_in_lagna)}")
            
        # Rule d: Jupiter or Mercury cast inimical glance on lord of 7th (from reference sign)
        rel_jup_7 = get_planet_relationship("Jupiter", self.planets["Jupiter"], seventh_lord, self.planets[seventh_lord])
        rel_merc_7 = get_planet_relationship("Mercury", self.planets["Mercury"], seventh_lord, self.planets[seventh_lord])
        if rel_jup_7 and not rel_jup_7["is_friendly"]:
            reasons_insincere.append(f"Jupiter casts a hostile aspect on the 7th lord ({seventh_lord}).")
        if rel_merc_7 and not rel_merc_7["is_friendly"]:
            reasons_insincere.append(f"Mercury casts a hostile aspect on the 7th lord ({seventh_lord}).")
            
        # Sincere indicators
        # indicator a: Benefic conjoins reference sign
        benefics_in_lagna = []
        for p in ["Jupiter", "Venus", "Mercury", "Moon"]:
            if get_sign(self.planets[p]["longitude"]) == ref_sign:
                # Mercury must not be combust to be benefic
                if p == "Mercury" and merc_combust:
                    continue
                benefics_in_lagna.append(p)
        if benefics_in_lagna:
            reasons_sincere.append(f"Benefics conjoin reference sign: {', '.join(benefics_in_lagna)}")
            
        # indicator b: Mars or Full Moon and Jupiter aspect reference sign
        # Using a simplified aspect on the sign longitude
        ref_lon = ref_sign * 30.0 + 15.0
        for p in ["Mars", "Moon", "Jupiter"]:
            rel = get_planet_relationship(p, self.planets[p], "Lagna", {"longitude": ref_lon, "speed": 0.0})
            if rel and rel["is_friendly"]:
                reasons_sincere.append(f"{p} aspects the reference sign favorably.")
                
        # indicator c: Jupiter or Mercury throws friendly aspect on lord of 7th (from reference sign)
        if rel_jup_7 and rel_jup_7["is_friendly"]:
            reasons_sincere.append(f"Jupiter throws a friendly aspect on the 7th lord ({seventh_lord}).")
        if rel_merc_7 and rel_merc_7["is_friendly"]:
            reasons_sincere.append(f"Mercury throws a friendly aspect on the 7th lord ({seventh_lord}).")
            
        is_sincere = len(reasons_insincere) <= len(reasons_sincere)
        
        return {
            "is_sincere": is_sincere,
            "reasons_insincere": reasons_insincere,
            "reasons_sincere": reasons_sincere
        }

    def evaluate_query(self, house_num, query_num=1, special_category=None):
        """
        Evaluates a query corresponding to a specific house.
        house_num: 1 to 12
        query_num: 1 to 5 (sequential query number for multiple queries)
        special_category: string (optional, e.g. "deity_curse", "sports")
        """
        if house_num < 1 or house_num > 12:
            raise ValueError("House number must be between 1 and 12.")
            
        # Determine the reference "Lagna" point based on the query number
        if query_num == 1:
            ref_sign = self.lagna_sign
            ref_point_name = "Ascendant (Lagna)"
        elif query_num == 2:
            ref_sign = get_sign(self.planets["Moon"]["longitude"])
            ref_point_name = "Moon"
        elif query_num == 3:
            ref_sign = get_sign(self.planets["Sun"]["longitude"])
            ref_point_name = "Sun"
        elif query_num == 4:
            ref_sign = get_sign(self.planets["Jupiter"]["longitude"])
            ref_point_name = "Jupiter"
        else:
            # 5th query onwards: stronger between Mercury and Venus
            merc_lon = self.planets["Mercury"]["longitude"]
            ven_lon = self.planets["Venus"]["longitude"]
            merc_sign = get_sign(merc_lon)
            ven_sign = get_sign(ven_lon)
            
            # Simple strength rank based on Avastha
            merc_avastha = get_planetary_avastha("Mercury", merc_lon, self.planets["Mercury"], self.planets["Sun"]["longitude"], self.planets)
            ven_avastha = get_planetary_avastha("Venus", ven_lon, self.planets["Venus"], self.planets["Sun"]["longitude"], self.planets)
            
            avastha_ranks = {
                "Deeptha": 9,
                "Athiveerya": 8,
                "Suveerya": 7,
                "Swastha": 6,
                "Muditha": 5,
                "Neutral": 4,
                "Pariheena": 3,
                "Suptha": 2,
                "Nipeeditha": 1,
                "Deena": 0,
                "Mushita": -1
            }
            
            merc_rank = avastha_ranks.get(merc_avastha, 4)
            ven_rank = avastha_ranks.get(ven_avastha, 4)
            
            if ven_rank >= merc_rank:
                ref_sign = ven_sign
                ref_point_name = "Venus (stronger)"
            else:
                ref_sign = merc_sign
                ref_point_name = "Mercury (stronger)"
                
        lagnapathi = SIGN_LORDS[ref_sign]
        merc_combust = abs(self.planets["Mercury"]["longitude"] - self.planets["Sun"]["longitude"]) % 360 <= 8.0
        
        # Calculate the query sign and Karyesa relative to this reference sign
        query_sign = (ref_sign + house_num - 1) % 12
        karyesa = SIGN_LORDS[query_sign]
        
        # Calculate query-specific sincerity
        sinc_res = self._check_sincerity(ref_sign=ref_sign)
        
        evaluation = {
            "house": house_num,
            "query_num": query_num,
            "ref_point_name": ref_point_name,
            "ref_sign_name": get_sign_name(ref_sign),
            "query_sign_name": get_sign_name(query_sign),
            "lagnapathi": lagnapathi,
            "karyesa": karyesa,
            "direct_relationship": None,
            "yogas": [],
            "success_probability": "Medium",
            "score_pct": 50,
            "timing": "Immediate / Self-realization",
            "details": [],
            "shatpanchasika_predictions": [],
            "sincerity": sinc_res
        }
        
        # 1. Check if Lagnapathi and Karyesa are the same planet
        if lagnapathi == karyesa:
            evaluation["success_probability"] = "Very High"
            evaluation["score_pct"] = 100
            evaluation["details"].append("Lagnapathi and Karyesa are the same planet (Self-realization).")
            sp_res = evaluate_shatpanchasika(self, house_num)
            evaluation["shatpanchasika_predictions"] = sp_res["predictions"]
            evaluation["details"].extend(sp_res["details"])
            
            # Incorporate special horary rules (Prasna Tantra Ch. III)
            active_cat = special_category
            if not active_cat:
                if house_num == 12: active_cat = "deity_curse"
                elif house_num == 6: active_cat = "master_servant"
                elif house_num == 4: active_cat = "crops_trade"
                elif house_num == 8: active_cat = "disputes"
            if active_cat:
                if active_cat == "deity_curse": sp_rules_res = evaluate_deity_curse(self)
                elif active_cat == "master_servant": sp_rules_res = evaluate_master_servant(self)
                elif active_cat == "meals": sp_rules_res = evaluate_meals(self)
                elif active_cat == "sports": sp_rules_res = evaluate_sports(self)
                elif active_cat == "disputes": sp_rules_res = evaluate_disputes(self)
                elif active_cat == "crops_trade": sp_rules_res = evaluate_crops_trade(self, house_num)
                else: sp_rules_res = None
                
                if sp_rules_res:
                    evaluation["shatpanchasika_predictions"].extend(sp_rules_res["predictions"])
                    evaluation["details"].extend(sp_rules_res["details"])
            return evaluation
            
        # 2. Check direct relationship
        rel = get_planet_relationship(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa])
        evaluation["direct_relationship"] = rel
        
        # 3. Check for Yogas
        moon_data = self.planets["Moon"]
        kamboola = detect_kamboola_yoga(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa], moon_data)
        if kamboola:
            evaluation["yogas"].append({"name": "Kamboola Yoga", "details": kamboola})
            
        nakta = detect_nakta_yoga(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa], self.planets)
        if nakta:
            evaluation["yogas"].append({"name": "Nakta Yoga", "details": nakta})
            
        yamaya = detect_yamaya_yoga(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa], self.planets)
        if yamaya:
            evaluation["yogas"].append({"name": "Yamaya Yoga", "details": yamaya})
            
        # 4. Calculate Success Score
        score = 0
        
        # Base aspect logic
        if rel:
            if rel["aspect_type"] == "Conjunction":
                p1_malefic = lagnapathi in ["Sun", "Mars", "Saturn"]
                p2_malefic = karyesa in ["Sun", "Mars", "Saturn"]
                if p1_malefic or p2_malefic:
                    score += 20
                    evaluation["details"].append(f"Applying conjunction ({rel['aspect_type']}) between Lagnapathi and Karyesa (Mixed results due to malefic presence).")
                else:
                    score += 45
                    evaluation["details"].append(f"Applying benefic conjunction ({rel['aspect_type']}) between Lagnapathi and Karyesa (Highly favorable).")
            elif rel["is_applying"]:
                if rel["is_friendly"]:
                    score += 50
                    evaluation["details"].append(f"Applying friendly aspect ({rel['aspect_type']}) between Lagnapathi and Karyesa.")
                else:
                    score += 20
                    evaluation["details"].append(f"Applying hostile aspect ({rel['aspect_type']}) between Lagnapathi and Karyesa (Success with obstacles).")
            else:
                score -= 20
                evaluation["details"].append(f"Separating aspect ({rel['aspect_type']}) between Lagnapathi and Karyesa (Easarapha Yoga - Failure).")
        else:
            evaluation["details"].append("No direct aspect between Lagnapathi and Karyesa.")
            
        # Yoga additions
        if kamboola:
            score += 30
            evaluation["details"].append("Kamboola Yoga present: Moon translates strength and coordinates the outcome.")
        if nakta:
            score += 20
            evaluation["details"].append(f"Nakta Yoga present: achieved through the mediation of {nakta[0]['translator']}.")
        if yamaya:
            score += 15
            evaluation["details"].append(f"Yamaya Yoga present: achieved through the authority/mediation of {yamaya[0]['translator']}.")
            
        # Check specific Prasna Tantra rules from the book
        # Rule 1: Lagnapathi aspects Ascendant (ref_sign) and Karyesa aspects target house (query_sign)
        lagnapathi_lon = self.planets[lagnapathi]["longitude"]
        karyesa_lon = self.planets[karyesa]["longitude"]
        moon_lon = self.planets["Moon"]["longitude"]
        
        lagnapathi_aspects_ref = aspects_sign(lagnapathi_lon, ref_sign)
        karyesa_aspects_query = aspects_sign(karyesa_lon, query_sign)
        if lagnapathi_aspects_ref and karyesa_aspects_query:
            score += 15
            evaluation["details"].append("Lagnapathi aspects Ascendant, and Karyesa aspects target house (Favorable).")
            
        # Rule 2: Lagnapathi aspects target house (query_sign) and Karyesa aspects Ascendant (ref_sign)
        lagnapathi_aspects_query = aspects_sign(lagnapathi_lon, query_sign)
        karyesa_aspects_ref = aspects_sign(karyesa_lon, ref_sign)
        if lagnapathi_aspects_query and karyesa_aspects_ref:
            score += 15
            evaluation["details"].append("Lagnapathi aspects target house, and Karyesa aspects Ascendant (Favorable).")
            
        # Rule 3: Moon aspects both Lagnapathi and Karyesa
        lagnapathi_sign = int(lagnapathi_lon / 30.0) % 12
        karyesa_sign = int(karyesa_lon / 30.0) % 12
        moon_aspects_lagnapathi = aspects_sign(moon_lon, lagnapathi_sign)
        moon_aspects_karyesa = aspects_sign(moon_lon, karyesa_sign)
        if moon_aspects_lagnapathi and moon_aspects_karyesa:
            score += 15
            evaluation["details"].append("Moon aspects both Lagnapathi and Karyesa (Favorable connection).")
            
        # Chapter 2, Stanzas 5-8 Success Levels
        sun_lon = self.planets["Sun"]["longitude"]
        benefics = ["Jupiter", "Venus"]
        if not merc_combust:
            benefics.append("Mercury")
            
        aspecting_ref = []
        for p in self.planets:
            if p in ["Rahu", "Ketu"]:
                continue
            if aspects_sign(self.planets[p]["longitude"], ref_sign):
                aspecting_ref.append(p)
                
        lagnapathi_sign = get_sign(self.planets[lagnapathi]["longitude"])
        aspecting_lord = []
        for p in self.planets:
            if p in ["Rahu", "Ketu"]:
                continue
            if aspects_sign(self.planets[p]["longitude"], lagnapathi_sign):
                aspecting_lord.append(p)
                
        lord_aspects_lagna = lagnapathi in aspecting_ref
        benefics_aspect_lagna = any(b in aspecting_ref for b in benefics)
        benefics_aspect_lord = any(b in aspecting_lord for b in benefics)
        
        tenth_house_sign = (ref_sign + 9) % 12
        lord_in_10th = lagnapathi_sign == tenth_house_sign
        benefics_in_10th = [b for b in benefics if get_sign(self.planets[b]["longitude"]) == tenth_house_sign]
        
        num_benefics_aspect_lagna = sum(1 for b in benefics if b in aspecting_ref)
        if get_sign(moon_lon) in aspecting_ref:
            num_benefics_aspect_lagna += 1
            
        moon_combust = check_combustion("Moon", moon_lon, sun_lon)
        moon_afflicted = moon_combust
        for malefic in ["Saturn", "Mars", "Rahu", "Ketu"]:
            if aspects_sign(self.planets[malefic]["longitude"], get_sign(moon_lon)):
                moon_afflicted = True
                break
        moon_free_from_affliction = not moon_afflicted
        
        success_ratio = 0.25
        ratio_reason = "Base / No benefic or lord aspect on Ascendant (Stanza 5-8: 1/4 success)."
        
        if lord_aspects_lagna or (moon_free_from_affliction and benefics_aspect_lagna):
            success_ratio = 1.0
            ratio_reason = "Ascendant aspected by its lord or benefics with unafflicted Moon (Stanza 5-8: Full success)."
        elif benefics_aspect_lagna or benefics_aspect_lord or lord_in_10th or len(benefics_in_10th) >= 2 or num_benefics_aspect_lagna >= 3:
            success_ratio = 0.75
            ratio_reason = "Benefics aspect Ascendant/lord, or significators in 10th (Stanza 5-8: 3/4 success)."
        elif benefics_aspect_lord:
            success_ratio = 0.50
            ratio_reason = "Ascendant lord is aspected by benefics (Stanza 5-8: 1/2 success)."
        elif not (lord_aspects_lagna or benefics_aspect_lagna):
            success_ratio = 0.25
            ratio_reason = "Ascendant not aspected by its lord or benefics (Stanza 5-8: 1/4 success)."
            
        if success_ratio == 1.0:
            score += 40
        elif success_ratio == 0.75:
            score += 25
        elif success_ratio == 0.50:
            score += 10
        elif success_ratio == 0.25:
            score -= 15
            
        evaluation["details"].append(f"Bhava Success Ratio: {ratio_reason}")
        
        # Sign shape
        if self.lagna_sign in SIRSHODAYA_SIGNS:
            score += 10
            evaluation["details"].append("Ascendant is a Sirshodaya sign (favorable, indicating rapid progress).")
        else:
            score -= 5
            evaluation["details"].append("Ascendant is a Prushtodaya sign (indicates initial delays/difficulties).")
            
        # 4.5 House-specific Horary Rules (B.V. Raman's Prasna Tantra)
        house_score_adj = 0
        
        # Helper: check planet occupying a specific house index (relative to ref_sign)
        def occupants_of_house(h_idx):
            target_s = (ref_sign + h_idx - 1) % 12
            occ = []
            for p, p_data in self.planets.items():
                if p in ["Rahu", "Ketu"]:
                    continue
                if get_sign(p_data["longitude"]) == target_s:
                    occ.append(p)
            return occ

        lagnapathi_data = self.planets[lagnapathi]
        karyesa_data = self.planets[karyesa]
        sun_lon_val = self.planets["Sun"]["longitude"]
        lagnapathi_avastha = get_planetary_avastha(lagnapathi, lagnapathi_data["longitude"], lagnapathi_data, sun_lon_val, self.planets)
        karyesa_avastha = get_planetary_avastha(karyesa, karyesa_data["longitude"], karyesa_data, sun_lon_val, self.planets)

        if house_num == 1:
            if lagnapathi_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"]:
                house_score_adj += 15
                evaluation["details"].append(f"House 1: Lagnapathi ({lagnapathi}) is strong in state '{lagnapathi_avastha}' (Favorable).")
            elif lagnapathi_avastha in ["Deena", "Mushita", "Nipeeditha"]:
                house_score_adj -= 15
                evaluation["details"].append(f"House 1: Lagnapathi ({lagnapathi}) is weak in state '{lagnapathi_avastha}' (Unfavorable).")
            
            moon_avastha = get_planetary_avastha("Moon", moon_lon, self.planets["Moon"], sun_lon_val, self.planets)
            if moon_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"]:
                house_score_adj += 10
                evaluation["details"].append(f"House 1: Moon is strong in state '{moon_avastha}' (Favorable).")
            elif moon_avastha in ["Deena", "Mushita", "Nipeeditha"]:
                house_score_adj -= 10
                evaluation["details"].append(f"House 1: Moon is weak in state '{moon_avastha}' (Unfavorable).")

        elif house_num == 2:
            occ_2 = occupants_of_house(2)
            benefics_in_2 = [p for p in occ_2 if p in ["Jupiter", "Venus"] or (p == "Mercury" and not merc_combust)]
            malefics_in_2 = [p for p in occ_2 if p in ["Sun", "Mars", "Saturn"]]
            
            if benefics_in_2:
                house_score_adj += 15
                evaluation["details"].append(f"House 2: Benefics occupying 2nd house: {', '.join(benefics_in_2)} (Favorable for finance).")
            if malefics_in_2:
                house_score_adj -= 10
                evaluation["details"].append(f"House 2: Malefics occupying 2nd house: {', '.join(malefics_in_2)} (Obstacles/loss).")

        elif house_num == 3:
            third_lord = SIGN_LORDS[(ref_sign + 2) % 12]
            third_lord_data = self.planets[third_lord]
            tl_combust = check_combustion(third_lord, third_lord_data["longitude"], sun_lon_val)
            tl_sign = get_sign(third_lord_data["longitude"])
            tl_in_dusthana = tl_sign in [(ref_sign + 5) % 12, (ref_sign + 7) % 12]
            
            if tl_combust:
                house_score_adj -= 15
                evaluation["details"].append(f"House 3: 3rd Lord ({third_lord}) is combust (Unfavorable for travels/siblings).")
            if tl_in_dusthana:
                house_score_adj -= 10
                evaluation["details"].append(f"House 3: 3rd Lord ({third_lord}) is in dusthana (6th/8th house) (Obstacles).")

        elif house_num == 4:
            occ_4 = occupants_of_house(4)
            occ_7 = occupants_of_house(7)
            benefics_4_7 = [p for p in (occ_4 + occ_7) if p in ["Jupiter", "Venus"] or (p == "Mercury" and not merc_combust)]
            
            if benefics_4_7:
                house_score_adj += 15
                evaluation["details"].append(f"House 4: Benefics in 4th/7th house: {', '.join(benefics_4_7)} (Favorable for property/vehicles/home).")
            
            if get_sign(moon_lon) == (ref_sign + 3) % 12:
                rel_moon_lagna = get_planet_relationship("Moon", self.planets["Moon"], lagnapathi, lagnapathi_data)
                if rel_moon_lagna and rel_moon_lagna["is_applying"]:
                    house_score_adj += 20
                    evaluation["details"].append("House 4: Moon is in 4th house and has applying aspect (Ithasala) with Lagna Lord (Highly favorable).")

        elif house_num == 5:
            fifth_lord = SIGN_LORDS[(ref_sign + 4) % 12]
            rel_1_5 = get_planet_relationship(lagnapathi, lagnapathi_data, fifth_lord, self.planets[fifth_lord])
            if rel_1_5 and rel_1_5["is_applying"]:
                house_score_adj += 20
                evaluation["details"].append("House 5: Applying aspect (Ithasala) between 1st and 5th lords (Favorable for children).")
            
            fifth_house_sign = (ref_sign + 4) % 12
            fifth_lord_sign = get_sign(self.planets[fifth_lord]["longitude"])
            f_house_masc = (fifth_house_sign % 2) != 0
            f_lord_masc = (fifth_lord_sign % 2) != 0
            
            if f_house_masc and f_lord_masc:
                evaluation["gender_prediction"] = "Male Child (Strong male indicators: both 5th house and 5th lord in masculine signs)"
            elif not f_house_masc and not f_lord_masc:
                evaluation["gender_prediction"] = "Female Child (Strong female indicators: both 5th house and 5th lord in feminine signs)"
            else:
                evaluation["gender_prediction"] = "Mixed/Undetermined (Mixed indicators: masculine house and feminine lord, or vice-versa)"

        elif house_num == 6:
            seventh_lord = SIGN_LORDS[(ref_sign + 6) % 12]
            tenth_lord = SIGN_LORDS[(ref_sign + 9) % 12]
            
            physician_strong = lagnapathi_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"]
            patient_strong = get_planetary_avastha(tenth_lord, self.planets[tenth_lord]["longitude"], self.planets[tenth_lord], sun_lon_val, self.planets) in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"]
            disease_weak = get_planetary_avastha(seventh_lord, self.planets[seventh_lord]["longitude"], self.planets[seventh_lord], sun_lon_val, self.planets) in ["Deena", "Mushita", "Nipeeditha"]
            
            if physician_strong and patient_strong and disease_weak:
                house_score_adj += 25
                evaluation["details"].append("House 6: Physician (1st lord) and patient (10th lord) are strong, while disease (7th lord) is weak (Excellent signs of recovery).")
            elif not patient_strong and not physician_strong:
                house_score_adj -= 15
                evaluation["details"].append("House 6: Both patient and physician lords are weak (Delays/complications in healing).")

        elif house_num == 7:
            if get_sign(moon_lon) == (ref_sign + 6) % 12:
                house_score_adj += 15
                evaluation["details"].append("House 7: Moon in the 7th house (indicates early marriage or return of partner).")
            
            ven_data = self.planets["Venus"]
            ven_avastha = get_planetary_avastha("Venus", ven_data["longitude"], ven_data, sun_lon_val, self.planets)
            if ven_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"]:
                house_score_adj += 10
                evaluation["details"].append(f"House 7: Venus (significator of marriage) is strong in state '{ven_avastha}'.")

        elif house_num == 8:
            eighth_lord = SIGN_LORDS[(ref_sign + 7) % 12]
            eighth_lord_sign = get_sign(self.planets[eighth_lord]["longitude"])
            if eighth_lord_sign == ref_sign:
                house_score_adj -= 25
                evaluation["details"].append(f"House 8: 8th Lord ({eighth_lord}, lord of death/defeat) occupies Ascendant (Highly unfavorable).")

        elif house_num == 9:
            occ_9 = occupants_of_house(9)
            benefics_in_9 = [p for p in occ_9 if p in ["Jupiter", "Venus"] or (p == "Mercury" and not merc_combust)]
            if benefics_in_9:
                house_score_adj += 20
                evaluation["details"].append(f"House 9: Benefics in 9th house: {', '.join(benefics_in_9)} (Highly favorable for long travel/pilgrimage).")

        elif house_num == 10:
            tenth_lord = SIGN_LORDS[(ref_sign + 9) % 12]
            tenth_lord_sign = get_sign(self.planets[tenth_lord]["longitude"])
            
            if lagnapathi_sign == (ref_sign + 9) % 12 and tenth_lord_sign == ref_sign:
                house_score_adj += 30
                evaluation["details"].append("House 10: Parivartana (mutual sign exchange) between 1st and 10th lords (Incredible career success).")
            
            if kamboola:
                house_score_adj += 15
                evaluation["details"].append("House 10: Moon forms Kamboola Yoga conjoining significators.")

        elif house_num == 11:
            eleventh_lord = SIGN_LORDS[(ref_sign + 10) % 12]
            rel_1_11 = get_planet_relationship(lagnapathi, lagnapathi_data, eleventh_lord, self.planets[eleventh_lord])
            if rel_1_11 and rel_1_11["is_applying"] and rel_1_11["is_friendly"]:
                house_score_adj += 25
                evaluation["details"].append("House 11: Friendly applying aspect (Ithasala) between 1st and 11th lords (Realization of desires).")
            
            occ_11 = occupants_of_house(11)
            benefics_in_11 = [p for p in occ_11 if p in ["Jupiter", "Venus"] or (p == "Mercury" and not merc_combust)]
            if benefics_in_11:
                house_score_adj += 15
                evaluation["details"].append(f"House 11: Benefics in 11th house: {', '.join(benefics_in_11)} (Auspicious for financial gains).")

        elif house_num == 12:
            twelfth_lord = SIGN_LORDS[(ref_sign + 11) % 12]
            twelfth_lord_sign = get_sign(self.planets[twelfth_lord]["longitude"])
            if twelfth_lord_sign == ref_sign:
                house_score_adj += 15
                evaluation["details"].append(f"House 12: 12th Lord ({twelfth_lord}) occupies the Ascendant (Power to querent over losses).")

        # Incorporate Shatpanchasika rules evaluation
        sp_res = evaluate_shatpanchasika(self, house_num)
        evaluation["shatpanchasika_predictions"] = sp_res["predictions"]
        evaluation["details"].extend(sp_res["details"])
        shatpanchasika_adj = sp_res["score_adjustment"]

        # Incorporate special horary rules (Prasna Tantra Ch. III)
        special_adj = 0
        active_cat = special_category
        if not active_cat:
            if house_num == 12:
                active_cat = "deity_curse"
            elif house_num == 6:
                active_cat = "master_servant"
            elif house_num == 4:
                active_cat = "crops_trade"
            elif house_num == 8:
                active_cat = "disputes"

        if active_cat:
            if active_cat == "deity_curse":
                sp_rules_res = evaluate_deity_curse(self)
            elif active_cat == "master_servant":
                sp_rules_res = evaluate_master_servant(self)
            elif active_cat == "meals":
                sp_rules_res = evaluate_meals(self)
            elif active_cat == "sports":
                sp_rules_res = evaluate_sports(self)
            elif active_cat == "disputes":
                sp_rules_res = evaluate_disputes(self)
            elif active_cat == "crops_trade":
                sp_rules_res = evaluate_crops_trade(self, house_num)
            else:
                sp_rules_res = None

            if sp_rules_res:
                evaluation["shatpanchasika_predictions"].extend(sp_rules_res["predictions"])
                evaluation["details"].extend(sp_rules_res["details"])
                special_adj = sp_rules_res["score_adjustment"]

        score = max(0, min(100, 50 + score + house_score_adj + shatpanchasika_adj + special_adj))
        evaluation["score_pct"] = score
        
        if score >= 80:
            evaluation["success_probability"] = "High / Certain"
        elif score >= 50:
            evaluation["success_probability"] = "Medium / Obstacles"
        else:
            evaluation["success_probability"] = "Low / Failure"
            
        # 5. Timing of event calculation
        lagna_chara = self.lagna_sign % 3  # 0 = Movable, 1 = Fixed, 2 = Common
        intervening_signs = (query_sign - ref_sign) % 12
        mult_val = intervening_signs * 12
        if lagna_chara == 0:
            mult_unit = "Days"
        elif lagna_chara == 2:
            mult_unit = "Weeks"
        else:
            mult_unit = "Months"
            
        evaluation["timing_details"] = f"Sign Multiplication timing: {mult_val} {mult_unit} (based on {intervening_signs} intervening signs)."
        
        if score >= 50:
            if lagnapathi == karyesa:
                evaluation["timing"] = "Immediate / Self-realization"
            elif rel and rel["is_applying"]:
                deg_diff = rel["orb_diff"]
                if lagna_chara == 0:
                    evaluation["timing"] = f"{deg_diff:.1f} Days/Weeks"
                elif lagna_chara == 2:
                    evaluation["timing"] = f"{deg_diff:.1f} Weeks/Months"
                else:
                    evaluation["timing"] = f"{deg_diff:.1f} Months/Years"
            elif kamboola or nakta or yamaya:
                evaluation["timing"] = f"{mult_val} {mult_unit} (via intermediary Yoga)"
            else:
                evaluation["timing"] = f"{mult_val} {mult_unit}"
        else:
            evaluation["timing"] = "Undetermined / Event Unlikely"
            
        return evaluation

# Helper function to get sign index from longitude
def get_sign(longitude):
    return int(longitude / 30.0) % 12

def aspects_sign(planet_lon, target_sign):
    p_sign = int(planet_lon / 30.0) % 12
    diff = (target_sign - p_sign) % 12
    return diff in [0, 2, 3, 4, 6, 8, 9, 10]
