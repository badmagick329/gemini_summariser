import re


class ParsedAudioFormat:
    _regex = re.compile(r"^((\d{3}-\d)|\d{3}).+(\d{3,4})k https.+\d+k \d+k (.+)$")
    _text: str
    _size: int
    _format_id: str
    _description: str

    def __init__(self, text: str) -> None:
        if not ParsedAudioFormat.is_valid(text):
            raise ValueError(f"Invalid audio format: {text}")
        self._text = text
        self.parse()

    @classmethod
    def is_valid(cls, text: str) -> bool:
        return "audio only" in text and cls._regex.match(text) is not None

    @property
    def size(self) -> int:
        return self._size

    @property
    def format_id(self) -> str:
        return self._format_id

    def parse(self):
        match = self._regex.match(self._text)
        if match is None:
            raise ValueError(f"Invalid audio format: {self._text}")

        self._format_id = match.group(1)
        self._size = int(match.group(3))
        self._description = match.group(4)

    @classmethod
    def remove_alternative_languages(
        cls, parsed_audio_formats: list["ParsedAudioFormat"]
    ) -> list["ParsedAudioFormat"]:
        originals = [
            p
            for p in parsed_audio_formats
            if "original (default)" in p._description.lower()
        ]

        return originals if originals else parsed_audio_formats
