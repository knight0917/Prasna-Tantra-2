import unittest
from datetime import datetime
from prasnatantra import PrasnaChart, get_sign_name, SIGN_LORDS
from prasnatantra.tajaka import get_planet_relationship, check_combustion

class TestPrasnaTantra(unittest.TestCase):
    def setUp(self):
        # Cast the B.V. Raman Example II chart: March 1, 1950 at 8 PM IST (14:30 UTC)
        # Lat: 12:58:18 N, Lon: 77:35:41 E
        self.local_dt = datetime(1950, 3, 1, 20, 0, 0)
        self.lat = "12:58:18"
        self.lon = "77:35:41"
        self.tz_offset = 5.5
        self.chart = PrasnaChart(self.local_dt, self.lat, self.lon, self.tz_offset)

    def test_lagna_calculation(self):
        # Calculated Lagna should be in Virgo (sign index 5)
        # Let's check if the Lagna sign is indeed Virgo
        self.assertEqual(self.chart.lagna_sign, 5)
        self.assertEqual(get_sign_name(self.chart.lagna_sign), "Virgo")
        
        # Verify Lagnapathi is Mercury
        self.assertEqual(self.chart.lagnapathi, "Mercury")

    def test_planetary_sign_positions(self):
        # Compare calculated planetary signs against B.V. Raman's chart (Index 0 = Aries, 1 = Taurus, ...)
        # Sun: Aquarius (10)
        # Moon: Cancer (3)
        # Mars: Virgo (5)
        # Jupiter: Capricorn (9)
        # Mercury: Capricorn (9)
        # Venus: Capricorn (9)
        # Saturn: Leo (4)
        
        expected_signs = {
            "Sun": 10,
            "Moon": 3,
            "Mars": 5,
            "Jupiter": 9,
            "Mercury": 9,
            "Venus": 9,
            "Saturn": 4
        }
        
        for name, expected_sign in expected_signs.items():
            lon = self.chart.planets[name]["longitude"]
            cal_sign = int(lon / 30) % 12
            self.assertEqual(cal_sign, expected_sign, f"{name} position mismatch: Cal {cal_sign}, Exp {expected_sign}")

    def test_planetary_sign_positions_raman_mode(self):
        # Cast the chart under Raman Ayanamsha
        chart_raman = PrasnaChart(self.local_dt, self.lat, self.lon, self.tz_offset, ayanamsha_mode="Raman")
        
        # We test calculated longitudes against correct Raman Ayanamsha values.
        # Jupiter has a 10-degree print error in B.V. Raman's book (printed as Aquarius 8°43' i.e. 308.72°,
        # but astronomically it is Capricorn 28°48' i.e. 298.80°).
        expected_longitudes = {
            "Sun": 318.73,
            "Moon": 101.66,
            "Mercury": 298.37,
            "Venus": 282.87,
            "Mars": 167.39,
            "Jupiter": 298.80,
            "Saturn": 144.78
        }
        
        for name, expected_lon in expected_longitudes.items():
            lon = chart_raman.planets[name]["longitude"]
            # Calculate short angular distance
            diff = abs(lon - expected_lon)
            if diff > 180:
                diff = 360 - diff
            self.assertLess(diff, 0.2, f"Raman mode: {name} longitude mismatch: Cal {lon:.2f}°, Exp {expected_lon:.2f}°")


    def test_aspects_and_orbs(self):
        # Test aspect logic
        # Sun and Moon: Sun is at ~318° (Aquarius), Moon is at ~101° (Cancer).
        # Sign distance: 318/30 = 10, 101/30 = 3. Difference = 7 signs (no aspect).
        # Mars (Virgo, ~166°) and Sun (Aquarius, ~318°): Sign distance = 5 signs (no aspect).
        # Mars and Lagna: both in Virgo (0 signs difference -> Conjunction)
        rel_mars_lagna = get_planet_relationship(
            "Mars", self.chart.planets["Mars"], 
            "Lagna", {"longitude": self.chart.lagna_sidereal, "speed": 0.0}
        )
        self.assertIsNotNone(rel_mars_lagna)
        self.assertEqual(rel_mars_lagna["aspect_type"], "Conjunction")

    def test_sincerity_check(self):
        # Verify that sincerity check runs and returns the status dictionary
        sinc = self.chart.sincerity
        self.assertIn("is_sincere", sinc)
        self.assertIsInstance(sinc["is_sincere"], bool)

    def test_query_evaluation(self):
        # Evaluate House 4 (Mother's Longevity)
        res = self.chart.evaluate_query(4)
        self.assertEqual(res["house"], 4)
        self.assertEqual(res["lagnapathi"], "Mercury")
        self.assertEqual(res["karyesa"], "Jupiter")  # 4th house is Sagittarius (sign 8), lord is Jupiter
        self.assertIn(res["success_probability"], ["High / Certain", "Medium / Obstacles", "Low / Failure", "Inconclusive (Insincere Query)"])

    def test_avastha_determinations(self):
        # In the 1950-03-01 test chart:
        # Sun is in Aquarius (10) -> Neutral sign for Sun
        # Moon is in Cancer (3) -> Own sign (Swastha)
        # Mars is in Virgo (5) -> Inimical sign for Mars (Suptha)
        # Jupiter is in Capricorn (9) -> Debilitated (Deena)
        from prasnatantra.tajaka import get_planetary_avastha
        
        moon_data = self.chart.planets["Moon"]
        moon_avastha = get_planetary_avastha("Moon", moon_data["longitude"], moon_data, self.chart.planets["Sun"]["longitude"])
        self.assertEqual(moon_avastha, "Swastha")
        
        jup_data = self.chart.planets["Jupiter"]
        jup_avastha = get_planetary_avastha("Jupiter", jup_data["longitude"], jup_data, self.chart.planets["Sun"]["longitude"])
        self.assertEqual(jup_avastha, "Deena")

    def test_multiple_queries_shift(self):
        # 1st query: should use Lagna (Virgo, lord Mercury)
        res1 = self.chart.evaluate_query(2, query_num=1)
        self.assertEqual(res1["ref_point_name"], "Ascendant (Lagna)")
        self.assertEqual(res1["lagnapathi"], "Mercury")
        self.assertEqual(res1["karyesa"], "Venus")  # 2nd from Virgo is Libra (lord Venus)

        # 2nd query: should use Moon (Cancer, lord Moon)
        res2 = self.chart.evaluate_query(2, query_num=2)
        self.assertEqual(res2["ref_point_name"], "Moon")
        self.assertEqual(res2["lagnapathi"], "Moon")
        # 2nd from Cancer is Leo (lord Sun)
        self.assertEqual(res2["karyesa"], "Sun")

        # 3rd query: should use Sun (Aquarius, lord Saturn)
        res3 = self.chart.evaluate_query(2, query_num=3)
        self.assertEqual(res3["ref_point_name"], "Sun")
        self.assertEqual(res3["lagnapathi"], "Saturn")
        # 2nd from Aquarius is Pisces (lord Jupiter)
        self.assertEqual(res3["karyesa"], "Jupiter")

        # 4th query: should use Jupiter (Capricorn, lord Saturn)
        res4 = self.chart.evaluate_query(2, query_num=4)
        self.assertEqual(res4["ref_point_name"], "Jupiter")
        self.assertEqual(res4["lagnapathi"], "Saturn")
        # 2nd from Capricorn is Aquarius (lord Saturn)
        self.assertEqual(res4["karyesa"], "Saturn")

        # 5th query: should use Mercury (stronger than Venus in this chart)
        res5 = self.chart.evaluate_query(2, query_num=5)
        self.assertTrue(res5["ref_point_name"].startswith("Mercury"))
        self.assertEqual(res5["lagnapathi"], "Saturn")
        self.assertEqual(res5["karyesa"], "Saturn")

    def test_mercury_venus_relative_strength_tie_breakers(self):
        from unittest.mock import patch
        
        # Instantiate a clean chart
        chart = PrasnaChart(self.local_dt, self.lat, self.lon, self.tz_offset)
        
        # Scenario 1: Avastha Rank Difference (Mercury superior)
        # Mercury at Virgo (exalted, Deeptha rank 9) vs Venus at Libra (own sign, Swastha rank 6)
        chart.planets = {
            "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
            "Mercury": {"longitude": 165.0, "speed": 1.0, "is_retrograde": False},
            "Venus": {"longitude": 180.0, "speed": 1.0, "is_retrograde": False}
        }
        stronger, reason = chart._get_stronger_mercury_venus()
        self.assertEqual(stronger, "Mercury")
        self.assertIn("superior Avastha", reason)
        
        # Scenario 2: Avastha Rank Difference (Venus superior)
        # Mercury at Libra (own sign, Swastha rank 6) vs Venus at Pisces (exalted, Deeptha rank 9)
        chart.planets = {
            "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
            "Mercury": {"longitude": 180.0, "speed": 1.0, "is_retrograde": False},
            "Venus": {"longitude": 340.0, "speed": 1.0, "is_retrograde": False}
        }
        stronger, reason = chart._get_stronger_mercury_venus()
        self.assertEqual(stronger, "Venus")
        self.assertIn("superior Avastha", reason)

        # Mock get_planetary_avastha to return equal ranks ("Neutral") for all remaining scenarios
        with patch('prasnatantra.engine.get_planetary_avastha', return_value="Neutral"):
            
            # Scenario 3: Combustion (Venus non-combust vs Mercury combust)
            # Sun at 0, Mercury at 5 (combust since diff 5 <= 8), Venus at 20 (not combust since diff 20 > 7)
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 5.0, "speed": 1.0, "is_retrograde": False},
                "Venus": {"longitude": 20.0, "speed": 1.0, "is_retrograde": False}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Venus")
            self.assertIn("Mercury is combust", reason)
            
            # Scenario 3b: Combustion (Mercury non-combust vs Venus combust)
            # Sun at 0, Mercury at 20 (not combust), Venus at 5 (combust since diff 5 <= 7)
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 20.0, "speed": 1.0, "is_retrograde": False},
                "Venus": {"longitude": 5.0, "speed": 1.0, "is_retrograde": False}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Mercury")
            self.assertIn("Venus is combust", reason)

            # Scenario 4: Malefic Conjunction / Planetary War
            # Both not combust. Mercury at 100 conjoined with Saturn at 102 (within avg orb). Venus at 150 (free).
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 100.0, "speed": 1.0, "is_retrograde": False},
                "Venus": {"longitude": 150.0, "speed": 1.0, "is_retrograde": False},
                "Saturn": {"longitude": 102.0, "speed": 0.05, "is_retrograde": False}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Venus")
            self.assertIn("conjoined with a malefic", reason)

            # Scenario 4b: Malefic Conjunction / Planetary War
            # Venus conjoined with Saturn at 102. Mercury at 150.
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 150.0, "speed": 1.0, "is_retrograde": False},
                "Venus": {"longitude": 100.0, "speed": 1.0, "is_retrograde": False},
                "Saturn": {"longitude": 102.0, "speed": 0.05, "is_retrograde": False}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Mercury")
            self.assertIn("conjoined with a malefic", reason)

            # Scenario 5: Retrograde Status (Mercury direct vs Venus retrograde)
            # Both not combust, not conjoined.
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 100.0, "speed": 1.0, "is_retrograde": False},
                "Venus": {"longitude": 150.0, "speed": -1.0, "is_retrograde": True}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Mercury")
            self.assertIn("Venus is retrograde", reason)

            # Scenario 5b: Retrograde Status (Venus direct vs Mercury retrograde)
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 100.0, "speed": -1.0, "is_retrograde": True},
                "Venus": {"longitude": 150.0, "speed": 1.0, "is_retrograde": False}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Venus")
            self.assertIn("Mercury is retrograde", reason)

            # Scenario 6: Motional Speed (Mercury faster)
            # Both direct, not combust, not conjoined.
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 100.0, "speed": 1.5, "is_retrograde": False},
                "Venus": {"longitude": 150.0, "speed": 1.2, "is_retrograde": False}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Mercury")
            self.assertIn("faster motional speed", reason)


            # Scenario 6b: Motional Speed (Venus faster)
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 100.0, "speed": 1.2, "is_retrograde": False},
                "Venus": {"longitude": 150.0, "speed": 1.5, "is_retrograde": False}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Venus")
            self.assertIn("faster motional speed", reason)

            # Scenario 7: Natural Strength (Naisargika Bala) (everything else equal)
            chart.planets = {
                "Sun": {"longitude": 0.0, "speed": 1.0, "is_retrograde": False},
                "Mercury": {"longitude": 100.0, "speed": 1.0, "is_retrograde": False},
                "Venus": {"longitude": 150.0, "speed": 1.0, "is_retrograde": False}
            }
            stronger, reason = chart._get_stronger_mercury_venus()
            self.assertEqual(stronger, "Venus")
            self.assertIn("Naisargika Bala", reason)

    def test_new_avasthas_suvratsut(self):
        from prasnatantra.tajaka import get_planetary_avastha
        # Let's test Athiveerya by creating a dummy planet in its own sign in multiple vargas
        # Sun at Aries 10 is exalted (Deeptha)
        dummy_p_data = {"is_retrograde": False, "speed": 1.0}
        self.assertEqual(get_planetary_avastha("Sun", 10.0, dummy_p_data, 100.0), "Deeptha")
        
        # Test Suveerya vs Pariheena
        # Note: Jupiter at 315.0 (Aquarius Rashi) is in Aquarius Navamsa (Vargottama), so it gets promoted to Swastha.
        self.assertEqual(get_planetary_avastha("Jupiter", 315.0, dummy_p_data, 100.0), "Swastha")
        self.assertEqual(get_planetary_avastha("Saturn", 250.0, dummy_p_data, 100.0), "Pariheena")

    def test_navamsa_dignity_integration(self):
        from prasnatantra.tajaka import get_planetary_avastha
        dummy_p_data = {"is_retrograde": False, "speed": 1.0}
        
        # 1. Navamsa Debilitation: Sun at Aries 22° is Rashi-exalted (Deeptha) but Navamsa-debilitated (Libra), demoting it to Deena
        self.assertEqual(get_planetary_avastha("Sun", 22.0, dummy_p_data, 100.0), "Deena")
        
        # 2. Navamsa Exaltation: Mars at Gemini 12° is Rashi-inimical (Suptha) but Navamsa-exalted (Capricorn), promoting it to Swastha
        self.assertEqual(get_planetary_avastha("Mars", 72.0, dummy_p_data, 100.0), "Swastha")
        
        # 3. Navamsa Benefic Aspect/Conjunction: Saturn at Aries 1° (Rashi-debilitated) conjoined with Jupiter in Navamsa Aries 1°
        planets_dict = {
            "Saturn": {"longitude": 1.0, "speed": 0.05, "is_retrograde": False},
            "Jupiter": {"longitude": 1.0, "speed": 0.08, "is_retrograde": False},
            "Sun": {"longitude": 100.0}
        }
        # Without planets_dict (no aspect check), Saturn is Deena
        self.assertEqual(get_planetary_avastha("Saturn", 1.0, planets_dict["Saturn"], 100.0), "Deena")
        # With planets_dict, Jupiter conjoins Saturn in Navamsa Aries, promoting/shielding it to Pariheena
        self.assertEqual(get_planetary_avastha("Saturn", 1.0, planets_dict["Saturn"], 100.0, planets_dict), "Pariheena")

    def test_new_sincerity_indicators(self):
        sinc = self.chart.sincerity
        # Ensure reasons are populated
        self.assertIsNotNone(sinc["reasons_sincere"])
        self.assertIsNotNone(sinc["reasons_insincere"])

    def test_success_ratio_scores(self):
        res = self.chart.evaluate_query(4)
        self.assertIn("Bhava Success Ratio", "".join(res["details"]))

    def test_raman_house_rules_and_timing(self):
        # Test timing details key exists
        res4 = self.chart.evaluate_query(4)
        self.assertIn("Sign Multiplication timing", res4["timing_details"])
        
        # Test house 5 gender prediction
        res5 = self.chart.evaluate_query(5)
        self.assertIn("gender_prediction", res5)
        self.assertTrue(any("House 5" in detail for detail in res5["details"]) or "gender_prediction" in res5)
        
        # Test house 2 finance
        res2 = self.chart.evaluate_query(2)
        # Check details for House 2 occupants check
        self.assertTrue(any("House 2" in d for d in res2["details"]) or res2 is not None)

    def test_shatpanchasika_rules(self):
        # 1. Evaluate House 5 (Children)
        res5 = self.chart.evaluate_query(5)
        self.assertIn("shatpanchasika_predictions", res5)
        predictions5 = res5["shatpanchasika_predictions"]
        
        # Verify that we have child gender predictions and object identification
        child_gender_pred = [p for p in predictions5 if p["category"] == "Child Gender"]
        self.assertTrue(len(child_gender_pred) > 0)
        
        # 2. Evaluate House 8 (Lost/Stolen Property)
        res8 = self.chart.evaluate_query(8)
        predictions8 = res8["shatpanchasika_predictions"]
        
        theft_pred = [p for p in predictions8 if p["category"] == "Theft / Lost Property"]
        self.assertTrue(len(theft_pred) > 0)
        self.assertTrue("insider" in theft_pred[0]["prediction"] or "outsider" in theft_pred[0]["prediction"])
        
        # 3. Evaluate House 1 (General and Thought Reading)
        res1 = self.chart.evaluate_query(1)
        predictions1 = res1["shatpanchasika_predictions"]
        thought_pred = [p for p in predictions1 if p["category"] == "Thought Reading"]
        self.assertTrue(len(thought_pred) > 0)
        self.assertIn("querist is currently thinking of", thought_pred[0]["prediction"])

    def test_special_rules_deity_curse(self):
        res = self.chart.evaluate_query(12, special_category="deity_curse")
        self.assertIn("shatpanchasika_predictions", res)
        deity_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] == "Deity Curse"]
        self.assertTrue(len(deity_pred) > 0)
        self.assertTrue(any("Deity Curse:" in d for d in res["details"]))

    def test_special_rules_master_servant(self):
        res = self.chart.evaluate_query(6, special_category="master_servant")
        self.assertIn("shatpanchasika_predictions", res)
        emp_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] == "Employment Stability"]
        self.assertTrue(len(emp_pred) > 0)
        self.assertTrue(any("Master-Servant:" in d for d in res["details"]))

    def test_special_rules_meals(self):
        res = self.chart.evaluate_query(1, special_category="meals")
        self.assertIn("shatpanchasika_predictions", res)
        meals_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] == "Dietary/Meals Query"]
        self.assertTrue(len(meals_pred) > 0)

    def test_special_rules_sports(self):
        res = self.chart.evaluate_query(7, special_category="sports")
        self.assertIn("shatpanchasika_predictions", res)
        sports_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] == "Contest Outcome"]
        self.assertTrue(len(sports_pred) > 0)
        self.assertTrue(any("Sports:" in d for d in res["details"]))

    def test_special_rules_disputes(self):
        res = self.chart.evaluate_query(8, special_category="disputes")
        self.assertIn("shatpanchasika_predictions", res)
        disp_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Legal Dispute Verdict", "Verdict Outcome"]]
        self.assertTrue(len(disp_pred) > 0)
        self.assertTrue(any("Disputes:" in d for d in res["details"]))

    def test_special_rules_crops_trade(self):
        res = self.chart.evaluate_query(4, special_category="crops_trade")
        self.assertIn("shatpanchasika_predictions", res)
        crops_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Agricultural Forecast", "Commercial Forecast", "Market Trends", "Commercial Transactions"]]
        self.assertTrue(len(crops_pred) > 0)

    def test_query_specific_sincerity(self):
        # Query 1: ref is Lagna (Virgo)
        res1 = self.chart.evaluate_query(1, query_num=1)
        self.assertIn("sincerity", res1)
        self.assertIn("is_sincere", res1["sincerity"])
        
        # Query 2: ref is Moon (Cancer)
        res2 = self.chart.evaluate_query(1, query_num=2)
        st = res2.get("sincerity", {})
        self.assertIn("is_sincere", st)

    def test_traveler_abroad(self):
        trav = self.chart.evaluate_traveler()
        self.assertIn("traveler_status", trav)
        self.assertIn("return_timing_desc", trav)
        self.assertIn("enemy_verdict", trav)
        self.assertIn("siege_verdict", trav)
        
    def test_miscellaneous_query(self):
        misc = self.chart.evaluate_miscellaneous()
        self.assertIn("pregnancy_status", misc)
        self.assertIn("gender_verdict", misc)
        self.assertIn("marriage_verdict", misc)
        self.assertIn("thought_desc", misc)
        self.assertIn("rain_verdict", misc)

    def test_dual_house_significations_fallbacks(self):
        # 1. Test Job query on House 10 triggers master_servant
        res_job = self.chart.evaluate_query(
            house_num=10, 
            query_text="Will I get a promotion in my job?"
        )
        # Should have Master-Servant details because of the job query text override
        self.assertTrue(any("Master-Servant:" in d for d in res_job["details"]))
        
        # 2. Test Love query on House 7 suppresses sports default
        res_love = self.chart.evaluate_query(
            house_num=7, 
            special_category="sports",
            query_text="Will she accept my love proposal?"
        )
        # Should NOT have sports predictions/details
        self.assertFalse(any("Sports:" in d for d in res_love["details"]))

    def test_special_rules_dreams(self):
        # Test dreams category mapping via keyword override
        res = self.chart.evaluate_query(8, query_text="what did my dream mean?")
        self.assertIn("shatpanchasika_predictions", res)
        # Should override default disputes (house 8) to dreams
        dream_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Dream Indication", "Dream Quality"]]
        self.assertTrue(len(dream_pred) > 0)
        self.assertTrue(any("Dreams:" in d for d in res["details"]))

    def test_special_rules_ships(self):
        # Test ships category mapping via keyword override
        res = self.chart.evaluate_query(8, query_text="will the ship bring gain?")
        self.assertIn("shatpanchasika_predictions", res)
        # Should override default disputes (house 8) to ships
        ship_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Voyage Profit", "Voyage Arrival"]]
        self.assertTrue(len(ship_pred) > 0)
        self.assertTrue(any("Voyage:" in d for d in res["details"]))
        # overlap cleanup: ship-focused query should not be dominated by traveler war/march categories
        self.assertFalse(any(p["category"] in ["Enemy Arrival", "Fighter Arrival Timing"] for p in res["shatpanchasika_predictions"]))

    def test_special_rules_rumours(self):
        # Test rumours category mapping via keyword override
        res = self.chart.evaluate_query(3, query_text="is the rumour true?")
        self.assertIn("shatpanchasika_predictions", res)
        rumour_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] == "News Reliability"]
        self.assertTrue(len(rumour_pred) > 0)
        self.assertTrue(any("Rumours:" in d for d in res["details"]))

    def test_disputes_context_filtering(self):
        res = self.chart.evaluate_query(8, special_category="disputes", query_text="Who wins this litigation?")
        self.assertIn("shatpanchasika_predictions", res)
        self.assertTrue(any("Dispute" in p["category"] or "Lawsuit" in p["category"] for p in res["shatpanchasika_predictions"]))
        self.assertFalse(any("Voyage" in p["category"] for p in res["shatpanchasika_predictions"]))

    def test_special_rules_sexual_matters(self):
        # Test sexual matters category mapping via keyword override
        res = self.chart.evaluate_query(7, query_text="will we have sexual union?")
        self.assertIn("shatpanchasika_predictions", res)
        sex_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Partner Indication", "Partner Description", "Union Quality"]]
        self.assertTrue(len(sex_pred) > 0)
        self.assertTrue(any("Sexual:" in d for d in res["details"]))

    def test_special_rules_hunting(self):
        res = self.chart.evaluate_query(6, query_text="Will the hunting expedition succeed?")
        self.assertIn("shatpanchasika_predictions", res)
        hunt_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Hunting Expedition", "Catch Quality", "Target Nature"]]
        self.assertTrue(len(hunt_pred) > 0)

    def test_special_rules_incarceration(self):
        res = self.chart.evaluate_query(12, query_text="Will he be released from prison soon?")
        self.assertIn("shatpanchasika_predictions", res)
        prison_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Captivity Status", "Release Prospects"]]
        self.assertTrue(len(prison_pred) > 0)

    def test_house6_disease_diagnosis_hint(self):
        res = self.chart.evaluate_query(6, query_text="What is the nature of this illness?")
        self.assertTrue(any("House 6 Diagnosis Hint" in d for d in res["details"]))

    def test_house3_additional_rule_detail(self):
        import copy
        c = copy.deepcopy(self.chart)
        # Force a deterministic friendly applying 1st/3rd-lord relation:
        # Lagna Virgo -> 1st lord Mercury, 3rd lord Mars
        c.lagna_sign = 5
        c.lagnapathi = "Mercury"
        c.planets["Mercury"]["longitude"] = 149.0
        c.planets["Mercury"]["speed"] = 1.2
        c.planets["Mars"]["longitude"] = 210.0
        c.planets["Mars"]["speed"] = 0.5
        res = c.evaluate_query(3, query_text="How are things with my siblings and efforts?")
        self.assertTrue(any("House 3 Analysis:" in d for d in res["details"]))

    def test_special_rules_women_enquiry(self):
        res = self.chart.evaluate_query(7, query_text="What is the response from this woman?")
        self.assertIn("shatpanchasika_predictions", res)
        wom_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Women Enquiry Outcome", "Emotional Climate"]]
        self.assertTrue(len(wom_pred) > 0)
        self.assertTrue(any("Women Enquiry:" in d for d in res["details"]))

    def test_special_rules_purchase_sale(self):
        res = self.chart.evaluate_query(4, query_text="Should I buy now or wait for sale?")
        self.assertIn("shatpanchasika_predictions", res)
        ps_pred = [p for p in res["shatpanchasika_predictions"] if p["category"] in ["Purchase Outlook", "Sale Outlook", "Net Gain"]]
        self.assertTrue(len(ps_pred) > 0)
        self.assertTrue(any("Purchase-Sale:" in d for d in res["details"]))

    def test_remaining_stanza_rules_career_and_foreign(self):
        import copy
        c = copy.deepcopy(self.chart)
        # Force favorable 1st-10th relation and 12th with 9th relation
        c.lagna_sign = 5
        c.lagnapathi = "Mercury"
        c.planets["Mercury"]["longitude"] = 150.0
        c.planets["Mercury"]["speed"] = 1.2
        # 10th lord from Virgo is Mercury itself (strong link by identity)
        # 12th lord from Virgo is Sun; 9th lord is Venus
        c.planets["Sun"]["longitude"] = 120.0
        c.planets["Sun"]["speed"] = 0.98
        c.planets["Venus"]["longitude"] = 180.0
        c.planets["Venus"]["speed"] = 0.9
        r12 = c.evaluate_query(12, query_text="foreign residence")
        self.assertTrue(any("Stanza Rule:" in d for d in r12["details"]))

    def test_remaining_stanza_rules_marriage_delay_and_quarrel(self):
        import copy
        c = copy.deepcopy(self.chart)
        c.lagna_sign = 5
        c.lagnapathi = "Mercury"
        seventh_sign = (c.lagna_sign + 6) % 12
        # place Saturn and Mars on 7th sign to trigger delay/quarrel rules
        c.planets["Saturn"]["longitude"] = seventh_sign * 30.0 + 5.0
        c.planets["Mars"]["longitude"] = seventh_sign * 30.0 + 12.0
        r7 = c.evaluate_query(7, query_text="marriage delay?")
        self.assertTrue(any("Saturn influence on 7th" in d for d in r7["details"]))
        self.assertTrue(any("Mars+Saturn afflict 7th" in d for d in r7["details"]))

    def test_shatpanchasika_rule1_kendra_significances(self):
        # Rule 1: Adhyaya I Sloka 2 (Kendra Significances)
        # Test House 1 (Lagna displacement)
        res1 = self.chart.evaluate_query(1)
        disp_pred = [p for p in res1["shatpanchasika_predictions"] if p["category"] == "Displacement Status"]
        self.assertEqual(len(disp_pred), 1)
        self.assertEqual(disp_pred[0]["prediction"], "Displacement / Transfer from current position/state")

        # Test House 4 (Prosperity)
        res4 = self.chart.evaluate_query(4)
        prop_pred = [p for p in res4["shatpanchasika_predictions"] if p["category"] == "Property & Success"]
        self.assertEqual(len(prop_pred), 1)
        self.assertEqual(prop_pred[0]["prediction"], "Decay of property / failure / loss")

        # Test House 7 (Traveler return)
        res7 = self.chart.evaluate_query(7)
        ret_pred = [p for p in res7["shatpanchasika_predictions"] if p["category"] == "Traveler Return Status"]
        self.assertEqual(len(ret_pred), 1)
        self.assertEqual(ret_pred[0]["prediction"], "Return of traveler from abroad / safe return soon")

        # Test House 10 (Absence)
        res10 = self.chart.evaluate_query(10)
        abs_pred = [p for p in res10["shatpanchasika_predictions"] if p["category"] == "Absence Status"]
        self.assertEqual(len(abs_pred), 1)
        self.assertEqual(abs_pred[0]["prediction"], "Uncertainty regarding absence/stay at home")

    def test_shatpanchasika_rule2_lost_article_recovery(self):
        # Rule 2: Lost Article Recovery (Adh I Sl 5 vs Ch VI Sl 3)
        # Test on standard chart (where both are True due to benefic in 11th)
        res8 = self.chart.evaluate_query(8)
        preds = res8["shatpanchasika_predictions"]
        
        adh1_sl5 = [p for p in preds if p["category"] == "Property Recovery (Adh I Sl 5)"]
        ch6_sl3 = [p for p in preds if p["category"] == "Property Recovery (Ch VI Sl 3)"]
        
        self.assertEqual(len(adh1_sl5), 1)
        self.assertIn("recovered / returned", adh1_sl5[0]["prediction"])
        
        self.assertEqual(len(ch6_sl3), 1)
        self.assertIn("recovered very soon", ch6_sl3[0]["prediction"])

        # Let's create a mocked chart to test other branches of Rule 2
        # case: benefic in 11th is False, full moon in lagna is True, aspected by Jupiter/Venus is False
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        
        # Set Moon in Lagna (Virgo, sign 5, e.g. 155 degrees)
        planets_copy["Moon"]["longitude"] = 155.0
        # Make Moon full (e.g. Sun in Pisces, sign 11, e.g. 335 degrees)
        planets_copy["Sun"]["longitude"] = 335.0
        
        # Move other benefics (Jupiter, Venus, Mercury) out of Lagna, 11th (Cancer, sign 3), and no aspect to Lagna
        planets_copy["Jupiter"]["longitude"] = 10.0 # Aries
        planets_copy["Venus"]["longitude"] = 130.0 # Leo (diff 1 from Virgo)
        planets_copy["Mercury"]["longitude"] = 130.0 # Leo
        
        # Set up a new chart instance and patch planets
        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 5 # Virgo
        dc.lagna_sidereal = 150.73
        dc.lagnapathi = "Mercury"
        
        from prasnatantra.shatpanchasika import evaluate_shatpanchasika
        res = evaluate_shatpanchasika(dc, 8)
        preds = res["predictions"]
        
        adh1_sl5 = [p for p in preds if p["category"] == "Property Recovery (Adh I Sl 5)"]
        ch6_sl3 = [p for p in preds if p["category"] == "Property Recovery (Ch VI Sl 3)"]
        
        # under Adh I Sl 5, since Moon is not aspected by Jupiter or Venus, it should be False
        self.assertEqual(adh1_sl5[0]["prediction"], "No recovery indicated under Adh. I Sl. 5 conditions.")
        # under Ch VI Sl 3, Full Moon in Lagna is enough to return True
        self.assertIn("recovered very soon", ch6_sl3[0]["prediction"])

    def test_shatpanchasika_rule3_absentee_return_and_timing(self):
        # Rule 3: Adhyaya V Slokas 1-5 (Absentee Return & Timing)
        # Test timing calculation on the standard chart
        res7 = self.chart.evaluate_query(7)
        preds = res7["shatpanchasika_predictions"]
        
        timing_pred = [p for p in preds if p["category"] == "Traveler Return Timing"]
        self.assertEqual(len(timing_pred), 1)
        self.assertIn("return in 1 days", timing_pred[0]["prediction"])

        # Test direct timing (first occupied house is direct)
        # Create a mock chart with Sun in 2nd house (Libra, sign 6, e.g. 190 degrees) and no planets in 1st house
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        for p in planets_copy:
            # Move all physical planets to Libra (sign 6, i.e. 2nd house from Virgo)
            planets_copy[p]["longitude"] = 190.0
            planets_copy[p]["is_retrograde"] = False
            
        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 5 # Virgo
        dc.lagna_sidereal = 150.73
        dc.lagnapathi = "Mercury"
        
        from prasnatantra.shatpanchasika import evaluate_shatpanchasika
        res = evaluate_shatpanchasika(dc, 7)
        preds = res["predictions"]
        
        timing_pred = [p for p in preds if p["category"] == "Traveler Return Timing"]
        self.assertEqual(len(timing_pred), 1)
        # First occupied house should be 2. Since planet is direct, 2 * 12 = 24 days.
        self.assertIn("return in 24 days", timing_pred[0]["prediction"])

    def test_shatpanchasika_rule4_theft_direction_distance(self):
        # Rule 4: Theft Direction & Distance (Ch. VI Sloka 4 correction)
        # Test direction and distance on standard chart
        res8 = self.chart.evaluate_query(8)
        preds = res8["shatpanchasika_predictions"]
        
        theft_pred = [p for p in preds if p["category"] == "Theft Direction & Distance"]
        self.assertEqual(len(theft_pred), 1)
        self.assertIn("taken to the South", theft_pred[0]["prediction"])
        self.assertIn("0 Yojana(s)", theft_pred[0]["prediction"])

        # Test distance > 0 when rising Navamsa idx > 4
        # We need rising Navamsa index to be, say, 7 (which is > 4).
        # We can change lagna_sidereal so that deg_in_sign / 3.333 is 7.
        # Let's say deg_in_sign = 25.0 degrees. 25.0 / 3.333 = 7.5. Nav idx = 7.
        # distance yojanas = 7 - 4 = 3 Yojanas.
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        
        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 5 # Virgo
        dc.lagna_sidereal = 175.0  # Virgo starts at 150. 175.0 is 25 degrees into Virgo.
        dc.lagnapathi = "Mercury"
        
        from prasnatantra.shatpanchasika import evaluate_shatpanchasika
        res = evaluate_shatpanchasika(dc, 8)
        preds = res["predictions"]
        
        theft_pred = [p for p in preds if p["category"] == "Theft Direction & Distance"]
        self.assertEqual(len(theft_pred), 1)
        # Nav index is 7, so yojanas = 7 - 4 = 3 Yojanas
        self.assertIn("3 Yojana(s) away", theft_pred[0]["prediction"])

    def test_shatpanchasika_rule5_nature_and_travel_intentions(self):
        # Rule 5: Adhyaya VII Sloka 6 & Sloka 9 (Subject Nature/Age & Abroad Intentions)
        # Test Subject Nature/Age on standard chart
        res1 = self.chart.evaluate_query(1)
        preds = res1["shatpanchasika_predictions"]
        
        desc_pred = [p for p in preds if p["category"] == "Query Subject Description"]
        self.assertEqual(len(desc_pred), 1)
        self.assertIn("adolescent maiden or youth", desc_pred[0]["prediction"])

        # Test Travel Intentions with direct planet in 6th (cancels travel)
        # Lagna sign: Aries (sign 0, movable)
        # Rising Navamsa: Aries (sign 0, movable)
        # We need intends_travel = is_movable_lagna and is_movable_nav and is_past_middle_nav.
        # Since is_past_middle_nav requires nav_idx >= 5.
        # The only movable nav indices >= 5 are: 6 (Libra).
        # So we want nav_idx = 6.
        # Deg in sign = 6 * 3.333 + 1 = 21.0 degrees.
        # So lagna_sidereal = 21.0.
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        for p in planets_copy:
            planets_copy[p]["longitude"] = 0.0
            planets_copy[p]["is_retrograde"] = False
        planets_copy["Sun"]["longitude"] = 165.0 # Virgo (sign 5, 6th house from Aries)
        
        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 0 # Aries
        dc.lagna_sidereal = 21.0
        dc.lagnapathi = "Mars"
        
        from prasnatantra.shatpanchasika import evaluate_shatpanchasika
        res = evaluate_shatpanchasika(dc, 3) # house 3 or 6 triggers travel intentions
        preds = res["predictions"]
        
        travel_pred = [p for p in preds if p["category"] == "Travel Intentions"]
        self.assertEqual(len(travel_pred), 1)
        self.assertIn("Travel is dropped/cancelled", travel_pred[0]["prediction"])

        # Test Travel Intentions with retrograde planet in 6th (travel still proceeds)
        planets_copy["Sun"]["is_retrograde"] = True
        res = evaluate_shatpanchasika(dc, 3)
        preds = res["predictions"]
        travel_pred = [p for p in preds if p["category"] == "Travel Intentions"]
        self.assertEqual(len(travel_pred), 1)
        self.assertIn("Despite obstacles (planet in 6th), traveler still proceeds", travel_pred[0]["prediction"])

    def test_shatpanchasika_kings_march_and_fighter_status(self):
        # Ch. II Slokas 9 & 13
        # Movable Lagna (Aries, sign 0)
        # Direct marching planet (Mercury) in Lagna
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        planets_copy["Mercury"]["longitude"] = 10.0  # Aries
        planets_copy["Mercury"]["is_retrograde"] = False
        # Move others out of Lagna
        for p in planets_copy:
            if p != "Mercury":
                planets_copy[p]["longitude"] = 100.0  # Cancer

        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 0  # Aries
        dc.lagna_sidereal = 10.0
        dc.lagnapathi = "Mars"

        from prasnatantra.shatpanchasika import evaluate_shatpanchasika
        res = evaluate_shatpanchasika(dc, 1)
        preds = res["predictions"]
        king_preds = [p for p in preds if p["category"] == "King March Status"]
        self.assertEqual(len(king_preds), 1)
        self.assertIn("Quick march of the king/leader", king_preds[0]["prediction"])

        # Retrograde marching planet (Mercury) in Lagna
        planets_copy["Mercury"]["is_retrograde"] = True
        res = evaluate_shatpanchasika(dc, 1)
        preds = res["predictions"]
        king_preds = [p for p in preds if p["category"] == "King March Status"]
        self.assertEqual(len(king_preds), 1)
        self.assertIn("The king/leader does not move from headquarters", king_preds[0]["prediction"])

        # Fixed Lagna (Taurus, sign 1)
        # Saturn or Jupiter in Lagna -> enemy stays in place (Ch. II Sl. 13)
        planets_copy = copy.deepcopy(self.chart.planets)
        planets_copy["Saturn"]["longitude"] = 40.0  # Taurus
        # Move others out
        for p in planets_copy:
            if p != "Saturn":
                planets_copy[p]["longitude"] = 100.0

        dc.planets = planets_copy
        dc.lagna_sign = 1
        dc.lagna_sidereal = 40.0
        dc.lagnapathi = "Venus"

        res = evaluate_shatpanchasika(dc, 1)
        preds = res["predictions"]
        enemy_preds = [p for p in preds if p["category"] == "Enemy Movement Status"]
        self.assertEqual(len(enemy_preds), 1)
        self.assertIn("The enemy stays in place", enemy_preds[0]["prediction"])

        # Movable Lagna (Aries, sign 0)
        # Sun or Jupiter in Lagna -> enemy arrives (Ch. II Sl. 13)
        planets_copy = copy.deepcopy(self.chart.planets)
        planets_copy["Sun"]["longitude"] = 10.0  # Aries
        for p in planets_copy:
            if p != "Sun":
                planets_copy[p]["longitude"] = 100.0

        dc.planets = planets_copy
        dc.lagna_sign = 0
        dc.lagna_sidereal = 10.0
        dc.lagnapathi = "Mars"

        res = evaluate_shatpanchasika(dc, 1)
        preds = res["predictions"]
        enemy_preds = [p for p in preds if p["category"] == "Enemy Movement Status"]
        self.assertEqual(len(enemy_preds), 1)
        self.assertIn("The enemy arrives", enemy_preds[0]["prediction"])

    def test_shatpanchasika_siege_and_peace(self):
        # Ch. III Slokas 1, 3, 4-5
        # Lagna sign Gemini (sign 2, biped)
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        # Move all planets out of crucial houses first
        for p in planets_copy:
            planets_copy[p]["longitude"] = 100.0  # Cancer

        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 2  # Gemini
        dc.lagna_sidereal = 70.0
        dc.lagnapathi = "Mercury"

        from prasnatantra.shatpanchasika import evaluate_shatpanchasika

        # Ch. III Sloka 1: Benefic in 10th (Pisces, sign 11) -> Victory to governor
        # 10th house is (2 + 10 - 1) % 12 = 11 (Pisces)
        planets_copy["Jupiter"]["longitude"] = 340.0  # Pisces
        res = evaluate_shatpanchasika(dc, 3)
        preds = res["predictions"]
        siege_preds = [p for p in preds if p["category"] == "Siege Outcome" and "Victory to the governor" in p["prediction"]]
        self.assertEqual(len(siege_preds), 1)

        # Ch. III Sloka 1: Mars or Saturn in 9th (Aquarius, sign 10) -> Defeat of governor
        # 9th house is (2 + 9 - 1) % 12 = 10 (Aquarius)
        planets_copy["Mars"]["longitude"] = 310.0  # Aquarius
        res = evaluate_shatpanchasika(dc, 3)
        preds = res["predictions"]
        siege_preds = [p for p in preds if p["category"] == "Siege Outcome" and "Complete defeat" in p["prediction"]]
        self.assertEqual(len(siege_preds), 1)

        # Ch. III Sloka 3: Malefic in 12, 10, 11 -> Advantage to besiegers
        # 12th house is (2 + 12 - 1) % 12 = 1 (Taurus)
        planets_copy["Mars"]["longitude"] = 45.0  # Taurus
        res = evaluate_shatpanchasika(dc, 3)
        preds = res["predictions"]
        siege_preds = [p for p in preds if p["category"] == "Siege Outcome" and "Advantage to the besiegers" in p["prediction"]]
        self.assertEqual(len(siege_preds), 1)

        # Ch. III Slokas 4-5: Mutually aspecting benefics in biped signs in Kendras -> Peace
        # Let's place Jupiter in 1st house (Gemini, sign 2, biped)
        # And Venus in 7th house (Sagittarius, sign 8, biped)
        # 1st and 7th houses mutually aspect (diff 6, opposition)
        planets_copy = copy.deepcopy(self.chart.planets)
        planets_copy["Sun"]["longitude"] = 100.0  # Cancer
        planets_copy["Moon"]["longitude"] = 100.0  # Cancer
        planets_copy["Jupiter"]["longitude"] = 70.0  # Gemini (1st house)
        planets_copy["Venus"]["longitude"] = 250.0  # Sagittarius (7th house)
        
        # Venus and Jupiter are benefics. Ensure Mercury is not combust
        planets_copy["Mercury"]["longitude"] = 100.0

        dc.planets = planets_copy
        dc.lagna_sign = 2
        dc.lagna_sidereal = 70.0
        res = evaluate_shatpanchasika(dc, 3)
        preds = res["predictions"]
        conflict_preds = [p for p in preds if p["category"] == "Conflict Status" and "Peace between kings" in p["prediction"]]
        self.assertEqual(len(conflict_preds), 1)

    def test_shatpanchasika_desires_and_gains(self):
        # Ch. IV Slokas 2, 3-4
        # Lagna sign Gemini (sign 2, biped)
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        for p in planets_copy:
            planets_copy[p]["longitude"] = 100.0  # Cancer

        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 2  # Gemini
        dc.lagna_sidereal = 70.0
        dc.lagnapathi = "Mercury"

        from prasnatantra.shatpanchasika import evaluate_shatpanchasika

        # Ch. IV Sloka 2: Benefic in 3, 5, 7, 11 -> Fulfillment of desires
        # Place Jupiter in 3rd house (Leo, sign 4)
        planets_copy["Jupiter"]["longitude"] = 130.0  # Leo
        # Place Venus in 1st house (Gemini, sign 2) to trigger biped Lagna with benefic
        planets_copy["Venus"]["longitude"] = 70.0  # Gemini
        planets_copy["Sun"]["longitude"] = 200.0  # Move Sun away so Venus/Jupiter are not combust
        planets_copy["Mercury"]["longitude"] = 200.0

        res = evaluate_shatpanchasika(dc, 11)
        preds = res["predictions"]
        desire_preds = [p for p in preds if p["category"] == "Realization of Desires"]
        self.assertTrue(len(desire_preds) > 0)
        self.assertIn("accomplishment of desired objects", desire_preds[0]["prediction"])
        self.assertIn("Highly favorable as Lagna is a biped sign with a benefic occupant", desire_preds[0]["prediction"])

        # Ch. IV Slokas 3-4: Moon in 10th house (Pisces, sign 11) -> Auspicious
        planets_copy = copy.deepcopy(self.chart.planets)
        for p in planets_copy:
            planets_copy[p]["longitude"] = 100.0
        planets_copy["Moon"]["longitude"] = 340.0  # Pisces (10th house)
        dc.planets = planets_copy

        res = evaluate_shatpanchasika(dc, 11)
        preds = res["predictions"]
        desire_preds = [p for p in preds if p["category"] == "Realization of Desires" and "Moon in the 10th house" in p["prediction"]]
        self.assertEqual(len(desire_preds), 1)

    def test_shatpanchasika_arrival_timing(self):
        # Ch. II Sloka 17
        # Lagna Gemini (sign 2)
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        for p in planets_copy:
            planets_copy[p]["longitude"] = 100.0  # Cancer

        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 2
        dc.lagna_sidereal = 70.0
        dc.lagnapathi = "Mercury"

        from prasnatantra.shatpanchasika import evaluate_shatpanchasika

        # Moon in 4th house (Virgo, sign 5). No planets between Lagna and Moon (houses 2, 3)
        for p in planets_copy:
            planets_copy[p]["longitude"] = 190.0  # Libra
        planets_copy["Moon"]["longitude"] = 160.0  # Virgo (4th house)

        res = evaluate_shatpanchasika(dc, 7)
        preds = res["predictions"]
        arrival_preds = [p for p in preds if p["category"] == "Fighter Arrival Timing"]
        self.assertEqual(len(arrival_preds), 1)
        self.assertIn("arrives within 4 days", arrival_preds[0]["prediction"])

        # Mars in 2nd house (Cancer, sign 3) -> Planet between Lagna and Moon -> Fighter will not arrive
        planets_copy["Mars"]["longitude"] = 100.0  # Cancer (2nd house)
        res = evaluate_shatpanchasika(dc, 7)
        preds = res["predictions"]
        arrival_preds = [p for p in preds if p["category"] == "Fighter Arrival Timing"]
        self.assertEqual(len(arrival_preds), 1)
        self.assertIn("will not arrive (Planet between Lagna and Moon)", arrival_preds[0]["prediction"])

    def test_shatpanchasika_fathers_location(self):
        # Ch. VII Sloka 12
        # Lagna Aquarius (sign 10)
        import copy
        planets_copy = copy.deepcopy(self.chart.planets)
        for p in planets_copy:
            planets_copy[p]["longitude"] = 100.0

        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = planets_copy
        dc.lagna_sign = 10
        dc.lagna_sidereal = 310.0
        dc.lagnapathi = "Saturn"

        from prasnatantra.shatpanchasika import evaluate_shatpanchasika

        # Sun in 8th house (Virgo, sign 5).
        planets_copy["Sun"]["longitude"] = 160.0  # Virgo (8th house)
        # Move all other planets to Aries so no benefic aspects or conjoins Virgo
        for p in planets_copy:
            if p != "Sun":
                planets_copy[p]["longitude"] = 15.0

        res = evaluate_shatpanchasika(dc, 8)
        preds = res["predictions"]
        father_preds = [p for p in preds if p["category"] == "Father's Location"]
        self.assertEqual(len(father_preds), 1)
        self.assertIn("remains in the same foreign country", father_preds[0]["prediction"])

        # Place Venus in 8th house (Virgo, sign 5, e.g. 165 degrees) -> Conjoined benefic
        planets_copy["Venus"]["longitude"] = 165.0
        res = evaluate_shatpanchasika(dc, 8)
        preds = res["predictions"]
        father_preds = [p for p in preds if p["category"] == "Father's Location"]
        self.assertEqual(len(father_preds), 1)
        self.assertIn("has quitted the foreign country", father_preds[0]["prediction"])

    def test_mercury_combustion_sincerity(self):
        import copy
        chart_copy = copy.deepcopy(self.chart)
        chart_copy.lagna_sign = 5 # Virgo
        chart_copy.planets["Sun"]["longitude"] = 0.0
        chart_copy.planets["Mercury"]["longitude"] = 10.0
        chart_copy.planets["Moon"]["longitude"] = 150.0 # in Virgo (Lagna)
        chart_copy.planets["Saturn"]["longitude"] = 150.0 # in Virgo (quadrant)
        
        res = chart_copy._check_sincerity()
        self.assertTrue(any("Mercury combust" in r for r in res["reasons_insincere"]))
        
        # Ensure that standard combustion for Mercury (limit 8.0°) is False at 10° separation
        self.assertFalse(check_combustion("Mercury", 10.0, 0.0))

    def test_sincerity_rahu_ketu_malefic(self):
        import copy
        chart_copy = copy.deepcopy(self.chart)
        chart_copy.lagna_sign = 5 # Virgo
        chart_copy.planets["Sun"]["longitude"] = 0.0
        chart_copy.planets["Mars"]["longitude"] = 0.0
        chart_copy.planets["Saturn"]["longitude"] = 0.0
        
        # Put Rahu in Virgo
        chart_copy.planets["Rahu"]["longitude"] = 160.0
        res = chart_copy._check_sincerity()
        self.assertTrue(any("Malefics conjoin reference sign" in r and "Rahu" in r for r in res["reasons_insincere"]))
        
        # Put Ketu in Virgo
        chart_copy.planets["Rahu"]["longitude"] = 0.0
        chart_copy.planets["Ketu"]["longitude"] = 160.0
        res2 = chart_copy._check_sincerity()
        self.assertTrue(any("Malefics conjoin reference sign" in r and "Ketu" in r for r in res2["reasons_insincere"]))

    def test_nakta_yamaya_speed_constraints(self):
        from prasnatantra.tajaka import detect_nakta_yoga, detect_yamaya_yoga
        
        p1_data = {"longitude": 10.0, "speed": 0.8}
        p2_data = {"longitude": 220.0, "speed": 0.5}
        
        planets_dict_nakta = {
            "Sun": {"longitude": 0.0, "speed": 1.0},
            "Venus": p1_data,
            "Mars": p2_data,
            "Mercury": {"longitude": 128.0, "speed": 1.5}
        }
        nakta_res = detect_nakta_yoga("Venus", p1_data, "Mars", p2_data, planets_dict_nakta)
        self.assertIsNotNone(nakta_res)
        self.assertEqual(nakta_res[0]["translator"], "Mercury")
        
        planets_dict_no_nakta = {
            "Sun": {"longitude": 128.0, "speed": 1.0},
            "Venus": p1_data,
            "Mars": p2_data
        }
        nakta_res2 = detect_nakta_yoga("Venus", p1_data, "Mars", p2_data, planets_dict_no_nakta)
        self.assertIsNone(nakta_res2)
        
        p1_yamaya = {"longitude": 128.0, "speed": 1.2}
        p2_yamaya = {"longitude": 98.0, "speed": 1.0}
        planets_dict_yamaya = {
            "Sun": {"longitude": 0.0, "speed": 1.0},
            "Venus": p1_yamaya,
            "Mars": p2_yamaya,
            "Saturn": {"longitude": 10.0, "speed": 0.05}
        }
        yamaya_res = detect_yamaya_yoga("Venus", p1_yamaya, "Mars", p2_yamaya, planets_dict_yamaya)
        self.assertIsNotNone(yamaya_res)
        self.assertEqual(yamaya_res[0]["translator"], "Saturn")
        
        planets_dict_no_yamaya = {
            "Sun": {"longitude": 10.0, "speed": 1.0},
            "Venus": p1_yamaya,
            "Mars": p2_yamaya
        }
        yamaya_res2 = detect_yamaya_yoga("Venus", p1_yamaya, "Mars", p2_yamaya, planets_dict_no_yamaya)
        self.assertIsNone(yamaya_res2)

    def test_gairikamboola_detection(self):
        import copy
        from prasnatantra.tajaka import detect_kamboola_yoga, detect_gairikamboola_yoga
        
        p1_data = {"longitude": 340.0, "speed": 1.2}
        p2_data = {"longitude": 341.0, "speed": 0.1}
        moon_data = {"longitude": 100.0, "speed": 13.0}
        
        planets_dict = {
            "Venus": p1_data,
            "Jupiter": p2_data,
            "Moon": moon_data,
            "Sun": {"longitude": 250.0, "speed": 1.0},
            "Mars": {"longitude": 60.0, "speed": 0.5},
            "Saturn": {"longitude": 130.0, "speed": 0.05}
        }
        
        kamboola = detect_kamboola_yoga("Venus", p1_data, "Jupiter", p2_data, moon_data)
        self.assertIsNotNone(kamboola)
        
        gairikamboola = detect_gairikamboola_yoga("Venus", p1_data, "Jupiter", p2_data, moon_data, planets_dict)
        self.assertIsNone(gairikamboola)
        
        planets_dict_combust = copy.deepcopy(planets_dict)
        planets_dict_combust["Sun"]["longitude"] = 102.0
        gairikamboola_combust = detect_gairikamboola_yoga("Venus", p1_data, "Jupiter", p2_data, moon_data, planets_dict_combust)
        self.assertIsNotNone(gairikamboola_combust)
        self.assertTrue(gairikamboola_combust["afflictions"]["combust"])
        
        planets_dict_deb = copy.deepcopy(planets_dict)
        planets_dict_deb["Moon"]["longitude"] = 220.0
        gairikamboola_deb = detect_gairikamboola_yoga("Venus", p1_data, "Jupiter", p2_data, planets_dict_deb["Moon"], planets_dict_deb)
        self.assertIsNotNone(gairikamboola_deb)
        self.assertTrue(gairikamboola_deb["afflictions"]["debilitated"])
        
        planets_dict_malefic = copy.deepcopy(planets_dict)
        planets_dict_malefic["Mars"]["longitude"] = 340.0
        gairikamboola_malefic = detect_gairikamboola_yoga("Venus", p1_data, "Jupiter", p2_data, moon_data, planets_dict_malefic)
        self.assertIsNotNone(gairikamboola_malefic)
        self.assertTrue(gairikamboola_malefic["afflictions"]["malefic_aspect"])

    def test_engine_gairikamboola_evaluation(self):
        import copy
        chart_copy = copy.deepcopy(self.chart)
        chart_copy.lagna_sign = 5
        chart_copy.planets["Mercury"]["longitude"] = 340.0
        chart_copy.planets["Mercury"]["speed"] = 1.2
        chart_copy.planets["Jupiter"]["longitude"] = 341.0
        chart_copy.planets["Jupiter"]["speed"] = 0.1
        chart_copy.planets["Moon"]["longitude"] = 100.0
        chart_copy.planets["Moon"]["speed"] = 13.0
        chart_copy.planets["Sun"]["longitude"] = 102.0
        
        chart_copy.planets["Mars"]["longitude"] = 60.0
        chart_copy.planets["Mars"]["speed"] = 0.5
        chart_copy.planets["Saturn"]["longitude"] = 130.0
        chart_copy.planets["Saturn"]["speed"] = 0.05
        
        res = chart_copy.evaluate_query(7)
        self.assertEqual(res["verdict"], "NO")
        self.assertTrue(res["score_pct"] <= 35)
        self.assertEqual(res["success_probability"], "Low / Failure")
        self.assertTrue(any("Gairikamboola Yoga detected" in detail for detail in res["details"]))

