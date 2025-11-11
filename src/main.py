import os
import sys
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


from config import Config
from gemini_output import ConsoleOutput, GeminiOutput
from google_files import GoogleFilesManager, GoogleFilesMappingsJson
from prompts import Prompts
from video import VideoFactory


def main():
    url, prompt = get_args()
    video_factory = VideoFactory(Config.YOUTUBE_DOWNLOAD_FOLDER)
    video = video_factory.create_video(url)

    response = summarise_video(video_path=video.path, prompt=prompt)
    gemini_output = GeminiOutput(
        Config.GEMINI_OUTPUT_DIR, video.video_id, prompt, response
    )
    gemini_output.write()


def get_args() -> tuple[str, str]:
    if len(sys.argv) < 2:
        print(
            "Usage: python video_example.py <youtube_url_or_local_video_path> [prompt]"
        )
        sys.exit(1)
    prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else Prompts.prompt1()
    url = sys.argv[1]

    return url, prompt


def summarise_video(video_path: Path, prompt: str) -> str:
    model = get_model()
    google_files_data = GoogleFilesMappingsJson(Config.GOOGLE_FILES_JSON)
    google_files_manager = GoogleFilesManager(google_files_data)
    sample_video, uploaded = google_files_manager.get_file(
        video_path, mime_type="video/webm"
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

    summary = Prompts.clean1(response.text)
    ConsoleOutput(summary).write()

    while True:
        question = input("Ask a question about the video or type q to quit\n")
        new_prompt = f"You previously answered this in response to this video:\n{summary}\n\nNow answer this: {question}"
        if question == "q":
            break
        response = model.generate_content(
            [sample_video, new_prompt], request_options={"timeout": 600}
        )
        ConsoleOutput(response.text).write()

    return response.text


def get_model():
    load_dotenv()
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel(Config.GEMINI_MODEL)


if __name__ == "__main__":
    main()
