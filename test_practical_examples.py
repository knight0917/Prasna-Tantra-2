import unittest
from datetime import datetime

from prasnatantra import PrasnaChart
from prasnatantra.lost_objects import evaluate_lost_property


EXAMPLES = [
    {
        "name": "Example I - Becoming Rich",
        "dt": datetime(1950, 10, 20, 21, 0, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 5.5,
        "house": 2,
        "expected_verdict": "YES, with struggle",
    },
    {
        "name": "Example II - Mother's Longevity",
        "dt": datetime(1950, 3, 1, 20, 0, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 5.5,
        "house": 4,
        "expected_verdict": "YES, with struggle",
    },
    {
        "name": "Example III - Getting a Child",
        "dt": datetime(1947, 9, 9, 12, 25, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 5.5,
        "house": 5,
        "expected_verdict": "MAYBE",
    },
    {
        "name": "Example IV - Absent Person Alive",
        "dt": datetime(1942, 7, 1, 20, 15, 0),
        "lat": "18.97",
        "lon": "72.83",
        "tz": 5.5,
        "house": 5,
        "expected_verdict": "YES, with struggle",
    },
    {
        "name": "Example V - Illness",
        "dt": datetime(1964, 5, 27, 18, 20, 0),
        "lat": "28.6",
        "lon": "77.2",
        "tz": 5.5,
        "house": 6,
        "expected_verdict": "YES",
    },
    {
        "name": "Example VI - Marriage",
        "dt": datetime(1962, 11, 6, 9, 20, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 6.5,
        "house": 7,
        "expected_verdict": "MAYBE",
    },
    {
        "name": "Example VII - End of Strike",
        "dt": datetime(1968, 9, 2, 14, 10, 0),
        "lat": "13.07",
        "lon": "80.28",
        "tz": 5.5,
        "house": 7,
        "expected_verdict": "MAYBE",
    },
    {
        "name": "Example VIII - Recovery of Stolen Property",
        "dt": datetime(1942, 3, 14, 8, 15, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 5.5,
        "house": 8,
        "expected_verdict": "YES",
    },
    {
        "name": "Example IX - Outcome of Law Suit",
        "dt": datetime(1963, 12, 1, 10, 15, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 5.5,
        "house": 7,
        "expected_verdict": "NO",
    },
    {
        "name": "Example X - Foreign Travel",
        "dt": datetime(1957, 3, 1, 10, 25, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 5.5,
        "house": 9,
        "expected_verdict": "MAYBE",
    },
    {
        "name": "Example XI - Leaving Present Job",
        "dt": datetime(1968, 12, 10, 10, 25, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 5.5,
        "house": 10,
        "expected_verdict": "MAYBE",
    },
    {
        "name": "Example XII - Profession",
        "dt": datetime(1949, 5, 5, 14, 0, 0),
        "lat": "12.9717",
        "lon": "77.5945",
        "tz": 5.5,
        "house": 10,
        "expected_verdict": "NO",
    },
]


class TestPracticalBookExamples(unittest.TestCase):
    def test_example_regression_verdicts(self):
        """
        Practical-case guardrail:
        verifies that the 12 well-known B.V. Raman examples stay aligned at
        the yes/no outcome-bucket level after code changes.
        """
        for ex in EXAMPLES:
            with self.subTest(example=ex["name"]):
                chart = PrasnaChart(
                    local_datetime=ex["dt"],
                    lat_str=ex["lat"],
                    lon_str=ex["lon"],
                    tz_offset_hours=ex["tz"],
                    ayanamsha_mode="Raman",
                )
                res = chart.evaluate_query(ex["house"], query_text=ex["name"])
                verdict = res["verdict"]
                self.assertEqual(
                    verdict,
                    ex["expected_verdict"],
                    f"{ex['name']} verdict regression: got '{verdict}'",
                )

    def test_example_viii_recovery_signal(self):
        """
        Book example VIII specifically expects recovery of stolen property.
        Validate the dedicated lost-property module agrees with the main verdict.
        """
        ex = next(x for x in EXAMPLES if "VIII" in x["name"])
        chart = PrasnaChart(
            local_datetime=ex["dt"],
            lat_str=ex["lat"],
            lon_str=ex["lon"],
            tz_offset_hours=ex["tz"],
            ayanamsha_mode="Raman",
        )
        eval_res = chart.evaluate_query(8, query_text="diamond ring stolen from home")
        lost_res = evaluate_lost_property(
            chart, evaluation=eval_res, query_text="diamond ring stolen from home"
        )
        self.assertIn("YES", lost_res["recovery_verdict"])


if __name__ == "__main__":
    unittest.main()
