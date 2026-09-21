import io
import json
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

import main
from exceptions import GeminiGenerationBlockedError, GeminiGenerationError
from main import get_args, get_response_text
from output_format import OutputFormat

VALID_STRUCTURED = json.dumps(
    {
        "creator": "Jane Smith",
        "topic": "household energy efficiency",
        "key_points": ["Insulation prevents heat loss.", "Heat pumps are efficient."],
        "important_highlight": "Improve insulation first.",
        "takeaways": ["Small changes add up."],
    }
)


class PromptFeedback:
    def __init__(self, block_reason=None):
        self.block_reason = block_reason


class Response:
    def __init__(self, candidates, prompt_feedback=None, text="summary"):
        self.candidates = candidates
        self.prompt_feedback = prompt_feedback
        self.response_id = "response-123"
        self.text = text


class FakeModel:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def generate_content(self, contents, **kwargs):
        self.calls.append((contents, kwargs))
        return Response(candidates=[object()], text=self.text)


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


class ArgumentParsingTests(unittest.TestCase):
    def parse(self, argv):
        with patch.object(sys, "argv", ["main.py", *argv]):
            return get_args()

    def test_default_format_is_markdown(self):
        args = self.parse(["VIDEO"])

        self.assertIs(args.output_format, OutputFormat.MARKDOWN)
        self.assertIsNone(args.prompt)

    def test_explicit_markdown_format(self):
        args = self.parse(["VIDEO", "--format", "markdown"])

        self.assertIs(args.output_format, OutputFormat.MARKDOWN)

    def test_voice_format(self):
        args = self.parse(["VIDEO", "--format", "voice"])

        self.assertIs(args.output_format, OutputFormat.VOICE)

    def test_invalid_format_is_rejected(self):
        with (
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit),
        ):
            self.parse(["VIDEO", "--format", "mp3"])

    def test_custom_positional_prompt_is_joined(self):
        args = self.parse(["VIDEO", "Give", "me", "bullets"])

        self.assertEqual(args.prompt, "Give me bullets")


class SummariseVideoTests(unittest.TestCase):
    def run_summary(self, text, output_format, structured):
        model = FakeModel(text)
        with (
            patch("main.get_model", return_value=model),
            patch("main.GoogleFilesMappingsJson"),
            patch("main.GoogleFilesManager") as manager_cls,
            patch("main.ConsoleOutput") as console,
        ):
            manager_cls.return_value.get_file.return_value = (object(), False)
            result = main.summarise_video(
                Path("video.mp4"),
                "prompt",
                output_format,
                structured=structured,
                interactive=False,
            )
        return model, console, result

    def test_voice_format_reaches_console_output(self):
        model, console, result = self.run_summary(
            VALID_STRUCTURED, OutputFormat.VOICE, structured=True
        )

        self.assertIs(console.call_args.args[1], OutputFormat.VOICE)
        self.assertNotIn("# ", result)
        self.assertIn("This video was created by Jane Smith", result)
        self.assertIn("generation_config", model.calls[0][1])

    def test_markdown_format_reaches_console_output(self):
        model, console, result = self.run_summary(
            VALID_STRUCTURED, OutputFormat.MARKDOWN, structured=True
        )

        self.assertIs(console.call_args.args[1], OutputFormat.MARKDOWN)
        self.assertIn("# Creator", result)
        self.assertIn("generation_config", model.calls[0][1])

    def test_custom_prompt_run_skips_structured_response_schema(self):
        model, console, result = self.run_summary(
            "freeform answer", OutputFormat.VOICE, structured=False
        )

        self.assertEqual(result, "freeform answer")
        self.assertIs(console.call_args.args[1], OutputFormat.VOICE)
        self.assertNotIn("generation_config", model.calls[0][1])

    def test_malformed_structured_output_raises_a_generation_error(self):
        with self.assertRaises(GeminiGenerationError):
            self.run_summary("not json", OutputFormat.MARKDOWN, structured=True)


if __name__ == "__main__":
    unittest.main()
