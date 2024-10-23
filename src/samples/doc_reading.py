import os

import google.generativeai as genai
from dotenv import load_dotenv

from const import SAMPLE_MD


def main():
    model = get_model()
    sample_md = genai.upload_file(SAMPLE_MD, mime_type="text/markdown")
    print(sample_md)
    response = model.generate_content(
        ["Give me a summary of this markdown file.", sample_md]
    )
    print(response.text)


def list_files():
    get_model()
    print("My files:")
    for f in genai.list_files():
        print("removing", f.name)
        f.delete()


def get_model():
    load_dotenv()
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel("gemini-1.5-flash")


if __name__ == "__main__":
    # main()
    list_files()
