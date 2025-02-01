import os

import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import File

from const import GEMINI_MODEL, GOOGLE_FILES_JSON, SAMPLE_MD
from google_files import GoogleFilesManager, GoogleFilesMappingsJson


def main():
    # cache_testing()
    # basic()
    manager_demo()


def manager_demo():
    _ = get_model()
    google_files_data = GoogleFilesMappingsJson(GOOGLE_FILES_JSON)
    google_files_manager = GoogleFilesManager(google_files_data)
    sample_md, uploaded = google_files_manager.get_file(
        SAMPLE_MD, mime_type="text/markdown"
    )
    print(f"Uploaded: {uploaded}")
    print(f"Got file: {sample_md}")
    sample_md, uploaded = google_files_manager.get_file(
        SAMPLE_MD, mime_type="text/markdown"
    )
    print(f"Uploaded: {uploaded}")
    print(f"Got file: {sample_md}")


def basic():
    model = get_model()
    sample_md = genai.upload_file(SAMPLE_MD, mime_type="text/markdown")
    print(sample_md)
    print("Uploaded files:")
    for f in genai.list_files():
        print(f.name)
    print("---------------")
    response = model.generate_content(
        ["Give me a summary of this markdown file.", sample_md]
    )
    print(response.text)


def cache_testing():
    cache = {}
    model = get_model()
    sample_md = get_google_file(cache, SAMPLE_MD)
    print(sample_md)
    print("generating response...")
    response = model.generate_content(
        ["Give me a summary of this markdown file.", sample_md]
    )
    print("---------------")
    print(response.text)
    print("Second run...")
    sample_md2 = get_google_file(cache, SAMPLE_MD)
    print("generating response...")
    response = model.generate_content(
        ["What's the purpose of this markdown file?", sample_md2]
    )
    print(response.text)
    print("---------------")
    remove_all_uploads()


def get_google_file(cache, key) -> File:
    cached = fetch_from_cache(cache, key)
    if not cached:
        print("Fetching from Google")
        file = genai.upload_file(key, mime_type="text/markdown")
        cache_set(cache, key, file.name)
        return file
    return cached


def cache_set(cache, key, value) -> None:
    print(f"Setting {key}:{value} in cache")
    cache[key] = value


def fetch_from_cache(cache, key) -> File | None:
    print(f"Searching for {key} in cache")
    result = cache.get(key)
    if not result:
        print("Not found in cache")
        return None

    print(f"Found value: {result}")
    file = genai.get_file(name=result)
    print(f"Found file\n{file}")
    return file


def remove_all_uploads():
    get_model()
    print("My files:")
    for f in genai.list_files():
        print("removing", f.name)
        f.delete()


def get_model():
    load_dotenv()
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel(GEMINI_MODEL)


if __name__ == "__main__":
    main()
    # remove_all_uploads()
