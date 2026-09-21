import json
import unittest

from exceptions import GeminiGenerationError
from summary import VideoSummary, parse_summary

VALID = {
    "creator": "Jane Smith",
    "topic": "household energy efficiency",
    "key_points": ["Insulation prevents heat loss.", "Heat pumps are efficient."],
    "important_highlight": "Improve insulation before replacing the heating system.",
    "takeaways": ["Small changes add up."],
}


class ParseSummaryTests(unittest.TestCase):
    def test_parses_a_complete_structured_summary(self):
        summary = parse_summary(json.dumps(VALID))

        self.assertEqual(
            summary,
            VideoSummary(
                creator="Jane Smith",
                topic="household energy efficiency",
                key_points=("Insulation prevents heat loss.", "Heat pumps are efficient."),
                important_highlight=(
                    "Improve insulation before replacing the heating system."
                ),
                takeaways=("Small changes add up.",),
            ),
        )

    def test_rejects_missing_fields(self):
        incomplete = {key: VALID[key] for key in VALID if key != "takeaways"}

        with self.assertRaisesRegex(GeminiGenerationError, "takeaways"):
            parse_summary(json.dumps(incomplete))

    def test_rejects_blank_required_text(self):
        broken = {**VALID, "creator": "   "}

        with self.assertRaisesRegex(GeminiGenerationError, "creator"):
            parse_summary(json.dumps(broken))

    def test_rejects_an_empty_list_field(self):
        broken = {**VALID, "key_points": []}

        with self.assertRaisesRegex(GeminiGenerationError, "key_points"):
            parse_summary(json.dumps(broken))

    def test_rejects_non_string_list_entries(self):
        broken = {**VALID, "takeaways": ["ok", 3]}

        with self.assertRaisesRegex(GeminiGenerationError, "takeaways"):
            parse_summary(json.dumps(broken))

    def test_rejects_malformed_json(self):
        with self.assertRaisesRegex(GeminiGenerationError, "valid JSON"):
            parse_summary("not json at all")

    def test_rejects_a_non_object_payload(self):
        with self.assertRaisesRegex(GeminiGenerationError, "JSON object"):
            parse_summary(json.dumps(["creator", "topic"]))


if __name__ == "__main__":
    unittest.main()
