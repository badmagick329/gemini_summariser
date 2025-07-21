import re


class ParsedVideoFormat:
    _regex = re.compile(r"^(\d+).+(\d{3,4})x(\d{3,4}).+")
    _text: str
    _width: int
    _height: int
    _format_id: int

    def __init__(self, text: str) -> None:
        if not ParsedVideoFormat.is_valid(text):
            raise ValueError(f"Invalid video format: {text}")
        self._text = text
        self.parse()

    @classmethod
    def is_valid(cls, text: str) -> bool:
        return "video only" in text

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def format_id(self) -> int:
        return self._format_id

    def parse(self):
        match = self._regex.match(self._text)
        if match is None:
            raise ValueError(f"Invalid video format: {self._text}")

        self._format_id = int(match.group(1))
        self._width = int(match.group(2))
        self._height = int(match.group(3))
