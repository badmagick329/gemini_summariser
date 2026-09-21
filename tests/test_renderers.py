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

    def test_avoids_mechanical_list_transitions(self):
        rendered = render_summary(self.summary, OutputFormat.VOICE)

        self.assertNotIn("First,", rendered)
        self.assertNotIn("Next,", rendered)
        self.assertNotIn("Finally,", rendered)

    def test_joins_key_points_as_natural_sentences(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("one", "two", "three"),
            important_highlight="Improve insulation first.",
            takeaways=("Small changes add up.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn("one. two. three.", rendered)

    def test_contains_no_markdown_syntax(self):
        rendered = render_summary(self.summary, OutputFormat.VOICE)

        assert_no_markdown_syntax(self, rendered)

    def test_does_not_announce_the_highlight_as_a_section(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("Insulation prevents heat loss.",),
            important_highlight="The presenter recommends improving insulation first.",
            takeaways=("Small changes add up.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertNotIn("The most important highlight is this", rendered)
        self.assertIn("The presenter recommends improving insulation first.", rendered)

    def test_turns_a_highlight_fragment_into_a_sentence_without_a_bridge(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("insulation prevents heat loss",),
            important_highlight="improving insulation comes first",
            takeaways=("small changes add up",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn("improving insulation comes first.", rendered)
        self.assertNotIn("The most important highlight", rendered)
        self.assertIn("insulation prevents heat loss.", rendered)

    def test_handles_complete_sentence_key_points(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("The presenter explains insulation.", "She compares systems."),
            important_highlight="Improve insulation first.",
            takeaways=("Small changes add up.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn(
            "The presenter explains insulation. She compares systems.", rendered
        )

    def test_preserves_proper_names_and_acronyms(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("OpenAI released a model.", "Gemini explains the topic."),
            important_highlight="Improve insulation first.",
            takeaways=("US-based research is growing.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn("OpenAI released a model. Gemini explains the topic.", rendered)
        self.assertIn("US-based research is growing.", rendered)

    def test_closes_without_announcing_a_takeaway_section(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="energy",
            key_points=("The presenter explains insulation.", "She compares systems."),
            important_highlight="Improve insulation first.",
            takeaways=("The results are clear.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn(
            "The presenter explains insulation. She compares systems.", rendered
        )
        self.assertIn("The results are clear.", rendered)
        self.assertNotIn("Overall", rendered)
        self.assertNotIn("takeaways are", rendered)

    def test_treats_a_punctuated_topic_as_a_phrase(self):
        summary = VideoSummary(
            creator="Jane Smith",
            topic="household energy efficiency.",
            key_points=("Insulation prevents heat loss.",),
            important_highlight="Improve insulation first.",
            takeaways=("Small changes add up.",),
        )

        rendered = render_summary(summary, OutputFormat.VOICE)

        self.assertIn("It focuses on household energy efficiency.", rendered)

    def test_preserves_the_summary_facts(self):
        rendered = render_summary(self.summary, OutputFormat.VOICE)

        self.assertIn("Jane Smith", rendered)
        self.assertIn("household energy efficiency", rendered)
        self.assertIn("Improve insulation first.", rendered)

    def test_is_connected_prose_split_into_paragraphs(self):
        rendered = render_summary(self.summary, OutputFormat.VOICE)

        self.assertGreaterEqual(len(rendered.split("\n\n")), 3)
        self.assertIn(
            "This video was created by Jane Smith. "
            "It focuses on household energy efficiency.",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
