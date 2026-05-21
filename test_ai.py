import unittest
from unittest.mock import patch, MagicMock
from prasnatantra.ai import load_groq_key, map_question_to_house, generate_astrological_reading

class TestAIIntegration(unittest.TestCase):
    
    @patch('os.environ.get')
    def test_load_groq_key_from_env(self, mock_env_get):
        mock_env_get.return_value = "env_key_test_123"
        key = load_groq_key()
        self.assertEqual(key, "env_key_test_123")
        
    @patch('requests.post')
    def test_map_question_to_house(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"house": 10, "category_name": "Career", "explanation": "Question pertains to job/career change."}'
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Force a dummy key
        with patch('prasnatantra.ai.load_groq_key', return_value="dummy_key"):
            res = map_question_to_house("Will I get a promotion next week?")
            self.assertEqual(res["house"], 10)
            self.assertEqual(res["category_name"], "Career")
            self.assertIn("job/career", res["explanation"])

    @patch('requests.post')
    def test_generate_astrological_reading(self, mock_post):
        mock_response = MagicMock()
        # Mock SSE response streaming lines
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "Astrological "}}]}',
            b'data: {"choices": [{"delta": {"content": "interpretation: Favorable prospects predicted."}}]}',
            b'data: [DONE]'
        ]
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        dummy_chart = {
            "house": 10,
            "ref_point_name": "Ascendant (Lagna)",
            "ref_sign_name": "Virgo",
            "query_sign_name": "Gemini",
            "lagnapathi": "Mercury",
            "karyesa": "Mercury",
            "success_probability": "Very High",
            "score_pct": 100,
            "timing": "Immediate",
            "details": ["Lagnapathi and Karyesa are same planet"],
            "direct_relationship": None,
            "yogas": []
        }
        
        with patch('prasnatantra.ai.load_groq_key', return_value="dummy_key"):
            reading_gen = generate_astrological_reading("Will my project succeed?", dummy_chart)
            reading = "".join(list(reading_gen))
            self.assertIn("Astrological interpretation", reading)

if __name__ == "__main__":
    unittest.main()
