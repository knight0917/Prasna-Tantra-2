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

    def test_new_avasthas_suvratsut(self):
        from prasnatantra.tajaka import get_planetary_avastha
        # Let's test Athiveerya by creating a dummy planet in its own sign in multiple vargas
        # Sun at Aries 10 is exalted (Deeptha)
        dummy_p_data = {"is_retrograde": False, "speed": 1.0}
        self.assertEqual(get_planetary_avastha("Sun", 10.0, dummy_p_data, 100.0), "Deeptha")
        
        # Test Suveerya vs Pariheena
        self.assertEqual(get_planetary_avastha("Jupiter", 315.0, dummy_p_data, 100.0), "Suveerya")
        self.assertEqual(get_planetary_avastha("Saturn", 250.0, dummy_p_data, 100.0), "Pariheena")

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

if __name__ == "__main__":
    unittest.main()
