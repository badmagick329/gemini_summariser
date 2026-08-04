class FileUploadError(Exception):
    pass


class FileRemovalError(Exception):
    pass


class GeminiGenerationBlockedError(Exception):
    def __init__(self, reason: str, response_id: str | None = None) -> None:
        self.reason = reason
        self.response_id = response_id
        super().__init__(f"Gemini blocked this request: {reason}")


class GeminiGenerationError(Exception):
    pass
