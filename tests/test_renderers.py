import re
import unittest

from output_format import OutputFormat
from renderers import render_summary
from summary import VideoSummary

HEADING_LINE = re.compile(r"^\s{0,3}#{1,6}\s")
BULLET_LINE = re.compile(r"^\s*([-*+]|\d+\.)\s+")
FENCE_LINE = re.compile(r"^\s*(```|~~~)")
TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")


def assert_no_markdown_syntax(test: unittest.TestCase, text: str) -> None:
    for line in text.splitlines():
        test.assertIsNone(HEADING_LINE.match(line), f"heading: {line!r}")
        test.assertIsNone(BULLET_LINE.match(line), f"bullet: {line!r}")
        test.assertIsNone(FENCE_LINE.match(line), f"fence: {line!r}")
        test.assertIsNone(TABLE_LINE.match(line), f"table: {line!r}")


class MarkdownRendererTests(unittest.TestCase):
    def setUp(self):
        self.summary = VideoSummary(
            creator="Jane Smith",
            topic="household energy efficiency",
            key_points=("Insulation prevents heat loss.", "Heat pumps are efficient."),
            important_highlight="Improve insulation first.",
            takeaways=("Small changes add up.",),
        )

    def test_keeps_the_visible_headings_and_bullet_structure(self):
        rendered = render_summary(self.summary, OutputFormat.MARKDOWN)

        self.assertIn("# Creator", rendered)
        self.assertIn("# Topic Discussed", rendered)
        self.assertIn("# Key points", rendered)
        self.assertIn("# Important Highlight", rendered)
        self.assertIn("# Takeaways", rendered)
        self.assertIn("- Insulation prevents heat loss.", rendered)
        self.assertIn("- Small changes add up.", rendered)

    def test_preserves_the_summary_facts(self):
        rendered = render_summary(self.summary, OutputFormat.MARKDOWN)

        self.assertIn("Jane Smith", rendered)
        self.assertIn("household energy efficiency", rendered)
        self.assertIn("Improve insulation first.", rendered)


class VoiceRendererTests(unittest.TestCase):
    def setUp(self):
        self.summary = VideoSummary(
            creator="Jane Smith",
            topic="household energy efficiency",
            key_points=("Insulation prevents heat loss.", "Heat pumps are efficient."),
            important_highlight="Improve insulation first.",
            takeaways=("Small changes add up.",),
        )

    def test_uses_spoken_transitions(self):
        rendered = render_summary(self.summary, OutputFormat.VOICE)

        self.assertIn("First,", rendered)
        self.assertIn("Finally,", rendered)
        self.assertNotIn("Next,", rendered)

    def test_uses_next_for_middle_points(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("one", "two", "three"),
            important_highlight="Improve insulation first.",
            takeaways=("Small changes add up.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn("First, one.", rendered)
        self.assertIn("Next, two.", rendered)
        self.assertIn("Finally, three.", rendered)

    def test_contains_no_markdown_syntax(self):
        rendered = render_summary(self.summary, OutputFormat.VOICE)

        assert_no_markdown_syntax(self, rendered)

    def test_does_not_glue_a_sentence_onto_a_that_clause(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("Insulation prevents heat loss.",),
            important_highlight="The presenter recommends improving insulation first.",
            takeaways=("Small changes add up.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertNotIn("is that The", rendered)
        self.assertIn(
            "The most important highlight is this. "
            "The presenter recommends improving insulation first.",
            rendered,
        )

    def test_embeds_a_fragment_after_that_cleanly(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("insulation prevents heat loss",),
            important_highlight="improving insulation comes first",
            takeaways=("small changes add up",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn(
            "The most important highlight is that improving insulation comes first.",
            rendered,
        )
        self.assertIn("First, insulation prevents heat loss.", rendered)

    def test_handles_complete_sentence_key_points(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("The presenter explains insulation.", "She compares systems."),
            important_highlight="Improve insulation first.",
            takeaways=("Small changes add up.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn("First, the presenter explains insulation.", rendered)
        self.assertIn("Finally, she compares systems.", rendered)

    def test_preserves_proper_names_and_acronyms_after_a_transition(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("OpenAI released a model.", "Gemini explains the topic."),
            important_highlight="Improve insulation first.",
            takeaways=("US-based research is growing.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn("First, OpenAI released a model.", rendered)
        self.assertIn("Finally, Gemini explains the topic.", rendered)
        self.assertIn("First, US-based research is growing.", rendered)

    def test_lowercases_only_ordinary_sentence_leading_words(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("The presenter explains insulation.", "She compares systems."),
            important_highlight="Improve insulation first.",
            takeaways=("The results are clear.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn("First, the presenter explains insulation.", rendered)
        self.assertIn("Finally, she compares systems.", rendered)
        self.assertIn("First, the results are clear.", rendered)

    def test_preserves_the_summary_facts(self):
        rendered = render_summary(self.summary, OutputFormat.VOICE)

        self.assertIn("Jane Smith", rendered)
        self.assertIn("household energy efficiency", rendered)
        self.assertIn("Improve insulation first.", rendered)

    def test_is_connected_prose_split_into_paragraphs(self):
        rendered = render_summary(self.summary, OutputFormat.VOICE)

        self.assertGreaterEqual(len(rendered.split("\n\n")), 3)
        self.assertIn("This video was created by Jane Smith", rendered)


if __name__ == "__main__":
    unittest.main()
