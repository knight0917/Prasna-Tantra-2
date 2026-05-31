import json
import unittest
from datetime import datetime
from pathlib import Path

from prasnatantra import PrasnaChart


class TestBookCoverageRouting(unittest.TestCase):
    def setUp(self):
        self.chart = PrasnaChart(
            datetime(1950, 3, 1, 20, 0, 0),
            "12:58:18",
            "77:35:41",
            5.5,
        )

    def test_matrix_files_have_zero_unclassified(self):
        root = Path(__file__).resolve().parent
        for name in ["suvratsut_coverage_matrix.json", "neelakanta_coverage_matrix.json"]:
            with self.subTest(matrix=name):
                data = json.loads((root / name).read_text(encoding="utf-8"))
                self.assertEqual(
                    data["unclassified_blocks"], 0, f"{name} still has unresolved blocks"
                )

    def test_high_value_special_category_routing_and_output(self):
        keyword_cases = [
            ("deity_curse", 12, "Is this due to deity curse and divine anger?"),
            ("master_servant", 6, "Will I continue this job service under my master?"),
            ("disputes", 8, "Will I win this litigation dispute?"),
            ("crops_trade", 4, "How will crop trade and harvest go?"),
            ("purchase_sale", 4, "Should I buy now or sell later in this transaction?"),
            ("dreams", 8, "What does this dream indicate?"),
            ("ships", 8, "Will the ship voyage bring cargo safely?"),
            ("rumours", 3, "Is this rumour report true?"),
            ("sexual_matters", 7, "Will we have sexual union?"),
            ("women_enquiry", 7, "What is the response from this woman?"),
            ("hunting", 6, "Will the hunting expedition succeed?"),
            ("incarceration", 12, "Will release from prison custody happen soon?"),
        ]
        for expected_cat, house_num, query_text in keyword_cases:
            with self.subTest(category=expected_cat):
                active = self.chart._get_active_special_category(house_num, None, query_text)
                self.assertEqual(active, expected_cat)
                res = self.chart.evaluate_query(house_num, query_text=query_text)
                self.assertGreater(
                    len(res.get("shatpanchasika_predictions", [])),
                    0,
                    f"No predictions returned for {expected_cat}",
                )

        explicit_cases = [
            ("meals", 1, "What food did I eat today?"),
            ("sports", 7, "Will my team win this contest?"),
        ]
        for explicit_cat, house_num, query_text in explicit_cases:
            with self.subTest(category=explicit_cat):
                res = self.chart.evaluate_query(
                    house_num, special_category=explicit_cat, query_text=query_text
                )
                self.assertGreater(
                    len(res.get("shatpanchasika_predictions", [])),
                    0,
                    f"No predictions returned for explicit category {explicit_cat}",
                )


if __name__ == "__main__":
    unittest.main()

