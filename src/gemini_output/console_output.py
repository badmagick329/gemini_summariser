import subprocess

from gemini_output import BaseOutput


class ConsoleOutput(BaseOutput):
    _text: str

    def __init__(self, text) -> None:
        self._text = text

    def write(self) -> None:
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
