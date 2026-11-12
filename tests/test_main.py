import io
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import httpx
from google.genai import errors, types

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
    def __init__(self, candidates, prompt_feedback=None, text: str | None = "summary"):
        self.candidates = candidates
        self.prompt_feedback = prompt_feedback
        self.response_id = "response-123"
        self.text = text


class Candidate:
    def __init__(self, finish_reason=None):
        self.finish_reason = finish_reason


class FakeModels:
    def __init__(self, texts):
        self.texts = list(texts)
        self.calls = []

    def generate_content(self, *, model, contents, config=None):
        self.calls.append({"model": model, "contents": contents, "config": config})
        return Response(candidates=[Candidate()], text=self.texts.pop(0))


class FakeFiles:
    def __init__(self, states):
        self.states = list(states)
        self.requested = []

    def get(self, *, name):
        self.requested.append(name)
        return types.File(name=name, state=self.states.pop(0))


class FakeClient:
    def __init__(self, texts, file_states=()):
        self.models = FakeModels(texts)
        self.files = FakeFiles(file_states)


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
        self.assertEqual(get_response_text(Response(candidates=[Candidate()])), "summary")

    def test_reports_a_candidate_without_text(self):
        response = Response(
            candidates=[Candidate(types.FinishReason.SAFETY)], text=None
        )

        with self.assertRaisesRegex(GeminiGenerationError, "SAFETY"):
            get_response_text(response)


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
    def run_summary(
        self,
        texts,
        output_format,
        structured,
        interactive=False,
        answers=(),
        uploaded_file=None,
        file_states=(),
    ):
        client = FakeClient(texts, file_states)
        video = uploaded_file or types.File(
            name="files/cached", state=types.FileState.ACTIVE
        )
        with (
            patch("main.get_client", return_value=client),
            patch("main.GoogleFilesMappingsJson"),
            patch("main.GoogleFilesManager") as manager_cls,
            patch("main.ConsoleOutput") as console,
            patch("main.time.sleep"),
            patch("builtins.input", side_effect=list(answers)),
            redirect_stdout(io.StringIO()),
        ):
            manager_cls.return_value.get_file.return_value = (
                video,
                uploaded_file is not None,
            )
            result = main.summarise_video(
                Path("video.mp4"),
                "prompt",
                output_format,
                structured=structured,
                interactive=interactive,
            )
        return client, console, result

    def test_voice_format_reaches_console_output(self):
        client, console, result = self.run_summary(
            [VALID_STRUCTURED], OutputFormat.VOICE, structured=True
        )

        self.assertIs(console.call_args.args[1], OutputFormat.VOICE)
        self.assertNotIn("# ", result)
        self.assertIn("This video was created by Jane Smith", result)
        config = client.models.calls[0]["config"]
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertIsNotNone(config.response_schema)

    def test_markdown_format_reaches_console_output(self):
        client, console, result = self.run_summary(
            [VALID_STRUCTURED], OutputFormat.MARKDOWN, structured=True
        )

        self.assertIs(console.call_args.args[1], OutputFormat.MARKDOWN)
        self.assertIn("# Creator", result)
        self.assertIsNotNone(client.models.calls[0]["config"].response_schema)

    def test_requests_use_the_configured_model_and_video(self):
        client, _, _ = self.run_summary(
            [VALID_STRUCTURED], OutputFormat.MARKDOWN, structured=True
        )

        call = client.models.calls[0]
        self.assertEqual(call["model"], main.Config.GEMINI_MODEL)
        self.assertEqual(call["contents"][0].name, "files/cached")
        self.assertEqual(call["contents"][1], "prompt")

    def test_custom_prompt_run_skips_structured_response_schema(self):
        client, console, result = self.run_summary(
            ["freeform answer"], OutputFormat.VOICE, structured=False
        )

        self.assertEqual(result, "freeform answer")
        self.assertIs(console.call_args.args[1], OutputFormat.VOICE)
        self.assertIsNone(client.models.calls[0]["config"].response_schema)

    def test_malformed_structured_output_raises_a_generation_error(self):
        with self.assertRaises(GeminiGenerationError):
            self.run_summary(["not json"], OutputFormat.MARKDOWN, structured=True)

    def test_new_upload_is_polled_until_processing_finishes(self):
        uploaded = types.File(name="files/new", state=types.FileState.PROCESSING)

        client, _, _ = self.run_summary(
            ["answer"],
            OutputFormat.MARKDOWN,
            structured=False,
            uploaded_file=uploaded,
            file_states=[types.FileState.PROCESSING, types.FileState.ACTIVE],
        )

        self.assertEqual(client.files.requested, ["files/new", "files/new"])
        self.assertEqual(client.models.calls[0]["contents"][0].name, "files/new")

    def test_reused_upload_is_not_polled(self):
        client, _, _ = self.run_summary(
            ["answer"], OutputFormat.MARKDOWN, structured=False
        )

        self.assertEqual(client.files.requested, [])

    def test_follow_up_questions_send_the_video_with_the_summary(self):
        client, console, result = self.run_summary(
            ["freeform answer", "follow-up answer"],
            OutputFormat.MARKDOWN,
            structured=False,
            interactive=True,
            answers=["Who presents it?", "q"],
        )

        self.assertEqual(result, "freeform answer")
        follow_up = client.models.calls[1]
        self.assertEqual(follow_up["contents"][0].name, "files/cached")
        self.assertIn("Who presents it?", follow_up["contents"][1])
        self.assertIn("freeform answer", follow_up["contents"][1])
        self.assertIsNone(follow_up["config"].response_schema)
        self.assertEqual(console.call_args.args[0], "follow-up answer")


class ClientRetryTests(unittest.TestCase):
    """Drives the real client against a fake HTTP transport."""

    def _generate_with_statuses(self, statuses: list[int]):
        sent = []

        def send(_client, request, **_kwargs):
            status = statuses[len(sent)]
            sent.append(request)
            body = (
                {"candidates": [{"content": {"role": "model", "parts": [{"text": "ok"}]}}]}
                if status == 200
                else {"error": {"code": status, "message": "busy", "status": "UNAVAILABLE"}}
            )
            return httpx.Response(status, json=body, request=request)

        with (
            patch.dict("os.environ", {"API_KEY": "test-key"}),
            patch("httpx.Client.send", send),
            patch("time.sleep"),
        ):
            client = main.get_client()
            try:
                response = client.models.generate_content(
                    model="model", contents=["hi"], config=main.TEXT_CONFIG
                )
            finally:
                client.close()
        return response, sent

    def test_transient_server_errors_are_retried(self):
        response, sent = self._generate_with_statuses([503, 504, 200])

        self.assertEqual(get_response_text(response), "ok")
        self.assertEqual(len(sent), 3)

    def test_gives_up_after_three_attempts(self):
        with self.assertRaises(errors.ServerError):
            self._generate_with_statuses([503, 504, 503, 200])

    def test_client_errors_are_not_retried(self):
        with self.assertRaises(errors.ClientError):
            self._generate_with_statuses([400, 200])


if __name__ == "__main__":
    unittest.main()
