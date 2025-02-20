import subprocess


class MarkdownPrinter:
    _text: str

    def __init__(self, text) -> None:
        self._text = text

    def print_with_glow(self) -> None:
        subprocess.run(
            ["glow"],
            input=self._text,
            text=True,
            capture_output=False,
            check=True,
            encoding="utf-8",
        )
