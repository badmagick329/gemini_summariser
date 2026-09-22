import hashlib
from pathlib import Path

from gemini_output import BaseOutput
from output_format import OutputFormat


class GeminiOutput(BaseOutput):
    _output_dir: Path
    _output_file: Path | None
    _file_id: str
    _prompt: str
    _response: str
    _output_format: OutputFormat

    def __init__(
        self,
        output_dir: Path,
        file_id: str,
        prompt: str,
        response: str,
        output_format: OutputFormat,
    ) -> None:
        if output_dir.is_file():
            raise ValueError(f"{output_dir} is a file, not a directory")
        output_dir.mkdir(parents=True, exist_ok=True)
        self._output_file = None
        self._output_dir = output_dir
        self._file_id = file_id
        self._prompt = prompt
        self._response = response
        self._output_format = output_format

    def write(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(self.file_output)

    @property
    def file_id(self) -> str:
        return self._file_id

    @property
    def prompt(self) -> str:
        return self._prompt

    @property
    def response(self):
        return self._response

    @property
    def output_file(self):
        if self._output_file:
            return self._output_file

        safe_id = "".join(
            char if char.isascii() and (char.isalnum() or char in "-_") else "_"
            for char in self.file_id
        )[:48]
        id_hash = hashlib.sha256(self.file_id.encode("utf-8")).hexdigest()[:12]
        filename = (
            self._output_dir
            / f"{safe_id}_{id_hash}_{self._alphanum_prompt_chars(self.prompt)}"
            f"{self._output_format.suffix}"
        )
        self._output_file = self._get_available_name(filename)
        return self._output_file

    @property
    def file_output(self) -> str:
        if self._output_format.is_voice:
            return self.response
        return f"# Prompt\n\n{self.prompt}\n\n# Response\n\n{self.response}"

    @staticmethod
    def _get_available_name(path: Path) -> Path:
        if not path.exists():
            return path

        int = 0
        while True:
            new_path = path.with_name(f"{path.stem}_{int}{path.suffix}")
            if not new_path.exists():
                return new_path
            int += 1

    @staticmethod
    def _alphanum_prompt_chars(prompt: str, max_chars: int = 100) -> str:
        return "".join(
            [char.replace(" ", "_") for char in prompt if char.isalnum() or char == " "]
        )[:max_chars]
