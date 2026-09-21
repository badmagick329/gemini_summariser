from output_format import OutputFormat
from summary import VideoSummary

_TERMINAL_PUNCTUATION = ".!?"

_LOWERCASE_LEADING_WORDS = frozenset(
    {
        "A",
        "An",
        "The",
        "This",
        "That",
        "These",
        "Those",
        "It",
        "Its",
        "He",
        "She",
        "They",
        "We",
        "You",
        "There",
        "Here",
        "In",
        "On",
        "At",
        "By",
        "For",
        "With",
        "From",
        "To",
        "Of",
        "As",
        "When",
        "While",
        "After",
        "Before",
        "If",
        "Because",
        "Since",
        "But",
        "And",
        "Or",
        "So",
        "Then",
        "Also",
        "However",
        "Therefore",
    }
)



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
        paragraphs.append(_with_transitions(summary.key_points))
    if summary.important_highlight:
        paragraphs.append(_highlight(summary.important_highlight))
    if summary.takeaways:
        paragraphs.append(
            "The main takeaways are these. " + _with_transitions(summary.takeaways)
        )
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _intro(creator: str, topic: str) -> str:
    creator = creator.strip()
    topic = topic.strip()
    if not creator and not topic:
        return ""
    if (
        creator
        and topic
        and not _is_complete_sentence(creator)
        and not _is_complete_sentence(topic)
    ):
        return _as_sentence(f"This video was created by {creator} and discusses {topic}")

    sentences = []
    if creator:
        sentences.append(
            _as_sentence(creator)
            if _is_complete_sentence(creator)
            else _as_sentence(f"This video was created by {creator}")
        )
    if topic:
        sentences.append(
            _as_sentence(topic)
            if _is_complete_sentence(topic)
            else _as_sentence(f"The video discusses {topic}")
        )
    return " ".join(sentences)


def _with_transitions(items: tuple[str, ...]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    sentences = []
    for index, item in enumerate(cleaned):
        if index == 0:
            transition = "First"
        elif index == len(cleaned) - 1:
            transition = "Finally"
        else:
            transition = "Next"
        sentences.append(_as_sentence(f"{transition}, {_lower_first_word(item)}"))
    return " ".join(sentences)


def _highlight(highlight: str) -> str:
    highlight = highlight.strip()
    if _is_complete_sentence(highlight):
        return f"The most important highlight is this. {_as_sentence(highlight)}"
    return f"The most important highlight is that {_as_sentence(highlight)}"


def _is_complete_sentence(text: str) -> bool:
    text = text.strip()
    return len(text) > 1 and text[0].isupper() and text[-1] in _TERMINAL_PUNCTUATION


def _as_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    return text if text[-1] in _TERMINAL_PUNCTUATION else text + "."


def _lower_first_word(text: str) -> str:
    head, separator, tail = text.partition(" ")
    if head in _LOWERCASE_LEADING_WORDS:
        return head[:1].lower() + head[1:] + separator + tail
    return text
