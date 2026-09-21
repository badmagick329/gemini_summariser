import unittest

from output_format import OutputFormat
from prompts import Prompts


class SummaryRequestTests(unittest.TestCase):
    def test_requests_the_structured_json_contract(self):
        request = Prompts.summary_request()

        self.assertIn("single JSON object", request)
        for field in (
            "creator",
            "topic",
            "key_points",
            "important_highlight",
            "takeaways",
        ):
            self.assertIn(f'"{field}"', request)

    def test_is_format_neutral(self):
        request = Prompts.summary_request()

        self.assertNotIn("<OutputFormat", request)
        self.assertNotIn("plain text meant to be read aloud", request)

    def test_includes_neutral_clarity_requirements(self):
        request = Prompts.summary_request()

        self.assertIn("abbreviations", request)
        self.assertIn("percent", request)
        self.assertIn("degrees Celsius", request)
        self.assertIn("dates", request)
        self.assertIn("read aloud", request)


class CustomRequestTests(unittest.TestCase):
    def test_keeps_the_user_prompt_and_adds_markdown_instructions(self):
        request = Prompts.custom_request("Give me three bullets", OutputFormat.MARKDOWN)

        self.assertIn("Give me three bullets", request)
        self.assertIn('name="markdown"', request)
        self.assertNotIn('name="voice"', request)

    def test_keeps_the_user_prompt_and_adds_voice_instructions(self):
        request = Prompts.custom_request("Give me three bullets", OutputFormat.VOICE)

        self.assertIn("Give me three bullets", request)
        self.assertIn('name="voice"', request)
        self.assertIn('"First,"', request)

    def test_the_two_formats_produce_different_contracts(self):
        markdown = Prompts.custom_request("p", OutputFormat.MARKDOWN)
        voice = Prompts.custom_request("p", OutputFormat.VOICE)

        self.assertNotEqual(markdown, voice)

    def test_markdown_custom_request_does_not_require_summary_headings(self):
        request = Prompts.custom_request("p", OutputFormat.MARKDOWN)

        for heading in (
            "# Creator",
            "# Topic Discussed",
            "# Key points",
            "# Important Highlight",
            "# Takeaways",
        ):
            self.assertNotIn(heading, request)

    def test_markdown_custom_request_still_gets_a_general_contract(self):
        request = Prompts.custom_request("p", OutputFormat.MARKDOWN)

        self.assertIn('name="markdown"', request)
        self.assertIn("Markdown", request)
        self.assertIn("headings or lists only where they genuinely help", request)


class FollowUpTests(unittest.TestCase):
    def test_includes_previous_summary_question_and_format_contract(self):
        prompt = Prompts.follow_up(
            "the earlier summary", "What about cost?", OutputFormat.VOICE
        )

        self.assertIn("the earlier summary", prompt)
        self.assertIn("What about cost?", prompt)
        self.assertIn('name="voice"', prompt)

    def test_markdown_follow_up_uses_markdown_contract(self):
        prompt = Prompts.follow_up("s", "q", OutputFormat.MARKDOWN)

        self.assertIn('name="markdown"', prompt)

    def test_markdown_follow_up_does_not_require_summary_headings(self):
        prompt = Prompts.follow_up("s", "q", OutputFormat.MARKDOWN)

        for heading in (
            "# Creator",
            "# Topic Discussed",
            "# Key points",
            "# Important Highlight",
            "# Takeaways",
        ):
            self.assertNotIn(heading, prompt)

    def test_markdown_follow_up_still_gets_a_general_contract(self):
        prompt = Prompts.follow_up("s", "q", OutputFormat.MARKDOWN)

        self.assertIn('name="markdown"', prompt)
        self.assertIn("Markdown", prompt)
        self.assertIn("headings or lists only where they genuinely help", prompt)


if __name__ == "__main__":
    unittest.main()
