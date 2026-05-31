import math
from datetime import datetime, timedelta
from .astronomy import calculate_lagna, get_planetary_positions, get_house_cusps, get_sign_name
from .tajaka import get_planet_relationship, detect_nakta_yoga, detect_yamaya_yoga, detect_kamboola_yoga, detect_gairikamboola_yoga, get_planetary_avastha, check_combustion, check_nipeeditha
from .shatpanchasika import evaluate_shatpanchasika
from .special_rules import (
    evaluate_deity_curse,
    evaluate_master_servant,
    evaluate_meals,
    evaluate_sports,
    evaluate_disputes,
    evaluate_crops_trade,
    evaluate_purchase_sale,
    evaluate_women_enquiry,
    evaluate_dreams,
    evaluate_hunting,
    evaluate_incarceration,
    evaluate_ships,
    evaluate_rumours,
    evaluate_sexual_matters
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
    def __init__(self, local_datetime, lat_str, lon_str, tz_offset_hours, ayanamsha_mode="Lahiri"):
        """
        local_datetime: datetime object
        lat_str: Latitude, e.g. "12:58:18"
        lon_str: Longitude, e.g. "77:35:41"
        tz_offset_hours: float (e.g. 5.5 for IST)
        ayanamsha_mode: str ("Lahiri" or "Raman")
        """
        self.local_time = local_datetime
        # Calculate UTC time
        self.utc_time = local_datetime - timedelta(hours=tz_offset_hours)
        self.utc_str = self.utc_time.strftime("%Y/%m/%d %H:%M:%S")
        
        self.latitude = lat_str
        self.longitude = lon_str
        self.tz_offset = tz_offset_hours
        self.ayanamsha_mode = ayanamsha_mode
        
        # 1. Calculate Lagna & Astronomy
        lagna_data = calculate_lagna(self.utc_str, lat_str, lon_str, ayanamsha_mode=ayanamsha_mode)
        self.lagna_sidereal = lagna_data["sidereal"]
        self.lagna_tropical = lagna_data["tropical"]
        self.ayanamsha = lagna_data["ayanamsha"]
        self.lst = lagna_data["lst"]
        
        # 2. Get house cusps (Whole Sign)
        self.houses = get_house_cusps(self.lagna_sidereal)
        self.lagna_sign = self.houses[1]["sign"]
        self.lagnapathi = SIGN_LORDS[self.lagna_sign]
        
        # 3. Get planetary positions
        self.planets = get_planetary_positions(self.utc_str, self.ayanamsha, ayanamsha_mode=ayanamsha_mode)
        
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
        
        # Mercury combustion limit is 14 degrees for the Sincerity check
        merc_sun_diff = abs(self.planets["Mercury"]["longitude"] - self.planets["Sun"]["longitude"]) % 360
        if merc_sun_diff > 180:
            merc_sun_diff = 360 - merc_sun_diff
        merc_combust_sincerity = merc_sun_diff <= 14.0
        
        # Rule a: Moon conjoining reference sign, Saturn in a quadrant, Mercury combust
        moon_in_lagna = get_sign(self.planets["Moon"]["longitude"]) == ref_sign
        sat_in_quadrant = get_sign(self.planets["Saturn"]["longitude"]) in quadrants
        
        if moon_in_lagna and sat_in_quadrant and merc_combust_sincerity:
            reasons_insincere.append("Moon conjoins reference sign, Saturn in quadrant, and Mercury combust.")
            
        # Rule b: Mars and Mercury aspect Moon conjoining reference sign
        rel_mars_moon = get_planet_relationship("Mars", self.planets["Mars"], "Moon", self.planets["Moon"])
        rel_merc_moon = get_planet_relationship("Mercury", self.planets["Mercury"], "Moon", self.planets["Moon"])
        if moon_in_lagna and rel_mars_moon and rel_merc_moon:
            reasons_insincere.append("Mars and Mercury aspect the Moon conjoining reference sign.")
            
        # Rule c: Malefic conjoins reference sign (without benefic aspect)
        malefics_in_lagna = []
        for p in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]:
            if get_sign(self.planets[p]["longitude"]) == ref_sign:
                malefics_in_lagna.append(p)
        if malefics_in_lagna:
            reasons_insincere.append(f"Malefics conjoin reference sign: {', '.join(malefics_in_lagna)}")
            
        # Rule d: Jupiter or Mercury cast inimical glance (square/opposition) on lord of 7th
        rel_jup_7 = get_planet_relationship("Jupiter", self.planets["Jupiter"], seventh_lord, self.planets[seventh_lord])
        rel_merc_7 = get_planet_relationship("Mercury", self.planets["Mercury"], seventh_lord, self.planets[seventh_lord])
        if rel_jup_7 and rel_jup_7["is_friendly"] is False:
            reasons_insincere.append(f"Jupiter casts a hostile aspect on the 7th lord ({seventh_lord}).")
        if rel_merc_7 and rel_merc_7["is_friendly"] is False:
            reasons_insincere.append(f"Mercury casts a hostile aspect on the 7th lord ({seventh_lord}).")
            
        # Sincere indicators
        # indicator a: Benefic conjoins reference sign
        benefics_in_lagna = []
        for p in ["Jupiter", "Venus", "Mercury", "Moon"]:
            if get_sign(self.planets[p]["longitude"]) == ref_sign:
                # Mercury must not be combust to be benefic
                if p == "Mercury" and merc_combust_sincerity:
                    continue
                benefics_in_lagna.append(p)
        if benefics_in_lagna:
            reasons_sincere.append(f"Benefics conjoin reference sign: {', '.join(benefics_in_lagna)}")
            
        # indicator b: Mars or Full Moon and Jupiter aspect reference sign
        # A planet aspects/conjoins Lagna if it's not in the 2nd, 6th, 8th, or 12th house relative to Lagna
        def aspects_or_conjoins_lagna(p_name):
            p_sign = get_sign(self.planets[p_name]["longitude"])
            return ((p_sign - ref_sign) % 12) not in [1, 5, 7, 11]
            
        is_full_moon = 120.0 <= abs(self.planets["Moon"]["longitude"] - self.planets["Sun"]["longitude"]) % 360 <= 240.0
        
        mars_aspects = aspects_or_conjoins_lagna("Mars")
        jup_aspects = aspects_or_conjoins_lagna("Jupiter")
        moon_aspects = aspects_or_conjoins_lagna("Moon")
        
        if mars_aspects or (is_full_moon and moon_aspects and jup_aspects):
            reasons_sincere.append("Mars or Full Moon and Jupiter aspect or conjoin Lagna.")
                
        # indicator c: Jupiter or Mercury throws friendly aspect on lord of 7th (from reference sign)
        if rel_jup_7 and rel_jup_7["is_friendly"]:
            reasons_sincere.append(f"Jupiter throws a friendly aspect on the 7th lord ({seventh_lord}).")
        if rel_merc_7 and rel_merc_7["is_friendly"]:
            reasons_sincere.append(f"Mercury throws a friendly aspect on the 7th lord ({seventh_lord}).")
            
        # Final sincerity decision:
        # keep classical insincerity signals, but avoid over-triggering invalidation
        # when mixed sincere and insincere indications coexist.
        ins_count = len(reasons_insincere)
        sin_count = len(reasons_sincere)
        ins_minus_sin = ins_count - sin_count
        is_sincere = not (
            (ins_count >= 2 and sin_count == 0) or
            (ins_count >= 3 and ins_minus_sin >= 2)
        )

        return {
            "is_sincere": is_sincere,
            "insincere_score": ins_minus_sin,
            "reasons_insincere": reasons_insincere,
            "reasons_sincere": reasons_sincere
        }

    def _build_narrative(self, ref_sign, ref_point_name, house_num, query_sign,
                          lagnapathi, karyesa, rel, kamboola, nakta, yamaya,
                          merc_combust, sinc_res, gairikamboola=None):
        """
        Generates a book-style Prasna Tantra narrative for evaluation["details"].
        Follows the classical analytical flow used in B.V. Raman's Prasna Tantra
        and Prithuyasas's Shatpanchasika.
        """
        from .astronomy import get_nakshatra_pada
        details = []

        def planet_desc(p_name):
            """Returns a full description: Planet in Sign (House N), Nakshatra Pada N, Direct/Retro."""
            lon  = self.planets[p_name]["longitude"]
            spd  = self.planets[p_name]["speed"]
            sign = int(lon / 30) % 12
            sign_name = get_sign_name(sign)
            nak, pada, _ = get_nakshatra_pada(lon)
            house = ((sign - ref_sign + 12) % 12) + 1
            motion = "Retrograde (R)" if spd < 0 else "Direct"
            deg = lon % 30
            d = int(deg); m = int((deg - d) * 60); s = int(((deg - d) * 60 - m) * 60)
            return (f"{p_name} in {sign_name} {d}\u00b0{m:02d}'{s:02d}\" "
                    f"(House {house} from {get_sign_name(ref_sign)}), "
                    f"{nak} Nakshatra Pada {pada}, {motion}")

        def sign_type(s):
            t = ["Moveable", "Fixed", "Dual"][s % 3]
            sr = "Sirshodaya (head-rising — quick results)" if s in [2,4,5,6,7,10] else "Prishtodaya (back-rising — delayed results)"
            return f"{t}, {sr}"

        # ── 1. CHART SETUP ────────────────────────────────────────────────────
        lagna_sn = get_sign_name(ref_sign)
        details.append(
            f"[CHART SETUP | Ref. Point: {ref_point_name}] "
            f"Reference Lagna: {lagna_sn} — {sign_type(ref_sign)}. "
            f"Lagnapathi (lord of {lagna_sn}): {lagnapathi}. "
            f">> {planet_desc(lagnapathi)}"
        )

        # ── 2. QUERY HOUSE & KARYESA ─────────────────────────────────────────
        query_sn = get_sign_name(query_sign)
        details.append(
            f"[QUERY HOUSE {house_num} | {query_sn}] "
            f"The {house_num}{'st' if house_num==1 else ('nd' if house_num==2 else ('rd' if house_num==3 else 'th'))} "
            f"house from {lagna_sn} is {query_sn}. "
            f"Karyesa (lord of {query_sn}): {karyesa}. "
            f">> {planet_desc(karyesa)}"
        )

        # ── 3. DIRECT RELATION (Ithasala / Easarapha) ────────────────────────
        if lagnapathi == karyesa:
            details.append(
                f"[DIRECT RELATION | Swami Yoga] Lagnapathi and Karyesa are the SAME planet "
                f"({lagnapathi}). This is Swami Yoga (Self-realization) — the querent is the "
                f"lord of both the reference Lagna and the query house. Per Shatpanchasika I.3: "
                f"'Whichever Bhava is aspected or occupied by its lord, the prosperity of that "
                f"Bhava is ensured.' This is the strongest possible indicator."
            )
        elif rel:
            aspect     = rel["aspect_type"]
            friendly   = "friendly" if rel["is_friendly"] else "hostile"
            applying   = "APPLYING (Ithasala)" if rel["is_applying"] else "SEPARATING (Easarapha)"
            orb        = rel["orb_diff"]
            if rel["is_applying"] and rel["is_friendly"]:
                verdict = "SUCCESS strongly indicated."
            elif rel["is_applying"] and not rel["is_friendly"]:
                verdict = "Success possible but with obstacles (hostile Ithasala)."
            else:
                verdict = "FAILURE indicated — Easarapha: the opportunity has passed or will not materialise."
            details.append(
                f"[DIRECT RELATION | Tajaka Aspect] {lagnapathi} (Lagnapathi) and {karyesa} (Karyesa) "
                f"share a {friendly} {aspect} — {applying}, within {orb:.1f}° orb. "
                f"{verdict} "
                f"[Shatpanchasika I.3; Prasna Tantra Ch. II: Ithasala = applying aspect = fulfilment; "
                f"Easarapha = separating = matter concluded/failed.]"
            )
        else:
            details.append(
                f"[DIRECT RELATION | No Aspect] No Tajaka aspect (Conjunction / Sextile / Square / "
                f"Trine / Opposition) exists between {lagnapathi} (Lagnapathi) and {karyesa} (Karyesa) "
                f"within operative orbs (Deepthamsas). This is unfavorable — the lords of the Lagna "
                f"and the query house are unconnected. Check for intermediary Yogas below. "
                f"[Shatpanchasika I.3]"
            )

        # ── 4. INTERMEDIARY YOGAS ────────────────────────────────────────────
        if gairikamboola:
            afflictions_str = []
            if gairikamboola["afflictions"]["combust"]:
                afflictions_str.append("combust")
            if gairikamboola["afflictions"]["debilitated"]:
                afflictions_str.append("debilitated in Scorpio")
            if gairikamboola["afflictions"]["malefic_aspect"]:
                afflictions_str.append("aspected/conjoined by Mars/Saturn")
            details.append(
                f"[YOGA — Gairikamboola] Gairikamboola Yoga detected (compromised Kamboola). "
                f"Lagnapathi and Karyesa have Ithasala, and the Moon mediates, but the Moon is afflicted "
                f"({', '.join(afflictions_str)}), which spoils the connection. [Prasna Tantra Ch. II]"
            )
        elif kamboola:
            translator = "Moon"
            details.append(
                f"[YOGA — Kamboola] Moon ({planet_desc('Moon')}) "
                f"acts as the intermediary, translating strength between {lagnapathi} and {karyesa} "
                f"via {translator}. The matter will be fulfilled through a third party or after some delay. "
                f"[Prasna Tantra Ch. II — Kamboola Yoga: Moon mediates between the two lords.]"
            )
        if nakta:
            translator = nakta[0].get("translator", "?")
            details.append(
                f"[YOGA — Nakta] {translator} acts as a nocturnal translator of light between "
                f"{lagnapathi} and {karyesa}. Achievement is possible through an intermediary agent. "
                f"[Prasna Tantra Ch. II — Nakta Yoga]"
            )
        if yamaya:
            translator = yamaya[0].get("translator", "?")
            details.append(
                f"[YOGA — Yamaya] {translator} coordinates the transfer of strength "
                f"between {lagnapathi} and {karyesa}. Success may come through authority or officialdom. "
                f"[Prasna Tantra Ch. II — Yamaya Yoga]"
            )
        if not (kamboola or nakta or yamaya) and not rel and lagnapathi != karyesa:
            details.append(
                "[YOGA — None] No Kamboola, Nakta, or Yamaya Yoga detected. "
                "Without either a direct Ithasala or an intermediary Yoga, the matter is unlikely to succeed."
            )

        # ── 5. MOON ANALYSIS ─────────────────────────────────────────────────
        moon_lon  = self.planets["Moon"]["longitude"]
        moon_sign = int(moon_lon / 30) % 12
        moon_sn   = get_sign_name(moon_sign)
        moon_house = ((moon_sign - ref_sign + 12) % 12) + 1
        moon_nak, moon_pada, _ = get_nakshatra_pada(moon_lon)
        moon_combust = abs(moon_lon - self.planets["Sun"]["longitude"]) % 360 <= 12.0
        sun_lon = self.planets["Sun"]["longitude"]

        moon_aspects_recv = []
        for p in ["Jupiter", "Venus", "Mercury", "Sun", "Mars", "Saturn"]:
            if p not in self.planets:
                continue
            p_sign = int(self.planets[p]["longitude"] / 30) % 12
            diff = (moon_sign - p_sign) % 12
            if diff in [0, 2, 3, 4, 6, 8, 9, 10]:
                is_b = p in ["Jupiter", "Venus"] or (p == "Mercury" and not merc_combust)
                moon_aspects_recv.append(("+" if is_b else "-") + p)

        moon_aff = moon_combust or any(a.startswith("-") for a in moon_aspects_recv)
        moon_status = "AFFLICTED" if moon_aff else "FREE from affliction"
        asp_str = f" Aspects received: {', '.join(moon_aspects_recv)}." if moon_aspects_recv else " No planetary aspects on Moon."

        details.append(
            f"[MOON ANALYSIS] Moon in {moon_sn} (House {moon_house} from ref.), "
            f"{moon_nak} Nakshatra Pada {moon_pada}.{asp_str} "
            f"Moon is {moon_status}{'— combust, severely weakened' if moon_combust else ''}. "
            f"[Shatpanchasika I.4–5: Moon aspected by Jupiter/Venus in Lagna restores lost matters; "
            f"Moon afflicted by malefics indicates obstacles.]"
        )

        # ── 6. LAGNA OCCUPANTS ───────────────────────────────────────────────
        lagna_occ = []
        for p, pd in self.planets.items():
            if p in ["Rahu", "Ketu"]:
                continue
            if int(pd["longitude"] / 30) % 12 == ref_sign:
                is_b = p in ["Jupiter", "Venus"] or (p == "Mercury" and not merc_combust) or p == "Moon"
                lagna_occ.append(("+" if is_b else "-") + p)

        if lagna_occ:
            details.append(
                f"[LAGNA OCCUPANTS] Planets in reference Lagna ({lagna_sn}): {', '.join(lagna_occ)}. "
                f"(+ benefic, - malefic). [Shatpanchasika I.4: benefics in Lagna ensure success; "
                f"malefics ensure failure.]"
            )
        else:
            details.append(f"[LAGNA OCCUPANTS] No planets occupy the reference Lagna ({lagna_sn}).")

        # ── 7. QUERY HOUSE OCCUPANTS ─────────────────────────────────────────
        query_occ = []
        for p, pd in self.planets.items():
            if p in ["Rahu", "Ketu"]:
                continue
            if int(pd["longitude"] / 30) % 12 == query_sign:
                is_b = p in ["Jupiter", "Venus"] or (p == "Mercury" and not merc_combust) or p == "Moon"
                query_occ.append(("+" if is_b else "-") + p)

        if query_occ:
            details.append(
                f"[QUERY HOUSE OCCUPANTS] Planets in House {house_num} ({query_sn}): {', '.join(query_occ)}. "
                f"[Shatpanchasika I.3: the lord and occupants of the Bhava determine its prosperity or ruin.]"
            )
        else:
            details.append(f"[QUERY HOUSE OCCUPANTS] No planets occupy House {house_num} ({query_sn}).")

        # ── 8. SINCERITY SUMMARY ─────────────────────────────────────────────
        if not sinc_res.get("is_sincere", True):
            details.append(
                f"[SINCERITY — INSINCERE] The Prasna chart indicates an INSINCERE or test query. "
                f"Insincere indicators ({len(sinc_res['reasons_insincere'])}): "
                + "; ".join(sinc_res["reasons_insincere"])
                + ". Per Prasna Tantra tradition: only a genuine, first-time question yields "
                f"a valid Prasna chart. The verdict below is marked Inconclusive."
            )
        else:
            details.append(
                f"[SINCERITY — SINCERE] Query appears genuine. "
                + (f"Sincere indicators: {'; '.join(sinc_res['reasons_sincere'])}." if sinc_res["reasons_sincere"] else "No explicit insincere indicators found.")
            )

        return details

    def _get_active_special_category(self, house_num, special_category, query_text):
        # 1. Check query_text keywords first to override any default categories
        if query_text:
            q_lower = query_text.lower()
            if any(kw in q_lower for kw in ["dream", "dreams", "sleep"]):
                return "dreams"
            elif any(kw in q_lower for kw in ["hunt", "hunting", "expedition", "game"]):
                return "hunting"
            elif any(kw in q_lower for kw in ["incarceration", "incarcerated", "imprison", "imprisoned", "prison", "jail", "custody", "captivity", "detention"]):
                return "incarceration"
            elif any(kw in q_lower for kw in ["ship", "ships", "voyage", "sea", "ocean", "sail", "vessel", "boat"]):
                return "ships"
            elif any(kw in q_lower for kw in ["rumour", "rumours", "rumor", "rumors", "news", "hearsay", "report"]):
                return "rumours"
            elif any(kw in q_lower for kw in ["sex", "sexual", "union", "intimacy", "copulation", "passion", "secretion", "prostitute", "adultery"]):
                return "sexual_matters"
            elif any(kw in q_lower for kw in ["woman", "women", "lady", "girl", "female", "her", "wife nature", "enquiry about women"]):
                return "women_enquiry"
            elif any(kw in q_lower for kw in ["purchase", "buy", "bought", "sale", "sell", "sold", "transaction", "deal", "acquisition"]):
                return "purchase_sale"

        active_cat = special_category
        # Suppress sports default for relationship queries if query_text is provided
        if active_cat == "sports" and query_text:
            love_keywords = ["love", "marriage", "marry", "relationship", "proposal", "propose", "romance", "spouse", "wife", "husband", "partner", "friendship", "friend", "attraction", "affection", "boy friend", "girlfriend", "boyfriend", "girl friend"]
            if any(kw in query_text.lower() for kw in love_keywords):
                active_cat = None
                
        if not active_cat:
            if house_num == 12:
                active_cat = "deity_curse"
            elif house_num == 6:
                active_cat = "master_servant"
            elif house_num == 4:
                active_cat = "crops_trade"
            elif house_num == 8:
                active_cat = "disputes"
            elif house_num == 10 and query_text:
                job_keywords = ["job", "career", "work", "employ", "service", "master", "promotion", "salary", "boss", "office", "profession", "business"]
                if any(kw in query_text.lower() for kw in job_keywords):
                    active_cat = "master_servant"
        return active_cat

    def _filter_shatpanchasika_predictions(self, predictions, active_cat, query_text):
        """
        Reduce cross-topic overlap noise in broad house-based Shatpanchasika outputs.
        Keeps predictions focused on the active special category where possible.
        """
        if not predictions:
            return predictions

        category_map = {
            "disputes": ["dispute", "litigation", "lawsuit", "conflict", "enemy", "arbitr", "judge", "siege", "war"],
            "ships": ["voyage", "ship", "cargo", "sea", "sail", "merchandise"],
            "sexual_matters": ["partner", "union", "sexual", "intimacy", "adultery"],
            "women_enquiry": ["women", "woman", "female", "partner", "union", "emotional"],
            "purchase_sale": ["purchase", "sale", "gain", "trade", "buyer", "seller", "transaction"],
            "hunting": ["hunting", "expedition", "catch", "target"],
            "incarceration": ["captivity", "imprison", "custody", "detention", "release"],
            "dreams": ["dream", "sleep"],
            "rumours": ["news", "rumour", "report"],
        }

        # infer traveler-style context from query text even when special category is not explicit
        q = (query_text or "").lower()
        traveler_intent = any(k in q for k in ["return", "abroad", "traveler", "gone away", "alive or dead", "journey"])
        focus_terms = category_map.get(active_cat, [])
        if traveler_intent and not focus_terms:
            focus_terms = ["traveler", "return", "abroad", "enemy", "arrival", "movement"]

        if not focus_terms:
            return predictions

        filtered = []
        fallback_general = []
        for p in predictions:
            cat = str(p.get("category", "")).lower()
            pred = str(p.get("prediction", "")).lower()
            text = f"{cat} {pred}"
            if any(term in text for term in focus_terms):
                filtered.append(p)
            elif "general" in cat:
                fallback_general.append(p)

        # Keep at least some contextual signal and avoid returning empty list
        if filtered:
            # Add at most one general line for context continuity
            if fallback_general:
                filtered.append(fallback_general[0])
            return filtered
        return predictions

    def _get_stronger_mercury_venus(self):
        """
        Determines the stronger planet between Mercury and Venus according to a 
        multi-tiered dignity comparison and standard tie-breakers.
        Returns:
            stronger_name: "Mercury" or "Venus"
            reason: Explanation of the decision for debug/narrative purposes
        """
        merc_data = self.planets["Mercury"]
        ven_data = self.planets["Venus"]
        merc_lon = merc_data["longitude"]
        ven_lon = ven_data["longitude"]
        sun_lon = self.planets["Sun"]["longitude"]

        # 1. Compare Avastha Ranks
        merc_avastha = get_planetary_avastha("Mercury", merc_lon, merc_data, sun_lon, self.planets)
        ven_avastha = get_planetary_avastha("Venus", ven_lon, ven_data, sun_lon, self.planets)

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

        if merc_rank != ven_rank:
            if merc_rank > ven_rank:
                return "Mercury", f"Mercury has superior Avastha ({merc_avastha}) compared to Venus ({ven_avastha})"
            else:
                return "Venus", f"Venus has superior Avastha ({ven_avastha}) compared to Mercury ({merc_avastha})"

        # 2. Combustion Tie-Breaker
        merc_combust = check_combustion("Mercury", merc_lon, sun_lon)
        ven_combust = check_combustion("Venus", ven_lon, sun_lon)
        if merc_combust != ven_combust:
            if not merc_combust:
                return "Mercury", "Mercury is non-combust while Venus is combust"
            else:
                return "Venus", "Venus is non-combust while Mercury is combust"

        # 3. Malefic Conjunction / Planetary War Tie-Breaker
        merc_vanquished = check_nipeeditha("Mercury", merc_lon, self.planets)
        ven_vanquished = check_nipeeditha("Venus", ven_lon, self.planets)
        if merc_vanquished != ven_vanquished:
            if not merc_vanquished:
                return "Mercury", "Mercury is not conjoined with a malefic while Venus is conjoined"
            else:
                return "Venus", "Venus is not conjoined with a malefic while Mercury is conjoined"

        # 4. Retrograde Status Tie-Breaker
        merc_retro = merc_data.get("is_retrograde", False)
        ven_retro = ven_data.get("is_retrograde", False)
        if merc_retro != ven_retro:
            if not merc_retro:
                return "Mercury", "Mercury is direct while Venus is retrograde"
            else:
                return "Venus", "Venus is direct while Mercury is retrograde"

        # 5. Motional Speed Tie-Breaker (faster absolute speed > slower)
        merc_speed = abs(merc_data.get("speed", 0.0))
        ven_speed = abs(ven_data.get("speed", 0.0))
        if not math.isclose(merc_speed, ven_speed, rel_tol=1e-9, abs_tol=1e-9):
            if merc_speed > ven_speed:
                return "Mercury", f"Mercury has faster motional speed ({merc_speed:.4f}°/day) than Venus ({ven_speed:.4f}°/day)"
            else:
                return "Venus", f"Venus has faster motional speed ({ven_speed:.4f}°/day) than Mercury ({merc_speed:.4f}°/day)"

        # 6. Natural Strength (Naisargika Bala) Tie-Breaker: Venus > Mercury
        return "Venus", "Venus has greater natural strength (Naisargika Bala) than Mercury"

    def evaluate_query(self, house_num, query_num=1, special_category=None, query_text=None):

        """
        Evaluates a query corresponding to a specific house.
        house_num: 1 to 12
        query_num: sequential query number for multiple queries.
                   Values wrap in a 1..5 cycle (e.g., 6->1, 7->2).
        special_category: string (optional, e.g. "deity_curse", "sports")
        query_text: string (optional, original query text for contextual overrides)
        """
        if house_num < 1 or house_num > 12:
            raise ValueError("House number must be between 1 and 12.")
            
        # Normalize query number to strict 1..5 classical cycle
        try:
            qn = int(query_num)
        except Exception:
            qn = 1
        if qn <= 0:
            qn = 1
        query_num_normalized = ((qn - 1) % 5) + 1

        # Determine the reference "Lagna" point based on normalized query number
        if query_num_normalized == 1:
            ref_sign = self.lagna_sign
            ref_point_name = "Ascendant (Lagna)"
        elif query_num_normalized == 2:
            ref_sign = get_sign(self.planets["Moon"]["longitude"])
            ref_point_name = "Moon"
        elif query_num_normalized == 3:
            ref_sign = get_sign(self.planets["Sun"]["longitude"])
            ref_point_name = "Sun"
        elif query_num_normalized == 4:
            ref_sign = get_sign(self.planets["Jupiter"]["longitude"])
            ref_point_name = "Jupiter"
        else:
            # 5th query: stronger between Mercury and Venus
            stronger_planet, strength_reason = self._get_stronger_mercury_venus()
            ref_sign = get_sign(self.planets[stronger_planet]["longitude"])
            ref_point_name = f"{stronger_planet} (stronger: {strength_reason})"
                
        lagnapathi = SIGN_LORDS[ref_sign]
        merc_combust = abs(self.planets["Mercury"]["longitude"] - self.planets["Sun"]["longitude"]) % 360 <= 8.0
        
        # Calculate the query sign and Karyesa relative to this reference sign
        query_sign = (ref_sign + house_num - 1) % 12
        karyesa = SIGN_LORDS[query_sign]
        
        # Calculate query-specific sincerity
        sinc_res = self._check_sincerity(ref_sign=ref_sign)
        
        evaluation = {
            "house": house_num,
            "query_num": query_num_normalized,
            "ref_point_name": ref_point_name,
            "ref_sign_name": get_sign_name(ref_sign),
            "query_sign_name": get_sign_name(query_sign),
            "lagnapathi": lagnapathi,
            "karyesa": karyesa,
            "direct_relationship": None,
            "yogas": [],
            "verdict": "MAYBE",           # Classical YES / NO / MAYBE / CANNOT BE ANSWERED
            "verdict_reason": "",         # One-line classical basis
            "success_probability": "Medium",
            "score_pct": 50,
            "timing": "Immediate / Self-realization",
            "details": [],
            "shatpanchasika_predictions": [],
            "sincerity": sinc_res
        }
        
        # 1. Check if Lagnapathi and Karyesa are the same planet (Self-realization)
        if lagnapathi == karyesa:
            # Build narrative first (needs rel/yoga inputs — use None for self-realization)
            evaluation["details"] = self._build_narrative(
                ref_sign, ref_point_name, house_num, query_sign,
                lagnapathi, karyesa,
                rel=None, kamboola=None, nakta=None, yamaya=None,
                merc_combust=merc_combust, sinc_res=sinc_res
            )

            sp_res = evaluate_shatpanchasika(self, house_num)
            active_cat = self._get_active_special_category(house_num, special_category, query_text)
            evaluation["shatpanchasika_predictions"] = self._filter_shatpanchasika_predictions(
                sp_res["predictions"], active_cat, query_text
            )
            evaluation["details"].extend(sp_res["details"])

            # Incorporate special horary rules (Prasna Tantra Ch. III)
            if active_cat:
                if active_cat == "deity_curse": sp_rules_res = evaluate_deity_curse(self)
                elif active_cat == "master_servant": sp_rules_res = evaluate_master_servant(self)
                elif active_cat == "meals": sp_rules_res = evaluate_meals(self)
                elif active_cat == "sports": sp_rules_res = evaluate_sports(self)
                elif active_cat == "disputes": sp_rules_res = evaluate_disputes(self)
                elif active_cat == "crops_trade": sp_rules_res = evaluate_crops_trade(self, house_num)
                elif active_cat == "purchase_sale": sp_rules_res = evaluate_purchase_sale(self)
                elif active_cat == "women_enquiry": sp_rules_res = evaluate_women_enquiry(self)
                elif active_cat == "dreams": sp_rules_res = evaluate_dreams(self)
                elif active_cat == "hunting": sp_rules_res = evaluate_hunting(self)
                elif active_cat == "incarceration": sp_rules_res = evaluate_incarceration(self)
                elif active_cat == "ships": sp_rules_res = evaluate_ships(self)
                elif active_cat == "rumours": sp_rules_res = evaluate_rumours(self)
                elif active_cat == "sexual_matters": sp_rules_res = evaluate_sexual_matters(self)
                else: sp_rules_res = None

                if sp_rules_res:
                    evaluation["shatpanchasika_predictions"].extend(sp_rules_res["predictions"])
                    evaluation["details"].extend(sp_rules_res["details"])

            # Sincerity gate
            if not sinc_res.get("is_sincere", True):
                evaluation["verdict"] = "CANNOT BE ANSWERED"
                evaluation["verdict_reason"] = "Query is insincere/test — Prasna chart invalid"
                evaluation["success_probability"] = "Inconclusive"
                evaluation["score_pct"] = 0
                evaluation["timing"] = "Not determinable — query marked insincere"
            else:
                evaluation["verdict"] = "YES"
                evaluation["verdict_reason"] = "Swami Yoga (Lagnapathi = Karyesa) — strongest possible indicator [Shatpanchasika I.3]"
                evaluation["success_probability"] = "Very High"
                evaluation["score_pct"] = 100
            return self._enrich_special_evaluations(evaluation, house_num, query_text)
            
        # 2. Check direct relationship
        rel = get_planet_relationship(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa])
        evaluation["direct_relationship"] = rel

        # 3. Check for Yogas
        moon_data = self.planets["Moon"]
        kamboola = detect_kamboola_yoga(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa], moon_data)
        gairikamboola = detect_gairikamboola_yoga(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa], moon_data, self.planets)
        if gairikamboola:
            evaluation["yogas"].append({"name": "Gairikamboola Yoga", "details": gairikamboola})
        elif kamboola:
            evaluation["yogas"].append({"name": "Kamboola Yoga", "details": kamboola})

        nakta = detect_nakta_yoga(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa], self.planets)
        if nakta:
            evaluation["yogas"].append({"name": "Nakta Yoga", "details": nakta})

        yamaya = detect_yamaya_yoga(lagnapathi, self.planets[lagnapathi], karyesa, self.planets[karyesa], self.planets)
        if yamaya:
            evaluation["yogas"].append({"name": "Yamaya Yoga", "details": yamaya})

        # Build full narrative now that rel and yogas are known
        evaluation["details"] = self._build_narrative(
            ref_sign, ref_point_name, house_num, query_sign,
            lagnapathi, karyesa, rel, kamboola, nakta, yamaya,
            merc_combust=merc_combust, sinc_res=sinc_res, gairikamboola=gairikamboola
        )
            
        # 4. Calculate Success Score (details narrative already built above)
        score = 0

        # Base aspect scoring
        if rel:
            if rel["aspect_type"] == "Conjunction":
                p1_malefic = lagnapathi in ["Sun", "Mars", "Saturn"]
                p2_malefic = karyesa in ["Sun", "Mars", "Saturn"]
                score += 20 if (p1_malefic or p2_malefic) else 45
            elif rel["is_applying"]:
                score += 50 if rel["is_friendly"] else 20
            else:
                score -= 20

        # Yoga score additions
        if gairikamboola:
            # Gairikamboola spoils the connection
            score -= 20
        elif kamboola:
            score += 30
        if nakta:
            score += 20
        if yamaya:
            score += 15
            
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
            rel_1_3 = get_planet_relationship(lagnapathi, lagnapathi_data, third_lord, third_lord_data)
            evaluation["details"].append(
                f"House 3 Analysis: 3rd lord is {third_lord}; combust={tl_combust}; dusthana(6/8)={tl_in_dusthana}."
            )
            
            if tl_combust:
                house_score_adj -= 15
                evaluation["details"].append(f"House 3: 3rd Lord ({third_lord}) is combust (Unfavorable for travels/siblings).")
            if tl_in_dusthana:
                house_score_adj -= 10
                evaluation["details"].append(f"House 3: 3rd Lord ({third_lord}) is in dusthana (6th/8th house) (Obstacles).")
            if rel_1_3 and rel_1_3["is_applying"] and rel_1_3["is_friendly"]:
                house_score_adj += 12
                evaluation["details"].append("House 3: Friendly applying relation between 1st and 3rd lords (success through effort and sibling harmony).")
            elif rel_1_3 and rel_1_3["is_friendly"] is False:
                house_score_adj -= 8
                evaluation["details"].append("House 3: Hostile relation between 1st and 3rd lords (quarrel/separation tendencies with siblings or effort-friction).")

        elif house_num == 4:
            occ_4 = occupants_of_house(4)
            occ_7 = occupants_of_house(7)
            benefics_4_7 = [p for p in (occ_4 + occ_7) if p in ["Jupiter", "Venus"] or (p == "Mercury" and not merc_combust)]
            fourth_lord = SIGN_LORDS[(ref_sign + 3) % 12]
            rel_1_4 = get_planet_relationship(lagnapathi, lagnapathi_data, fourth_lord, self.planets[fourth_lord])
            
            if benefics_4_7:
                house_score_adj += 15
                evaluation["details"].append(f"House 4: Benefics in 4th/7th house: {', '.join(benefics_4_7)} (Favorable for property/vehicles/home).")
            if rel_1_4 and rel_1_4["is_applying"] and rel_1_4["is_friendly"]:
                house_score_adj += 10
                evaluation["details"].append("House 4: Friendly applying relation between 1st and 4th lords (property/home acquisition and domestic harmony).")
            elif rel_1_4 and rel_1_4["is_friendly"] is False:
                house_score_adj -= 8
                evaluation["details"].append("House 4: Hostile tie between 1st and 4th lords (domestic friction, delay in property comfort).")
            
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
            if rel_1_5 and rel_1_5["is_friendly"] is False:
                house_score_adj -= 10
                evaluation["details"].append("House 5: Hostile 1st/5th relation may indicate delay, anxiety, or interruptions in childbirth/education.")
            
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

            # Expanded disease-nature hints from planet influencing the 6th house/lord
            sixth_sign = (ref_sign + 5) % 12
            sixth_lord = SIGN_LORDS[sixth_sign]
            rel_lord_6 = get_planet_relationship(sixth_lord, self.planets[sixth_lord], lagnapathi, lagnapathi_data)
            disease_hint_map = {
                "Sun": "heat/bile, inflammatory, feverish or cardiac strain patterns",
                "Moon": "fluid/phlegmatic, edema, glandular or psychosomatic fluctuations",
                "Mars": "acute, injury, bleeding, infection, surgery-prone patterns",
                "Mercury": "nervous, respiratory, skin/allergy, variable diagnosis patterns",
                "Jupiter": "metabolic, endocrine, swelling/growth, sugar-lipid tendencies",
                "Venus": "reproductive, renal/urinary, venous or hormonal imbalance patterns",
                "Saturn": "chronic, degenerative, obstructive, pain/stiffness long-duration patterns",
            }
            disease_hint = disease_hint_map.get(sixth_lord, "mixed disease tendencies")
            evaluation["details"].append(
                f"House 6 Diagnosis Hint: 6th lord is {sixth_lord}, suggesting {disease_hint}."
            )
            if rel_lord_6 and rel_lord_6["is_applying"] and not rel_lord_6["is_friendly"]:
                evaluation["details"].append(
                    "House 6 Diagnosis Hint: Hostile applying tie between 6th lord and Lagnapathi suggests aggravation phase."
                )
            elif rel_lord_6 and rel_lord_6["is_applying"] and rel_lord_6["is_friendly"]:
                evaluation["details"].append(
                    "House 6 Diagnosis Hint: Friendly applying tie between 6th lord and Lagnapathi supports manageable/treatable progression."
                )

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

        # Additional explicit rule coverage from remaining stanza set
        # Stanza 1: Lagnapathi in Lagna + Moon aspecting Lagna -> fulfillment
        if get_sign(self.planets[lagnapathi]["longitude"]) == ref_sign and aspects_sign(self.planets["Moon"]["longitude"], ref_sign):
            house_score_adj += 12
            evaluation["details"].append("Stanza Rule: Lagnapathi occupies Lagna and Moon aspects Lagna -> fulfillment strongly indicated.")

        # Stanza 13 style danger intensification: severe affliction involving 7th, Moon, and 8th axis
        seventh_sign = (ref_sign + 6) % 12
        eighth_sign = (ref_sign + 7) % 12
        sat_aff_7 = aspects_sign(self.planets["Saturn"]["longitude"], seventh_sign) or get_sign(self.planets["Saturn"]["longitude"]) == seventh_sign
        mars_aff_7 = aspects_sign(self.planets["Mars"]["longitude"], seventh_sign) or get_sign(self.planets["Mars"]["longitude"]) == seventh_sign
        nodes_aff_7 = (
            aspects_sign(self.planets["Rahu"]["longitude"], seventh_sign) or get_sign(self.planets["Rahu"]["longitude"]) == seventh_sign or
            aspects_sign(self.planets["Ketu"]["longitude"], seventh_sign) or get_sign(self.planets["Ketu"]["longitude"]) == seventh_sign
        )
        moon_aff_8 = aspects_sign(self.planets["Moon"]["longitude"], eighth_sign) or get_sign(self.planets["Moon"]["longitude"]) == eighth_sign
        if (sat_aff_7 and mars_aff_7 and nodes_aff_7 and moon_aff_8):
            house_score_adj -= 18
            evaluation["details"].append("Stanza Rule: Saturn/Mars/nodal severe 7th-axis affliction with Moon-8th involvement -> danger/intensity increases.")

        # Stanza 31/57: strong 11th-lord favorable connection -> gains / recovery support
        eleventh_lord = SIGN_LORDS[(ref_sign + 10) % 12]
        rel_1_11_extra = get_planet_relationship(lagnapathi, self.planets[lagnapathi], eleventh_lord, self.planets[eleventh_lord])
        eleventh_avastha = get_planetary_avastha(eleventh_lord, self.planets[eleventh_lord]["longitude"], self.planets[eleventh_lord], sun_lon_val, self.planets)
        if rel_1_11_extra and rel_1_11_extra["is_applying"] and rel_1_11_extra["is_friendly"] and eleventh_avastha in ["Deeptha", "Swastha", "Athiveerya", "Suveerya"]:
            house_score_adj += 10
            evaluation["details"].append("Stanza Rule: Strong 11th-lord favorable tie supports gain/recovery/new-position outcomes.")

        # Stanza 35: 1st-3rd favorable link -> success through effort
        third_lord_extra = SIGN_LORDS[(ref_sign + 2) % 12]
        rel_1_3_extra = get_planet_relationship(lagnapathi, self.planets[lagnapathi], third_lord_extra, self.planets[third_lord_extra])
        if rel_1_3_extra and rel_1_3_extra["is_applying"] and rel_1_3_extra["is_friendly"]:
            house_score_adj += 8
            evaluation["details"].append("Stanza Rule: Friendly applying 1st-3rd relation -> success through courage/effort.")

        # Stanza 70: weak/afflicted 6th-lord weakens enemies
        sixth_lord_extra = SIGN_LORDS[(ref_sign + 5) % 12]
        sixth_avastha = get_planetary_avastha(sixth_lord_extra, self.planets[sixth_lord_extra]["longitude"], self.planets[sixth_lord_extra], sun_lon_val, self.planets)
        if sixth_avastha in ["Deena", "Mushita", "Nipeeditha", "Suptha"]:
            house_score_adj += 6
            evaluation["details"].append("Stanza Rule: 6th-lord weak/afflicted -> enemy strength reduces.")

        # Stanza 72/73/75: marriage-relational nuance on 7th
        if house_num == 7:
            sat_on_7 = aspects_sign(self.planets["Saturn"]["longitude"], seventh_sign) or get_sign(self.planets["Saturn"]["longitude"]) == seventh_sign
            mars_on_7 = aspects_sign(self.planets["Mars"]["longitude"], seventh_sign) or get_sign(self.planets["Mars"]["longitude"]) == seventh_sign
            if sat_on_7:
                house_score_adj -= 6
                evaluation["details"].append("Stanza Rule: Saturn influence on 7th -> delay in marriage/union.")
            if sat_on_7 and mars_on_7:
                house_score_adj -= 8
                evaluation["details"].append("Stanza Rule: Mars+Saturn afflict 7th -> quarrels/friction in relationships.")
            fifth_lord_extra = SIGN_LORDS[(ref_sign + 4) % 12]
            seventh_lord_extra = SIGN_LORDS[(ref_sign + 6) % 12]
            rel_5_7 = get_planet_relationship(fifth_lord_extra, self.planets[fifth_lord_extra], seventh_lord_extra, self.planets[seventh_lord_extra])
            if rel_5_7 and rel_5_7["is_applying"] and rel_5_7["is_friendly"]:
                house_score_adj += 8
                evaluation["details"].append("Stanza Rule: Favorable 5th-7th connection -> emotional attachment/love-marriage support.")

        # Stanza 117/123: 1st-10th career growth vs 10th linked to 8th/12th instability
        if house_num == 10:
            tenth_lord_extra = SIGN_LORDS[(ref_sign + 9) % 12]
            rel_1_10 = get_planet_relationship(lagnapathi, self.planets[lagnapathi], tenth_lord_extra, self.planets[tenth_lord_extra])
            tenth_sign_extra = get_sign(self.planets[tenth_lord_extra]["longitude"])
            if rel_1_10 and rel_1_10["is_applying"] and rel_1_10["is_friendly"]:
                house_score_adj += 10
                evaluation["details"].append("Stanza Rule: Favorable 1st-10th relation -> career growth and ambition fulfillment.")
            if tenth_sign_extra in [(ref_sign + 7) % 12, (ref_sign + 11) % 12]:
                house_score_adj -= 10
                evaluation["details"].append("Stanza Rule: 10th-lord linked to 8th/12th axis -> profession change/instability signal.")

        # Stanza 142: 12th-lord favorable with 9th/7th -> foreign travel/residence
        if house_num in [9, 12]:
            twelfth_lord_extra = SIGN_LORDS[(ref_sign + 11) % 12]
            ninth_lord_extra = SIGN_LORDS[(ref_sign + 8) % 12]
            seventh_lord_extra = SIGN_LORDS[(ref_sign + 6) % 12]
            rel_12_9 = get_planet_relationship(twelfth_lord_extra, self.planets[twelfth_lord_extra], ninth_lord_extra, self.planets[ninth_lord_extra])
            rel_12_7 = get_planet_relationship(twelfth_lord_extra, self.planets[twelfth_lord_extra], seventh_lord_extra, self.planets[seventh_lord_extra])
            if (rel_12_9 and rel_12_9["is_applying"] and rel_12_9["is_friendly"]) or (rel_12_7 and rel_12_7["is_applying"] and rel_12_7["is_friendly"]):
                house_score_adj += 8
                evaluation["details"].append("Stanza Rule: Favorable 12th-lord tie with 9th/7th -> foreign travel/residence support.")

        # Stanza 118: 4th-lord favorable with 11th-lord -> cultivation/agri-profit
        if house_num == 4:
            fourth_lord_extra = SIGN_LORDS[(ref_sign + 3) % 12]
            eleventh_lord_extra = SIGN_LORDS[(ref_sign + 10) % 12]
            rel_4_11 = get_planet_relationship(fourth_lord_extra, self.planets[fourth_lord_extra], eleventh_lord_extra, self.planets[eleventh_lord_extra])
            if rel_4_11 and rel_4_11["is_applying"] and rel_4_11["is_friendly"]:
                house_score_adj += 8
                evaluation["details"].append("Stanza Rule: Favorable 4th-11th relation -> profit through cultivation/land output.")

        # Incorporate Shatpanchasika rules evaluation
        sp_res = evaluate_shatpanchasika(self, house_num)
        evaluation["shatpanchasika_predictions"] = self._filter_shatpanchasika_predictions(
            sp_res["predictions"], active_cat=None, query_text=query_text
        )
        evaluation["details"].extend(sp_res["details"])
        shatpanchasika_adj = sp_res["score_adjustment"]

        # Incorporate special horary rules (Prasna Tantra Ch. III)
        special_adj = 0
        active_cat = self._get_active_special_category(house_num, special_category, query_text)
        evaluation["shatpanchasika_predictions"] = self._filter_shatpanchasika_predictions(
            evaluation["shatpanchasika_predictions"], active_cat, query_text
        )

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
            elif active_cat == "purchase_sale":
                sp_rules_res = evaluate_purchase_sale(self)
            elif active_cat == "women_enquiry":
                sp_rules_res = evaluate_women_enquiry(self)
            elif active_cat == "dreams":
                sp_rules_res = evaluate_dreams(self)
            elif active_cat == "hunting":
                sp_rules_res = evaluate_hunting(self)
            elif active_cat == "incarceration":
                sp_rules_res = evaluate_incarceration(self)
            elif active_cat == "ships":
                sp_rules_res = evaluate_ships(self)
            elif active_cat == "rumours":
                sp_rules_res = evaluate_rumours(self)
            elif active_cat == "sexual_matters":
                sp_rules_res = evaluate_sexual_matters(self)
            else:
                sp_rules_res = None

            if sp_rules_res:
                evaluation["shatpanchasika_predictions"].extend(sp_rules_res["predictions"])
                evaluation["details"].extend(sp_rules_res["details"])
                special_adj = sp_rules_res["score_adjustment"]

        score = max(0, min(100, 50 + score + house_score_adj + shatpanchasika_adj + special_adj))
        evaluation["score_pct"] = score

        # ── Classical YES / NO / MAYBE verdict (Shatpanchasika Ch. I-II) ──────
        if gairikamboola:
            evaluation["verdict"] = "NO"
            evaluation["verdict_reason"] = (
                f"Gairikamboola Yoga detected (compromised Kamboola) — "
                f"although Lagnapathi and Karyesa have Ithasala, the Moon's severe affliction "
                f"spoils the connection and prevents success. [Prasna Tantra Ch. II]"
            )
        elif rel and rel["is_applying"] and rel["is_friendly"]:
            if score >= 80:
                evaluation["verdict"] = "YES"
                evaluation["verdict_reason"] = (
                    f"Ithasala (applying {rel['aspect_type']}) between {lagnapathi} and {karyesa} — "
                    f"friendly aspect, full success. [Shatpanchasika I.3]"
                )
            else:
                evaluation["verdict"] = "YES, but partially"
                evaluation["verdict_reason"] = (
                    f"Ithasala (applying {rel['aspect_type']}) between {lagnapathi} and {karyesa} — "
                    f"friendly but weakened by other factors. Partial success. [Shatpanchasika II.5-8]"
                )
        elif rel and rel["is_applying"] and not rel["is_friendly"]:
            evaluation["verdict"] = "YES, with struggle"
            evaluation["verdict_reason"] = (
                f"Hostile Ithasala ({rel['aspect_type']}) between {lagnapathi} and {karyesa} — "
                f"success is possible but only after obstacles and effort. [Prasna Tantra Ch. II]"
            )
        elif rel and not rel["is_applying"]:
            evaluation["verdict"] = "NO"
            evaluation["verdict_reason"] = (
                f"Easarapha (separating {rel['aspect_type']}) between {lagnapathi} and {karyesa} — "
                f"the opportunity has passed or the matter will not materialise. [Shatpanchasika I.3]"
            )
        elif kamboola or nakta or yamaya:
            yoga_name = "Kamboola" if kamboola else ("Nakta" if nakta else "Yamaya")
            evaluation["verdict"] = "YES, through intermediary"
            evaluation["verdict_reason"] = (
                f"No direct Ithasala, but {yoga_name} Yoga found — matter achievable "
                f"through a third party or after delay. [Prasna Tantra Ch. II — Intermediary Yogas]"
            )
        elif score >= 50:
            evaluation["verdict"] = "MAYBE"
            evaluation["verdict_reason"] = (
                "Mixed indicators — no clear Ithasala or Easarapha. "
                "Benefic placements give some hope but outcome is uncertain."
            )
        else:
            evaluation["verdict"] = "NO"
            evaluation["verdict_reason"] = (
                f"No aspect between {lagnapathi} and {karyesa}, no intermediary Yoga, "
                f"and unfavorable benefic/malefic balance. [Shatpanchasika I.3-4]"
            )

        # Align score and success_probability with the classical verdict to prevent contradictions
        verdict = evaluation["verdict"]
        if verdict == "NO":
            score = min(score, 35)
            evaluation["success_probability"] = "Low / Failure"
        elif verdict == "MAYBE":
            score = min(max(score, 40), 55)
            evaluation["success_probability"] = "Medium / Obstacles"
        elif verdict in ["YES, but partially", "YES, with struggle", "YES, through intermediary"]:
            score = min(max(score, 50), 75)
            evaluation["success_probability"] = "Medium / Obstacles"
        elif verdict == "YES":
            score = max(score, 80)
            evaluation["success_probability"] = "High / Certain"

        evaluation["score_pct"] = score

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

        # 6. Final sincerity gate — overrides everything
        if not sinc_res.get("is_sincere", True):
            evaluation["verdict"] = "CANNOT BE ANSWERED"
            evaluation["verdict_reason"] = (
                "Query is insincere or a test — Prasna Tantra: only a genuine first-time "
                "question produces a valid chart. No verdict can be given."
            )
            evaluation["success_probability"] = "Inconclusive (Insincere Query)"
            evaluation["score_pct"] = 0
            evaluation["timing"] = "Not determinable — query flagged as insincere/test"

        return self._enrich_special_evaluations(evaluation, house_num, query_text)

    def _enrich_special_evaluations(self, evaluation, house_num, query_text):
        evaluation["marriage_analysis"] = None
        evaluation["children_analysis"] = None
        evaluation["wealth_analysis"] = None
        evaluation["health_analysis"] = None
        
        is_marriage = False
        is_children = False
        is_wealth = False
        is_health = False
        
        if query_text:
            q_lower = query_text.lower()
            if any(w in q_lower for w in ["marry", "marriage", "wedding", "spouse", "wife", "husband", "partner", "union"]):
                is_marriage = True
            if any(w in q_lower for w in ["child", "baby", "son", "daughter", "progeny", "pregnancy", "pregnant", "conceive"]):
                is_children = True
            if any(w in q_lower for w in ["money", "wealth", "finance", "rich", "profit", "gain", "gold", "earning", "asset", "salary"]):
                is_wealth = True
            if any(w in q_lower for w in ["health", "illness", "disease", "patient", "sick", "recover", "cure", "medical", "treatment", "pain"]):
                is_health = True
                
        if house_num == 7:
            is_marriage = True
        elif house_num == 5:
            is_children = True
        elif house_num in [2, 11]:
            is_wealth = True
        elif house_num == 6:
            is_health = True
            
        if is_marriage:
            from .marriage import evaluate_marriage_query
            evaluation["marriage_analysis"] = evaluate_marriage_query(self)
        if is_children:
            from .children import evaluate_children_query
            evaluation["children_analysis"] = evaluate_children_query(self)
        if is_wealth:
            from .wealth import evaluate_wealth_query
            evaluation["wealth_analysis"] = evaluate_wealth_query(self)
        if is_health:
            from .health import evaluate_health_query
            evaluation["health_analysis"] = evaluate_health_query(self)
            
        return evaluation

    def evaluate_traveler(self):
        """Evaluates traveling, marching, and return status based on Shatpanchasika."""
        from .traveler import evaluate_traveler_abroad
        return evaluate_traveler_abroad(self)

    def evaluate_miscellaneous(self):
        """Evaluates pregnancy, marriage, thought reading, and rain prospects based on Shatpanchasika."""
        from .miscellaneous import evaluate_miscellaneous_query
        return evaluate_miscellaneous_query(self)

# Helper function to get sign index from longitude
def get_sign(longitude):
    return int(longitude / 30.0) % 12

def aspects_sign(planet_lon, target_sign):
    p_sign = int(planet_lon / 30.0) % 12
    diff = (target_sign - p_sign) % 12
    return diff in [0, 2, 3, 4, 6, 8, 9, 10]
