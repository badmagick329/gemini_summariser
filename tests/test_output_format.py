import unittest

from output_format import OutputFormat


class OutputFormatTests(unittest.TestCase):
    def test_markdown_is_the_default_suffix_and_is_not_voice(self):
        self.assertEqual(OutputFormat.MARKDOWN.suffix, ".md")
        self.assertFalse(OutputFormat.MARKDOWN.is_voice)

    def test_voice_uses_txt_suffix(self):
        self.assertEqual(OutputFormat.VOICE.suffix, ".txt")
        self.assertTrue(OutputFormat.VOICE.is_voice)

    def test_values_match_cli_choices(self):
        self.assertEqual(
            [output_format.value for output_format in OutputFormat],
            ["markdown", "voice"],
        )


if __name__ == "__main__":
    unittest.main()
