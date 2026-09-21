from output_format import OutputFormat


class Prompts:
    """Compose generation prompts from content, structure, and format parts.

    Built-in summaries are requested as a format-neutral JSON contract so that
    one parsed summary can be rendered to any output format. Custom prompts and
    follow-up questions stay freeform, so the selected format instructions are
    appended to their content request instead.
    """

    @staticmethod
    def content_instructions() -> str:
        return """<ContentRequirements>
Carefully watch and understand the video and provide:
1. Who seems to be the creator of the video.
2. The main topic discussed in the video.
3. The key points mentioned in the video, summarised clearly.
4. Anything important about the video that should be mentioned.
5. The information from the video that is useful to learn or know, if any.
</ContentRequirements>"""

    @staticmethod
    def structured_instructions() -> str:
        return """<ResponseFormat>
Respond with a single JSON object and nothing else. Do not use Markdown, code fences, or commentary.
The object must match this shape:
{
  "creator": "who created the video, or unknown",
  "topic": "the main topic",
  "key_points": ["key point 1", "key point 2"],
  "important_highlight": "the single most important thing to mention",
  "takeaways": ["useful thing to know 1", "useful thing to know 2"]
}
Every field is required. Use non-empty strings, and at least one entry in each list.
</ResponseFormat>"""

    @staticmethod
    def quality_instructions() -> str:
        return """<QualityRequirements>
- Use clear language that is easy to follow.
- Do not miss key details. Elaborate when something needs more explanation.
- Provide enough information that watching the video is not necessary.
- Avoid including raw URLs unless a link is essential.
- Expand ambiguous abbreviations at first mention where practical.
- Write symbols and units in clear words, such as "percent" and "degrees Celsius".
- Use unambiguous, naturally readable dates.
- Keep numeric expressions clear when they are read aloud.
</QualityRequirements>"""

    @staticmethod
    def markdown_instructions() -> str:
        return """<OutputFormat name="markdown">
- Respond in Markdown.
- Use clear paragraphs, and add headings or lists only where they genuinely help the reader.
- Do not add any text before your answer.
</OutputFormat>"""

    @staticmethod
    def voice_instructions() -> str:
        return """<OutputFormat name="voice">
- Write narration-ready plain text meant to be read aloud, with no visual formatting.
- Use short, complete sentences and short paragraphs.
- Replace headings with spoken transitions, and replace bullet lists with transitions such as "First,", "Next,", and "Finally.".
- Do not use Markdown, headings, bullet markers, tables, code fences, emojis, or raw URLs.
- Avoid phrases such as "as listed below".
- Write numbers, dates, symbols, abbreviations, and units the way a person would say them where practical.
- Use punctuation and paragraph breaks to create natural pauses.
</OutputFormat>"""

    @classmethod
    def format_instructions(cls, output_format: OutputFormat) -> str:
        if output_format is OutputFormat.VOICE:
            return cls.voice_instructions()
        return cls.markdown_instructions()

    @classmethod
    def summary_request(cls) -> str:
        return (
            f"{cls.content_instructions()}\n\n"
            f"{cls.structured_instructions()}\n\n"
            f"{cls.quality_instructions()}"
        )

    @classmethod
    def custom_request(cls, user_prompt: str, output_format: OutputFormat) -> str:
        return (
            f"<ContentRequest>\n{user_prompt}\n</ContentRequest>\n\n"
            f"{cls.format_instructions(output_format)}"
        )

    @classmethod
    def follow_up(
        cls, summary: str, question: str, output_format: OutputFormat
    ) -> str:
        return (
            f"You previously answered this in response to this video:\n{summary}\n\n"
            f"Now answer this: {question}\n\n"
            f"{cls.format_instructions(output_format)}"
        )
