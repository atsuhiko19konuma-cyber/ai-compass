# AI Compass

AI Compass is a personal-use local web app for a calm Japanese AI morning briefing.

Every day it:

1. Reads AI news from RSS feeds
2. Selects exactly 3 practical stories
3. Creates beginner-friendly Japanese summaries
4. Creates one short Japanese audio script
5. Generates one local MP3 file and a phone-friendly WAV copy
6. Shows everything in a simple Streamlit app

This is intentionally small. No login, no database, no cloud deployment, no complicated frontend.

## What You Need

- A computer with Python installed
- An OpenAI API key
- Your smartphone on the same Wi-Fi network if you want to listen from your phone

## Install Python

If Python is not installed:

1. Open [python.org/downloads](https://www.python.org/downloads/)
2. Download the latest Python 3 version
3. Install it
4. Open Terminal and check:

```bash
python3 --version
```

If you see something like `Python 3.12.x`, you are ready.

## Set Up This App

Open Terminal in this project folder, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, the activation command is different:

```bash
.venv\Scripts\activate
```

## Add Your OpenAI API Key

Create your private `.env` file:

```bash
cp .env.example .env
```

Open `.env` and replace this:

```text
OPENAI_API_KEY=sk-your-api-key-here
```

with your real OpenAI API key.

Do not share your `.env` file.

## Generate Today's Briefing

Run:

```bash
python generate_daily_news.py
```

The app saves files like this:

```text
data/
  2026-05-07/
    news.json
    podcast.txt
    podcast.mp3
```

If today's files already exist, the script will skip generation to save money.

To intentionally regenerate today:

```bash
python generate_daily_news.py --force
```

## Run the App

Run:

```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## Open on Your Smartphone

Your computer and phone must be on the same Wi-Fi.

Run Streamlit with network access:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Find your computer's local IP address.

On macOS:

```bash
ipconfig getifaddr en0
```

Then open this on your phone:

```text
http://YOUR-IP-ADDRESS:8501
```

Example:

```text
http://192.168.1.20:8501
```

## Use It When Your PC Is Closed

If your PC is closed, the local app cannot be opened from your phone. The simple cloud option for this Streamlit app is Streamlit Community Cloud, not Vercel.

Recommended path:

1. Put this project in a private GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Click `Create app`
4. Select your GitHub repository
5. Set the app file to `app.py`
6. Add secrets in the advanced settings
7. Deploy

Use this as the Secrets template:

```toml
OPENAI_API_KEY = "sk-your-api-key-here"
OPENAI_SUMMARY_MODEL = "gpt-5-nano"
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"
OPENAI_TTS_VOICE = "coral"
APP_PASSWORD = "your-private-password"
```

`APP_PASSWORD` is strongly recommended in the cloud. Without it, anyone who finds the URL could generate audio using your OpenAI API key.

Vercel is not the best fit for this version because AI Compass is a Streamlit app. Vercel's Python support is for serverless HTTP functions, not a long-running Streamlit UI. Deploying to Vercel would require rewriting the app into a different web architecture.

## Cost-Saving Design

AI Compass is designed to keep API usage low:

- RSS is free
- Only 3 stories are sent to OpenAI
- Only one short audio briefing is generated per day
- Existing daily files are reused
- The default text model is `gpt-5-nano`
- The default speech model is `gpt-4o-mini-tts`

OpenAI's current docs recommend the Responses API for new text generation and document `gpt-4o-mini-tts` for text-to-speech. The pricing page lists `gpt-5-nano` as a very low-cost option for summarization-style tasks.

Useful official docs:

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create?lang=python)
- [OpenAI text generation guide](https://platform.openai.com/docs/guides/text?api-mode=chat&lang=python)
- [OpenAI text-to-speech guide](https://platform.openai.com/docs/guides/text-to-speech)
- [OpenAI pricing](https://platform.openai.com/docs/pricing)

## RSS Sources

The current sources are in `news_sources.py`.

The app tries sources such as:

- OpenAI News
- OpenAI Blog
- Anthropic News
- Google AI Blog
- Google Research Blog
- Google DeepMind Blog
- Hugging Face Blog
- TechCrunch AI
- VentureBeat AI
- The Verge
- Ars Technica AI
- MIT Technology Review AI
- Planet AI

If one feed is temporarily broken, the app skips it and continues.

## Make the News More Interesting

If the selected stories feel boring, edit:

```text
interest_keywords.txt
```

Add one topic per line.

Good examples:

```text
chatgpt
claude
automation
productivity
meeting
spreadsheet
notebooklm
perplexity
cursor
```

The app reads mostly English RSS feeds, so English keywords work best.

The app also tries not to choose all 3 stories from the same source. This keeps the briefing less biased toward one company.

## About X / Twitter

X can have interesting AI news, but it is harder to maintain:

- It often requires login or API access
- It can break when X changes its website
- It can add cost and complexity
- It may include rumors or hype

For now, AI Compass uses RSS first because it is cheaper, calmer, and easier to maintain.

## Troubleshooting

### `OPENAI_API_KEY is not set`

Your `.env` file is missing or the key was not added.

Check that `.env` exists and contains:

```text
OPENAI_API_KEY=sk-...
```

### `Could not find 3 usable AI news stories`

RSS feeds may be temporarily unavailable.

Try again later, or add more RSS feeds in `news_sources.py`.

### The phone cannot open the app

Check:

- Your phone and computer are on the same Wi-Fi
- You used `--server.address 0.0.0.0`
- You used your computer's local IP address
- macOS firewall is not blocking Python or Streamlit

### It generated audio again and cost money

Normal use does not regenerate if today's files already exist.

Only this command forces regeneration:

```bash
python generate_daily_news.py --force
```

## Daily Routine

Each morning:

```bash
source .venv/bin/activate
python generate_daily_news.py
streamlit run app.py --server.address 0.0.0.0
```

Then open the app on your phone and press play.

The audio briefing is now designed to be short and low cost:

- Under 3 minutes
- One narrator voice
- No teacher/student conversation
- `gpt-5-nano` for summaries and scripts

The goal is simple:

> Every morning, calmly understand useful AI news in 5 minutes.
