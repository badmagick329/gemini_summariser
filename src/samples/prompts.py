class Mediator:
    @staticmethod
    def prompt1():
        return """<Question>
Carefully watch and understand the video provided and answer the following questions

1. Who seems to be the creator of the video
2. What is the main topic discussed in the video
3. Highlight the key points mentioned in the video and summarise them
4. Is there anything important about the video that should be mentioned?
5. Highlight the information from the video that can be useful to learn or know, if any
</Question>

<OutputFormat>
# Creator

<your answer here>

# Topic Discussed

<your answer here>

# Key points

- point 1
- point 2
- point 3
...

# Important Highlight

<your answer here>

# Takeaways

<your answer here>
```
</OutputFormat>

<OutputInstructions>
- DO NOT output your answer in any other format than the one provided
- Ensure that you do not miss out on key details from the video. If something needs to be elaborated on, then elaborate on it some more
- Ensure your summary provides enough information so that watching the video is not unnecessary.
</OutputInstructions>
"""

    @staticmethod
    def clean1(text: str):
        lines = text.splitlines()
        idx = 0
        for i, line in enumerate(lines):
            if line == "# Creator":
                idx = i
                break

        return "\n".join(lines[idx:])
