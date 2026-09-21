import json
from dataclasses import dataclass

from exceptions import GeminiGenerationError

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "creator": {"type": "string"},
        "topic": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "important_highlight": {"type": "string"},
        "takeaways": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "creator",
        "topic",
        "key_points",
        "important_highlight",
        "takeaways",
    ],
}

_TEXT_FIELDS = ("creator", "topic", "important_highlight")
_LIST_FIELDS = ("key_points", "takeaways")


@dataclass(frozen=True)
class VideoSummary:
    """Format-neutral summary content shared by every renderer.

    Rendering presentation is deliberately kept out of this type so that
    switching output formats cannot change the underlying facts.
    """

    creator: str
    topic: str
    key_points: tuple[str, ...]
    important_highlight: str
    takeaways: tuple[str, ...]


def parse_summary(raw: str) -> VideoSummary:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as error:
        raise GeminiGenerationError(
            f"the structured summary was not valid JSON: {error}"
        ) from error

    if not isinstance(data, dict):
        raise GeminiGenerationError("the structured summary was not a JSON object")

    missing = [
        field for field in (*_TEXT_FIELDS, *_LIST_FIELDS) if field not in data
    ]
    if missing:
        raise GeminiGenerationError(
            "the structured summary was missing required field(s): "
            + ", ".join(missing)
        )

    return VideoSummary(
        creator=_text(data, "creator"),
        topic=_text(data, "topic"),
        key_points=_text_list(data, "key_points"),
        important_highlight=_text(data, "important_highlight"),
        takeaways=_text_list(data, "takeaways"),
    )


def _text(data: dict, field: str) -> str:
    value = data[field]
    if not isinstance(value, str) or not value.strip():
        raise GeminiGenerationError(
            f"the structured summary field '{field}' must be a non-empty string"
        )
    return value.strip()


def _text_list(data: dict, field: str) -> tuple[str, ...]:
    value = data[field]
    if not isinstance(value, list) or not value:
        raise GeminiGenerationError(
            f"the structured summary field '{field}' must be a non-empty list"
        )
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise GeminiGenerationError(
            f"the structured summary field '{field}' must only contain non-empty strings"
        )
    return tuple(item.strip() for item in value)
