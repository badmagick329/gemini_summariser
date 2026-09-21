import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from gemini_output import ConsoleOutput, GeminiOutput
from output_format import OutputFormat


class ConsoleOutputTests(unittest.TestCase):
    def test_voice_output_is_printed_without_glow(self):
        buffer = io.StringIO()
        with (
            patch("gemini_output.console_output.subprocess.run") as run,
            redirect_stdout(buffer),
        ):
            ConsoleOutput("spoken narration", OutputFormat.VOICE).write()

        run.assert_not_called()
        self.assertEqual(buffer.getvalue().strip(), "spoken narration")

    def test_markdown_output_is_sent_through_glow(self):
        with patch("gemini_output.console_output.subprocess.run") as run:
            ConsoleOutput("# Heading", OutputFormat.MARKDOWN).write()

        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["glow"])
        self.assertEqual(run.call_args.kwargs["input"], "# Heading")

    def test_markdown_output_falls_back_to_print_without_glow(self):
        buffer = io.StringIO()
        with (
            patch(
                "gemini_output.console_output.subprocess.run",
                side_effect=FileNotFoundError,
            ),
            redirect_stdout(buffer),
        ):
            ConsoleOutput("# Heading", OutputFormat.MARKDOWN).write()

        self.assertIn("# Heading", buffer.getvalue())


class FileOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_markdown_output_uses_md_and_keeps_prompt_and_response(self):
        output = GeminiOutput(
            self.output_dir,
            "video-id",
            "the prompt",
            "# Response",
            OutputFormat.MARKDOWN,
        )

        self.assertEqual(output.output_file.suffix, ".md")
        self.assertIn("# Prompt", output.file_output)
        self.assertIn("the prompt", output.file_output)
        self.assertIn("# Response", output.file_output)

    def test_voice_output_uses_txt_and_contains_only_narration(self):
        output = GeminiOutput(
            self.output_dir,
            "video-id",
            "the prompt",
            "spoken narration",
            OutputFormat.VOICE,
        )

        self.assertEqual(output.output_file.suffix, ".txt")
        self.assertEqual(output.file_output, "spoken narration")

    def test_voice_file_is_written_without_the_prompt(self):
        output = GeminiOutput(
            self.output_dir,
            "video-id",
            "the prompt",
            "spoken narration",
            OutputFormat.VOICE,
        )

        output.write()

        self.assertEqual(output.output_file.read_text(encoding="utf-8"), "spoken narration")
        self.assertNotIn("the prompt", output.output_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