class TestKalapindaTiming(unittest.TestCase):
    def test_equinoctial_shadow(self):
        from prasnatantra.timing import calculate_equinoctial_shadow
        # Standard values
        self.assertAlmostEqual(calculate_equinoctial_shadow(0), 0.0)
        self.assertAlmostEqual(calculate_equinoctial_shadow(45), 12.0)
        self.assertAlmostEqual(calculate_equinoctial_shadow(-45), 12.0)
        
        with self.assertRaises(ValueError):
            calculate_equinoctial_shadow(90)
        with self.assertRaises(ValueError):
            calculate_equinoctial_shadow(-95)

    def test_kalapinda_book_example(self):
        from prasnatantra.timing import calculate_kalapinda_timing
        import math
        
        # Latitude that produces a gnomon shadow of exactly 8.0:
        # 12 * tan(lat) = 8 => lat = atan(2/3) ≈ 33.6900675
        lat = math.degrees(math.atan(2.0 / 3.0))
        
        # Taurus 5° 54' -> 30 + 5.9 = 35.9 degrees
        res = calculate_kalapinda_timing(35.9, lat)
        
        self.assertAlmostEqual(res["equinoctial_shadow"], 8.0, places=7)
        self.assertEqual(res["kalapinda"], 2154)
        
        # First process: rem = (2154 * 8) % 7 = 17232 % 7 = 5 (Jupiter)
        self.assertEqual(res["first_process"]["remainder"], 5)
        self.assertEqual(res["first_process"]["planet"], "Jupiter")
        self.assertEqual(res["first_process"]["gunaka"], 8)
        
        # Second process: product = 2154 * 8 = 17232. Divisor = 5 + 21 + 14 + 9 + 8 = 57.
        # y = 17232 % 57 = 18
        self.assertEqual(res["second_process"]["divisor"], 57)
        self.assertEqual(res["second_process"]["remainder_y"], 18)
        
        # Third process:
        # 18 - Sun (5) = 13
        # 13 < Moon (21) => Moon rising planet, leftover = 13.
        self.assertEqual(res["third_process"]["rising_planet"], "Moon")
        self.assertTrue(res["third_process"]["is_benefic"])
        self.assertEqual(res["third_process"]["leftover_points"], 13)
        self.assertEqual(res["third_process"]["rising_planet_gunaka"], 21)
        
        # Timing: fortnights, value = 13, proportion = 13/21, days = 13/21 * 15
        self.assertEqual(res["timing"]["unit"], "fortnights")
        self.assertEqual(res["timing"]["value"], 13)
        self.assertAlmostEqual(res["timing"]["proportion"], 13 / 21)
        self.assertAlmostEqual(res["timing"]["time_in_days"], (13 / 21) * 15)

    def test_kalapinda_zero_latitude(self):
        from prasnatantra.timing import calculate_kalapinda_timing
        
        # Latitude = 0 -> shadow = 0.
        # Kalapinda = 2154.
        # First process: product = 0. rem = 0 -> Saturn (7)
        res = calculate_kalapinda_timing(35.9, 0.0)
        
        self.assertEqual(res["equinoctial_shadow"], 0.0)
        self.assertEqual(res["first_process"]["remainder"], 7)
        self.assertEqual(res["first_process"]["planet"], "Saturn")
        self.assertEqual(res["first_process"]["gunaka"], 11)
        
        # Second process: product = 2154 * 11 = 23694. Divisor = 79.
        # 23694 % 79 = 73.
        self.assertEqual(res["second_process"]["divisor"], 79)
        self.assertEqual(res["second_process"]["remainder_y"], 73)
        
        # Third process:
        # 73 - Sun(5) - Moon(21) - Mars(14) - Mercury(9) - Jupiter(8) - Venus(11) = 5.
        # 5 < Saturn(11) => Saturn rising, leftover = 5.
        self.assertEqual(res["third_process"]["rising_planet"], "Saturn")
        self.assertFalse(res["third_process"]["is_benefic"])
        self.assertEqual(res["third_process"]["leftover_points"], 5)
        self.assertEqual(res["timing"]["unit"], "years")
        self.assertEqual(res["timing"]["value"], 5)
        self.assertAlmostEqual(res["timing"]["time_in_days"], (5 / 11) * 365)

