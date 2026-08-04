import unittest

from exceptions import GeminiGenerationBlockedError, GeminiGenerationError
from main import get_response_text


class PromptFeedback:
    def __init__(self, block_reason=None):
        self.block_reason = block_reason


class Response:
    def __init__(self, candidates, prompt_feedback=None, text="summary"):
        self.candidates = candidates
        self.prompt_feedback = prompt_feedback
        self.response_id = "response-123"
        self.text = text


class GeminiResponseTests(unittest.TestCase):
    def test_reports_a_blocked_request_without_accessing_response_text(self):
        response = Response(
            candidates=[], prompt_feedback=PromptFeedback("PROHIBITED_CONTENT")
        )

        with self.assertRaisesRegex(
            GeminiGenerationBlockedError, "PROHIBITED_CONTENT"
        ) as context:
            get_response_text(response)

        self.assertEqual(context.exception.response_id, "response-123")

    def test_reports_an_empty_unblocked_response(self):
        response = Response(candidates=[])

        with self.assertRaises(GeminiGenerationError):
            get_response_text(response)

    def test_returns_text_for_a_normal_response(self):
        self.assertEqual(get_response_text(Response(candidates=[object()])), "summary")


if __name__ == "__main__":
    unittest.main()
