from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SAMPLE_MD = DATA_DIR / "sample_md.md"
CACHE_DIR = DATA_DIR / "cache"
CACHE_FILES_JSON = DATA_DIR / "cache_files_mappings.json"
GOOGLE_FILES_JSON = DATA_DIR / "google_files_mappings.json"
YOUTUBE_DOWNLOAD_FOLDER = DATA_DIR / "videos"
SAMPLE_YOUTUBE_VIDEO = "https://www.youtube.com/watch?v=DVRg0daTads"
GEMINI_OUTPUT_DIR = DATA_DIR / "gemini_outputs"
GEMINI_MODEL = "gemini-1.5-flash"
