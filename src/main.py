import argparse
import mimetypes
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
from cleanup import CleanupManager
from exceptions import GeminiGenerationBlockedError, GeminiGenerationError
from gemini_output import ConsoleOutput, GeminiOutput
from google_files import GoogleFilesManager, GoogleFilesMappingsJson
from prompts import Prompts
from video import VideoFactory


def main():
    load_dotenv(BASE_DIR.parent / ".env.local")
    load_dotenv()
    Config.init()
    args = get_args()
    if args.command == "cleanup":
        return cleanup(args)

    url, prompt, interactive = args.video, args.prompt, not args.no_chat
    video_factory = VideoFactory(Config.YOUTUBE_DOWNLOAD_FOLDER)
    video = video_factory.create_video(url)

    try:
        response = summarise_video(
            video_path=video.path, prompt=prompt, interactive=interactive
        )
    except GeminiGenerationBlockedError as error:
        print(f"Gemini blocked this video request: {error.reason}.")
        if error.response_id:
            print(f"Gemini response ID: {error.response_id}")
        print("No summary was generated. The downloaded video and upload cache were kept.")
        return 3
    except GeminiGenerationError as error:
        print(f"Gemini returned no usable summary: {error}")
        return 4

    gemini_output = GeminiOutput(
        Config.GEMINI_OUTPUT_DIR, video.video_id, prompt, response
    )
    gemini_output.write()
    return 0


def get_args() -> argparse.Namespace:
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        parser = argparse.ArgumentParser(
            description="Remove expired Gemini Summariser cache files."
        )
        parser.add_argument("cleanup", help=argparse.SUPPRESS)
        parser.add_argument("--apply", action="store_true", help="Delete planned files.")
        parser.add_argument(
            "--days", type=positive_int, default=7, help="Age of completed videos (default: 7)."
        )
        parser.add_argument(
            "--part-days", type=positive_int, default=1, help="Age of partial downloads (default: 1)."
        )
        parser.add_argument(
            "--outputs", action="store_true", help="Also remove old Markdown summaries."
        )
        args = parser.parse_args()
        args.command = "cleanup"
        return args

    parser = argparse.ArgumentParser(
        description="Summarise a YouTube or local video with Google Gemini."
    )
    parser.add_argument("video", help="A YouTube URL or path to a local video file")
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Optional custom prompt. Uses the built-in summary prompt when omitted.",
    )
    parser.add_argument(
        "--no-chat",
        action="store_true",
        help="Generate and save the summary without starting follow-up Q&A.",
    )
    args = parser.parse_args()
    args.command = "summarise"
    args.prompt = " ".join(args.prompt) if args.prompt else Prompts.prompt1()
    return args


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def cleanup(args: argparse.Namespace) -> int:
    manager = CleanupManager(
        Config.YOUTUBE_DOWNLOAD_FOLDER,
        Config.GEMINI_OUTPUT_DIR,
        Config.YOUTUBE_DOWNLOADS_MANIFEST,
        Config.GOOGLE_FILES_JSON,
    )
    plan = manager.plan(args.days, args.part_days, args.outputs)
    action = "Deleted" if args.apply else "Would delete"
    print(f"{action} {len(plan.files)} file(s), reclaiming {format_bytes(plan.bytes_to_reclaim)}.")
    print(f"{action} {len(plan.stale_download_ids)} stale download mapping(s).")
    print(f"{action} {len(plan.stale_google_mapping_keys)} stale Gemini mapping(s).")
    if args.apply:
        manager.apply(plan)
    elif plan.files or plan.stale_download_ids or plan.stale_google_mapping_keys:
        print("Preview only. Run again with --apply to perform this cleanup.")
    return 0


def format_bytes(size: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def summarise_video(video_path: Path, prompt: str, interactive: bool = True) -> str:
    model = get_model()
    google_files_data = GoogleFilesMappingsJson(Config.GOOGLE_FILES_JSON)
    google_files_manager = GoogleFilesManager(google_files_data)
    mime_type = mimetypes.guess_type(video_path)[0] or "video/mp4"
    sample_video, uploaded = google_files_manager.get_file(
        video_path, mime_type=mime_type
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

    summary = Prompts.clean1(get_response_text(response))
    ConsoleOutput(summary).write()

    while interactive:
        question = input("Ask a question about the video or type q to quit\n")
        if question == "q":
            break
        new_prompt = f"You previously answered this in response to this video:\n{summary}\n\nNow answer this: {question}"
        response = model.generate_content(
            [sample_video, new_prompt], request_options={"timeout": 600}
        )
        try:
            ConsoleOutput(get_response_text(response)).write()
        except GeminiGenerationBlockedError as error:
            print(f"Gemini blocked that question: {error.reason}.")

    return summary


def get_response_text(response) -> str:
    prompt_feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(prompt_feedback, "block_reason", None)
    if block_reason:
        reason = getattr(block_reason, "name", str(block_reason))
        raise GeminiGenerationBlockedError(
            reason=reason, response_id=getattr(response, "response_id", None)
        )

    if not getattr(response, "candidates", None):
        raise GeminiGenerationError("the API returned no candidates and no block reason")

    try:
        return response.text
    except ValueError as error:
        raise GeminiGenerationError(str(error)) from error


def get_model():
    load_dotenv()
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel(Config.GEMINI_MODEL)


if __name__ == "__main__":
    sys.exit(main())
