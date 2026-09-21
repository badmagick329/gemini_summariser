import subprocess

from gemini_output import BaseOutput
from output_format import OutputFormat


class ConsoleOutput(BaseOutput):
    """Render Markdown through Glow but print voice narration verbatim."""

    _text: str
    _output_format: OutputFormat

    def __init__(self, text: str, output_format: OutputFormat) -> None:
        self._text = text
        self._output_format = output_format

    def write(self) -> None:
        if self._output_format.is_voice:
            print(self._text)
            return

        try:
            subprocess.run(
                ["glow"],
                input=self._text,
                text=True,
                capture_output=False,
                check=True,
                encoding="utf-8",
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(self._text)
            return
