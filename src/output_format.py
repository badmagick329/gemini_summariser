from enum import Enum


class OutputFormat(Enum):
    """How a generated summary should be presented, not what it contains."""

    MARKDOWN = "markdown"
    VOICE = "voice"

    @property
    def suffix(self) -> str:
        return ".txt" if self is OutputFormat.VOICE else ".md"

    @property
    def is_voice(self) -> bool:
        return self is OutputFormat.VOICE
