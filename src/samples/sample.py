import os

import google.generativeai as genai
from dotenv import load_dotenv

from const import GEMINI_MODEL

load_dotenv()


def main():
    genai.configure(api_key=os.environ["API_KEY"])
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content("Write a story about a magic backpack.")
    print(response.text)


if __name__ == "__main__":
    main()