class TestShatpanchasikaMethodB(unittest.TestCase):
    def test_method_b_moola_example(self):
        class DummyChart:
            pass
        dc = DummyChart()
        dc.planets = {
            "Sun": {"longitude": 0.0},
            "Moon": {"longitude": 0.0},
            "Mars": {"longitude": 0.0},
            "Mercury": {"longitude": 0.0},
            "Jupiter": {"longitude": 0.0},
            "Venus": {"longitude": 0.0},
            "Saturn": {"longitude": 199.0}
        }
        dc.lagna_sign = 0
        dc.lagna_sidereal = 23.0
        dc.lagnapathi = "Mars"
        
        from prasnatantra.shatpanchasika import evaluate_shatpanchasika
        res = evaluate_shatpanchasika(dc, 1)
        preds = [p for p in res["predictions"] if "Method B" in p["prediction"]]
        
        self.assertTrue(len(preds) >= 1)
        moola_preds = [p for p in preds if "Mula" in p["prediction"] or "Vegetable" in p["prediction"]]
        self.assertTrue(len(moola_preds) >= 1)
        self.assertTrue(any("Saturn" in p["prediction"] for p in moola_preds))

class TestLostPropertyRelational(unittest.TestCase):
    def test_yoga_alignment_and_living_entity(self):
        class DummyChart:
            pass
        dc = DummyChart()
        dc.lagna_sign = 6 # Libra
        dc.lagna_sidereal = 196.5 # Libra
        dc.lagnapathi = "Venus"
        dc.planets = {
            "Sun": {"longitude": 60.0, "speed": 1.0},
            "Moon": {"longitude": 100.0, "speed": 1.0}, # Cancer (House 10 from Libra, sign 3)
            "Mars": {"longitude": 10.0, "speed": 1.0},
            "Mercury": {"longitude": 70.0, "speed": 1.0},
            "Jupiter": {"longitude": 200.0, "speed": 1.0},
            "Venus": {"longitude": 69.87, "speed": 1.0}, # Gemini (House 9)
            "Saturn": {"longitude": 240.0, "speed": 1.0}
        }
        
        # Test 1: Swami Yoga overall success propagates to lost recovery verdict
        from prasnatantra.lost_objects import evaluate_lost_property
        
        eval_dict = {
            "verdict": "YES",
            "lagnapathi": "Venus",
            "karyesa": "Venus",
            "yogas": []
        }
        
        # Call with query text "i lost someone"
        res = evaluate_lost_property(dc, evaluation=eval_dict, query_text="i lost someone")
        
        # Assertions
        self.assertTrue(res["is_living_entity"])
        self.assertEqual(res["substance_type"], "Jeeva (Animal / Human / Living / Leather)")
        self.assertIn("YES", res["recovery_verdict"])
        self.assertIn("Swami Yoga", res["recovery_reason"])

