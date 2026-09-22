# Gemini Video Summariser

A command-line tool that uses Google's Gemini AI to summarise videos. Works with both YouTube videos and local video files.

## Features

- **YouTube Support**: Automatically downloads YouTube videos using `yt-dlp`
- **Local Video Support**: Summarise videos stored on your device
- **Interactive Q&A**: Ask follow-up questions about the video after the initial summary
- **Smart Caching**: Avoids re-uploading videos that have already been processed
- **Markdown Output**: Summaries are saved as markdown files and displayed with rich formatting in the console
- **Voice Output**: Summaries can be rendered as narration-ready plain text for text-to-speech tools

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
uv run ./src/main.py <youtube_url_or_local_video_path> [prompt] [--format markdown|voice]
```

`--format` selects the output style and defaults to `markdown`.

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

**Generate narration-ready text instead of Markdown:**

```sh
uv run ./src/main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --format voice
```

**Create a summary without starting interactive Q&A:**

```sh
uv run ./src/main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --no-chat
```

### PowerShell wrapper

The wrapper at `C:\scripts\gs.ps1` forwards all arguments, so the format option
works through it unchanged:

```powershell
C:\scripts\gs.ps1 VIDEO --format voice
C:\scripts\gs.ps1 VIDEO --format markdown
```


### Cleanup

Downloaded YouTube videos are a local cache. Preview a cleanup before deleting
anything:

```sh
uv run ./src/main.py cleanup
```

By default it targets completed downloads older than 7 days, partial downloads
older than 1 day, and stale mappings for those app-managed downloads. Markdown
summaries are preserved. Add `--apply` to delete the planned files, change the
retention period with `--days`, or include old summaries explicitly:

```sh
uv run ./src/main.py cleanup --apply --days 14
uv run ./src/main.py cleanup --apply --outputs --days 90
```

### Default Prompt

When no custom prompt is provided, the tool generates a comprehensive summary that includes:

- Information on the creator
- Topics Discussed
- Key insights and findings
- Conclusions and takeaways from the video

The built-in response is requested as structured content against a shared schema
and then rendered by the selected renderer. Each run makes a new model request,
so the summary is generated afresh every time.

### Interactive Mode

After the initial summary is generated, you can ask follow-up questions about the video. Type your question and press Enter, or type `q` to quit. Follow-up answers use the selected format but are only shown in the console; they are not saved.

## Limitations

- **Video length**: Maximum 45 minutes (Gemini API limitation)

## Output

Summaries are saved in the `data/gemini_outputs` directory, including for local videos. Filenames contain a safe video identifier, a short hash of the original identifier, and the prompt text.

- **Markdown** (`--format markdown`, the default) is saved as a `.md` file and rendered in the console with [glow](https://github.com/charmbracelet/glow) when available.
- **Voice** (`--format voice`) is saved as a `.txt` file containing narration only. It is printed to the console as plain text and is not sent through glow.

Voice output is plain, spoken-style prose. It uses short sentences and paragraphs,
avoids mechanical list transitions, and varies sentence openings. The shared
structured content is requested with clear, naturally readable numbers, dates,
symbols, and units, and the voice renderer arranges it for reading aloud. It does
not synthesize audio.

## Configuration

You can modify settings in `src/config.py`:

- `GEMINI_MODEL` - The Gemini model to use (default: `gemini-3.8-flash`)
- Output and cache directories

### YouTube downloads

The app detects `yt-dlp` from `PATH` on Windows, Linux, and macOS. On Windows
it prefers `yt-dlp.exe` and never calls a `.bat`/`.cmd` shim, avoiding
PowerShell/CMD escaping problems with output templates such as
`%(title)s.%(ext)s`. If no executable is found, it also supports a `yt_dlp`
module installed in the same Python environment as the app.

Set the following optional values in `.env` when YouTube requires them:

```dotenv
# Optional: explicitly select a native executable when multiple versions exist.
# Windows: C:\path\to\yt-dlp.exe
# Linux/macOS: /usr/local/bin/yt-dlp
YTDLP_EXECUTABLE=
YTDLP_COOKIES_FILE=/path/to/youtube-cookies.txt
YTDLP_JS_RUNTIMES=deno
YTDLP_FORMAT=bv*+ba/b
YTDLP_OUTPUT_TEMPLATE=%(upload_date>%y%m%d)s %(title)s.%(ext)s
```

Downloaded paths are recorded in `data/videos/.downloads.json`, so a custom
output template does not prevent the app from finding a video on later runs.
For unusual future workarounds, use `YTDLP_EXTRA_ARGS` as a JSON array (for
example `YTDLP_EXTRA_ARGS=["--extractor-args", "youtube:player_client=web"]`)
or set `YTDLP_CONFIG_LOCATION` to a yt-dlp configuration file.

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
