import os
import sys
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

from const import (
    GEMINI_OUTPUT_DIR,
    GOOGLE_FILES_JSON,
    SAMPLE_YOUTUBE_VIDEO,
    YOUTUBE_DOWNLOAD_FOLDER,
)
from google_files import GoogleFilesManager, GoogleFilesMappingsJson
from output_handlers import GeminiOutput
from youtube_video import Video


def main():
    url, prompt = get_args()

    video = Video(url, YOUTUBE_DOWNLOAD_FOLDER)
    print("Downloding video...")
    download_status = video.download()
    print(download_status)
    print(video.downloaded_file())
    downloaded_file = video.downloaded_file()
    assert downloaded_file, "Error downloading file"

    response = video_processing_example(downloaded_file=downloaded_file, prompt=prompt)
    gemini_output = GeminiOutput(GEMINI_OUTPUT_DIR, video.video_id, prompt, response)
    gemini_output.write_output()


def get_args() -> tuple[str, str]:
    prompt = "Summarise this video. Then create a quiz with answer key based on the information in the video."
    url = SAMPLE_YOUTUBE_VIDEO

    for arg in sys.argv[1:]:
        if arg.startswith("https"):
            url = arg
        else:
            prompt = arg

    return url, prompt


def video_processing_example(downloaded_file: Path, prompt: str) -> str:
    model = get_model()
    google_files_data = GoogleFilesMappingsJson(GOOGLE_FILES_JSON)
    google_files_manager = GoogleFilesManager(google_files_data)
    sample_video, uploaded = google_files_manager.get_file(
        downloaded_file, mime_type="video/webm"
    )
    if uploaded:
        print("Waiting on video to be processed")
        while sample_video.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            sample_video = genai.get_file(sample_video.name)

    print("Making LLM inference request...")
    response = model.generate_content(
        [sample_video, prompt], request_options={"timeout": 600}
    )

    print(response.text)
    return response.text


def get_model():
    load_dotenv()
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel(model_name="gemini-1.5-pro")