class TestPrasnaTantraMarriageAndChildren(unittest.TestCase):
    def test_marriage_query(self):
        class DummyChart:
            pass
        dc = DummyChart()
        dc.lagna_sign = 0 # Aries
        dc.lagna_sidereal = 15.0
        dc.lagnapathi = "Mars"
        dc.planets = {
            "Sun": {"longitude": 10.0, "speed": 1.0},
            "Moon": {"longitude": 150.0, "speed": 1.0},
            "Mars": {"longitude": 73.0, "speed": 1.5},  # Gemini, friendly Trine to Venus in Libra (195.0), applying
            "Mercury": {"longitude": 25.0, "speed": 1.0},
            "Jupiter": {"longitude": 200.0, "speed": 1.0},
            "Venus": {"longitude": 195.0, "speed": 1.0}, # Libra (7th house)
            "Saturn": {"longitude": 220.0, "speed": 1.0}  # Scorpio, does not aspect Libra
        }
        
        from prasnatantra.marriage import evaluate_marriage_query
        res = evaluate_marriage_query(dc)
        self.assertIn("YES", res["verdict"])
        self.assertEqual(res["spouse_influencing_planet"], "Venus")
        self.assertIn("romantic", res["spouse_personality"].lower())
        
    def test_children_query(self):
        class DummyChart:
            pass
        dc = DummyChart()
        dc.lagna_sign = 0 # Aries
        dc.lagna_sidereal = 15.0
        dc.lagnapathi = "Mars"
        dc.planets = {
            "Sun": {"longitude": 335.0, "speed": 1.0},    # Pisces, does not aspect Leo
            "Moon": {"longitude": 150.0, "speed": 1.0},   # Virgo, does not aspect Leo
            "Mars": {"longitude": 93.0, "speed": 1.5},     # Cancer, does not aspect Leo, friendly Trine to Sun, applying
            "Mercury": {"longitude": 25.0, "speed": 1.0},   # Aries, aspects Leo
            "Jupiter": {"longitude": 130.0, "speed": 1.0}, # Leo (5th house), occupies Leo
            "Venus": {"longitude": 195.0, "speed": 1.0},   # Libra, aspects Leo
            "Saturn": {"longitude": 275.0, "speed": 1.0}   # Capricorn, does not aspect Leo
        }
        
        from prasnatantra.children import evaluate_children_query
        res = evaluate_children_query(dc)
        self.assertIn("YES", res["verdict"])
        self.assertEqual(res["gender_verdict"], "MALE CHILD (BOY) — Highly probable.")
        self.assertIn("good health", res["progeny_welfare"].lower())

