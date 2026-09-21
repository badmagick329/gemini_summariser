from pathlib import Path


class Config:
    DATA_DIR = Path(__file__).parent.parent / "data"
    CACHE_DIR = DATA_DIR / "cache"
    CACHE_FILES_JSON = DATA_DIR / "cache_files_mappings.json"
    GOOGLE_FILES_JSON = DATA_DIR / "google_files_mappings.json"
    YOUTUBE_DOWNLOAD_FOLDER = DATA_DIR / "videos"
    YOUTUBE_DOWNLOADS_MANIFEST = YOUTUBE_DOWNLOAD_FOLDER / ".downloads.json"
    GEMINI_OUTPUT_DIR = DATA_DIR / "gemini_outputs"
    GEMINI_MODEL = "gemini-3.8-flash"

    @classmethod
    def init(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.YOUTUBE_DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.GEMINI_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
