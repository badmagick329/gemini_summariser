import os

import google.generativeai as genai
from dotenv import load_dotenv

from const import GEMINI_MODEL


def main():
    model = get_model()
    # print("basic example")
    # basic(model)
    print("stop seq example")
    stop_sequence_example(model)
    print("max tokens example")
    max_tokens_example(model)


def get_model():
    load_dotenv()
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel(GEMINI_MODEL)


def basic(model):
    chat = model.start_chat(
        history=[  # type: ignore
            {"role": "user", "parts": "Hello"},
            {
                "role": "model",
                "parts": "Great to meet you. What would you like to know?",
            },
        ]
    )
    response = chat.send_message("I have 2 dogs in my house.")
    print(response.text)
    response = chat.send_message("How many paws are in my house?")
    print(response.text)


def stop_sequence_example(model):
    response = model.generate_content(
        "Tell me a story about a magic backpack.",
        generation_config=genai.types.GenerationConfig(
            # Only one candidate for now.
            candidate_count=1,
            stop_sequences=["x"],
            max_output_tokens=20,
            temperature=1.0,
        ),
    )
    print(response.text)


def max_tokens_example(model):
    response = model.generate_content(
        "Write a story about a magic backpack.",
        generation_config=genai.GenerationConfig(
            max_output_tokens=250,
            temperature=0.1,
        ),
    )
    print(response.text)


if __name__ == "__main__":
    main()