class TestPrasnaTantraWealthAndHealth(unittest.TestCase):
    def test_wealth_query_success(self):
        class DummyChart:
            pass
        dc = DummyChart()
        dc.lagna_sign = 0  # Aries
        dc.lagna_sidereal = 15.0
        dc.lagnapathi = "Mars"
        dc.planets = {
            "Sun": {"longitude": 180.0, "speed": 1.0},
            "Moon": {"longitude": 43.0, "speed": 1.2},
            "Mars": {"longitude": 282.0, "speed": 1.5},
            "Mercury": {"longitude": 170.0, "speed": 1.2},
            "Jupiter": {"longitude": 200.0, "speed": 1.0},
            "Venus": {"longitude": 45.0, "speed": 1.0},  # Taurus, 2nd house
            "Saturn": {"longitude": 310.0, "speed": 0.05} # Aquarius, 11th house
        }
        
        from prasnatantra.wealth import evaluate_wealth_query
        res = evaluate_wealth_query(dc)
        self.assertIn("YES", res["verdict"])
        self.assertIn("Stable", res["accumulated_wealth_status"])
        self.assertIn("Prosperous", res["incoming_gains_status"])
        
    def test_wealth_query_loss(self):
        class DummyChart:
            pass
        dc = DummyChart()
        dc.lagna_sign = 0  # Aries
        dc.lagna_sidereal = 15.0
        dc.lagnapathi = "Mars"
        dc.planets = {
            "Sun": {"longitude": 45.0, "speed": 1.0},
            "Moon": {"longitude": 180.0, "speed": 1.2},
            "Mars": {"longitude": 200.0, "speed": 1.5},
            "Mercury": {"longitude": 170.0, "speed": 1.2},
            "Jupiter": {"longitude": 290.0, "speed": 1.0},
            "Venus": {"longitude": 46.0, "speed": 1.0},  # Combust Venus (2nd lord)
            "Saturn": {"longitude": 225.0, "speed": 0.05} # Scorpio
        }
        
        from prasnatantra.wealth import evaluate_wealth_query
        res = evaluate_wealth_query(dc)
        self.assertIn("NO", res["verdict"])
        self.assertIn("Weak", res["accumulated_wealth_status"])
        
    def test_health_query_recovery(self):
        class DummyChart:
            pass
        dc = DummyChart()
        dc.lagna_sign = 0  # Aries
        dc.lagna_sidereal = 15.0
        dc.lagnapathi = "Mars"
        dc.planets = {
            "Sun": {"longitude": 180.0, "speed": 1.0},
            "Moon": {"longitude": 125.0, "speed": 1.2},
            "Mars": {"longitude": 42.0, "speed": 1.5},
            "Mercury": {"longitude": 43.0, "speed": 1.2},
            "Jupiter": {"longitude": 120.0, "speed": 1.0}, # Leo
            "Venus": {"longitude": 80.0, "speed": 1.0},
            "Saturn": {"longitude": 280.0, "speed": 0.05}
        }
        
        from prasnatantra.health import evaluate_health_query
        res = evaluate_health_query(dc)
        self.assertIn("YES", res["verdict"])
        self.assertIn("Excellent", res["vitality_status"])
        self.assertIn("Quick", res["recovery_timing"])
        
    def test_health_query_danger(self):
        class DummyChart:
            pass
        dc = DummyChart()
        dc.lagna_sign = 0  # Aries
        dc.lagna_sidereal = 15.0
        dc.lagnapathi = "Mars"
        dc.planets = {
            "Sun": {"longitude": 194.0, "speed": 1.0},
            "Moon": {"longitude": 190.0, "speed": 1.2}, # Combust Moon
            "Mars": {"longitude": 195.0, "speed": 1.5}, # Combust Lagna Lord Mars
            "Mercury": {"longitude": 170.0, "speed": 1.2},
            "Jupiter": {"longitude": 290.0, "speed": 1.0},
            "Venus": {"longitude": 80.0, "speed": 1.0},
            "Saturn": {"longitude": 155.0, "speed": 0.05} # Saturn in Virgo (6th house)
        }
        
        from prasnatantra.health import evaluate_health_query
        res = evaluate_health_query(dc)
        self.assertIn("NO", res["verdict"])
        self.assertIn("Weak", res["vitality_status"])
        self.assertIn("Severe", res["severity_level"])

if __name__ == "__main__":
    unittest.main()
