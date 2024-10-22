import os
import sys
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from const import SAMPLE_MD


def main():
    model = get_model()
    sample_md = genai.upload_file(SAMPLE_MD, mime_type="text/markdown")
    print(sample_md)
    response = model.generate_content(
        ["Give me a summary of this markdown file.", sample_md]
    )
    print(response.text)


def get_model():
    load_dotenv()
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel("gemini-1.5-flash")


if __name__ == "__main__":
    main()
