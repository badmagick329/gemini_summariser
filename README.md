# Gemini Video Summariser

A command-line tool that uses Google's Gemini AI to summarise videos. Works with both YouTube videos and local video files.

## Features

- **YouTube Support**: Automatically downloads YouTube videos using `yt-dlp`
- **Local Video Support**: Summarise videos stored on your device
- **Interactive Q&A**: Ask follow-up questions about the video after the initial summary
- **Smart Caching**: Avoids re-uploading videos that have already been processed
- **Markdown Output**: Summaries are saved as markdown files and displayed with rich formatting in the console

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - Python package manager
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Required for YouTube video downloads
- [glow](https://github.com/charmbracelet/glow) - Recommended for prettier console output
- Google Gemini API key

## Installation

1. **Install uv** (if not already installed):

   **Windows (PowerShell):**

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   **Linux/macOS:**

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:

   ```sh
   git clone https://github.com/badmagick329/gemini_summariser
   cd geminisummariser
   ```

3. **Install dependencies**:

   ```sh
   uv sync
   ```

4. **Set up your API key**:

   Create a `.env` file in the project root:

   ```
   API_KEY=your_gemini_api_key_here
   ```

   You can get a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

5. **Install yt-dlp** (for YouTube support):

   See the [yt-dlp installation guide](https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#installation).

6. **Install glow** (optional, for prettier console output):

   See the [glow installation guide](https://github.com/charmbracelet/glow?tab=readme-ov-file#installation).

## Usage

```
uv run ./src/main.py <youtube_url_or_local_video_path> [prompt]
```

### Examples

**Summarise a YouTube video with the default prompt:**

```sh
uv run ./src/main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Summarise a local video:**

```sh
uv run ./src/main.py "/path/to/my_video.mp4"
```

**Use a custom prompt:**

```sh
uv run ./src/main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "Give me a brief 3-bullet summary"
```

### Default Prompt

When no custom prompt is provided, the tool generates a comprehensive summary in markdown format that includes:

- Information on the creator
- Topics Discussed
- Key insights and findings
- Conclusions and takeaways from the video

### Interactive Mode

After the initial summary is generated, you can ask follow-up questions about the video. Type your question and press Enter, or type `q` to quit.

## Limitations

- **Video length**: Maximum 45 minutes (Gemini API limitation)

## Output

Summaries are saved as markdown files in the `data/gemini_outputs` directory. The filename includes the video ID and a hash of the prompt used.

## Configuration

You can modify settings in `src/config.py`:

- `GEMINI_MODEL` - The Gemini model to use (default: `gemini-2.5-flash`)
- Output and cache directories

## Summary Example

```md
# Creator

The creator of the video is Rick Astley, as he is the primary performer and
vocalist in the music video for his song "Never Gonna Give You Up."

# Topic Discussed

The main topic discussed in the video, through the lyrics of the song "Never
Gonna Give You Up," is unwavering love, commitment, and loyalty in a romantic
relationship. The singer expresses his deep feelings and makes strong assurances
that he will always be there for his beloved, promising never to betray,
abandon, or hurt them.

# Key points

- **Declaration of Mutual Understanding:** The song begins by stating, "We're no
  strangers to love, You know the rules and so do I." This suggests an established
  connection and a shared understanding of what love entails between the two
  individuals.
- **Desire for Commitment:** The singer expresses a clear intention for a
  serious and lasting relationship with the line, "A full commitment's what I'm
  thinking of." He emphasizes that he wants the other person to fully comprehend
  his feelings.
- **Uniqueness of His Love:** He asserts the special nature of his commitment by
  saying, "You wouldn't get this from any other guy," implying that his dedication
  is singular and unparalleled.
- **Core Promises of Loyalty and Support (The Chorus):** The most prominent key
  points are the repeated pledges of steadfastness:
  - "Never gonna give you up" (will not abandon)
  - "Never gonna let you down" (will always be reliable)
  - "Never gonna run around and desert you" (will remain faithful)
  - "Never gonna make you cry" (will protect from sadness)
  - "Never gonna say goodbye" (will stay forever)
  - "Never gonna tell a lie and hurt you" (will be honest and caring)
- **Acknowledgment of Unexpressed Feelings:** The song alludes to an unspoken
  understanding between them, "We've known each other for so long, Your heart's
  been aching but you're too shy to say it, Inside we both know what's been going
  on." This suggests a deep, intuitive connection even if feelings haven't been
  fully vocalized by the other person.
- **Openness and Transparency:** The singer encourages the other person to
  recognize his genuine intentions: "And if you ask me how I'm feeling, Don't tell
  me you're too blind to see." He wants his feelings to be clear and reciprocated.

# Important Highlight

The most important aspect of this video, beyond its original purpose as a music
video, is its iconic status as an internet meme known as "Rickrolling." This
phenomenon involves tricking someone into clicking a hyperlink that unexpectedly
leads to the music video for "Never Gonna Give You Up." The video's catchy tune,
Rick Astley's distinctive dance moves, vibrant red hair, and the somewhat
earnest delivery of the lyrics have all contributed to its massive cultural
impact as a form of bait-and-switch humor. The various scene changes, from a
formal church setting to an urban underpass and a chain-link fence, also add to
its unique and memorable visual style, which is often parodied or referenced in
internet culture.

# Takeaways

- **The Power of Unconditional Commitment:** The song provides a clear lyrical
  example of expressing steadfast love and loyalty, which are universally valued
  themes in relationships. It showcases how simple, direct promises can convey a
  powerful message of dedication.
- **Understanding Internet Meme Culture:** For those unfamiliar, this video
  serves as a prime example of a "Rickroll," which is a foundational internet
  meme. Learning about Rickrolling helps in understanding how viral content can
  originate, evolve, and become deeply embedded in online communication and
  culture, often re-contextualizing original media for humorous purposes.
- **1980s Pop Music Aesthetics:** The video itself is a great snapshot of late
  1980s music video production. From the fashion choices (blazers, striped shirts,
  trench coats, sunglasses) to the energetic, somewhat stylized dance routines and
  varying sets, it offers insight into the visual trends of that era in pop music.
- **The Enduring Appeal of a Catchy Tune:** Despite being released in 1987, the
  song's melody and chorus remain highly recognizable and enjoyable, demonstrating
  the lasting impact of well-crafted pop music.
```
