from output_format import OutputFormat
from summary import VideoSummary

_TERMINAL_PUNCTUATION = ".!?"

def render_summary(summary: VideoSummary, output_format: OutputFormat) -> str:
    if output_format is OutputFormat.VOICE:
        return _render_voice(summary)
    return _render_markdown(summary)


def _render_markdown(summary: VideoSummary) -> str:
    return "\n\n".join(
        [
            "# Creator",
            summary.creator,
            "# Topic Discussed",
            summary.topic,
            "# Key points",
            _markdown_list(summary.key_points),
            "# Important Highlight",
            summary.important_highlight,
            "# Takeaways",
            _markdown_list(summary.takeaways),
        ]
    )


def _markdown_list(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _render_voice(summary: VideoSummary) -> str:
    paragraphs = [_intro(summary.creator, summary.topic)]
    if summary.key_points:
        paragraphs.append(_spoken_paragraph(summary.key_points))
    closing_sentences = []
    if summary.important_highlight:
        closing_sentences.append(summary.important_highlight)
    if summary.takeaways:
        closing_sentences.extend(summary.takeaways)
    if closing_sentences:
        paragraphs.append(_spoken_paragraph(tuple(closing_sentences)))
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _intro(creator: str, topic: str) -> str:
    creator = creator.strip()
    topic = topic.strip()
    if not creator and not topic:
        return ""
    sentences = []
    if creator:
        sentences.append(_as_sentence(f"This video was created by {creator}"))
    if topic:
        sentences.append(_as_sentence(f"It focuses on {topic}"))
    return " ".join(sentences)


def _spoken_paragraph(items: tuple[str, ...]) -> str:
    return " ".join(_as_sentence(item) for item in items if item.strip())


def _as_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    return text if text[-1] in _TERMINAL_PUNCTUATION else text + "."
