import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from openai import OpenAI


DEFAULT_SUMMARY_MODEL = "gpt-5-nano"
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_TTS_VOICE = "coral"


def get_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Please add it to your .env file.")
    return OpenAI()


def generate_story_summaries(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ask OpenAI to rewrite exactly 3 selected stories for a beginner in Japanese."""
    client = get_client()
    model = os.getenv("OPENAI_SUMMARY_MODEL", DEFAULT_SUMMARY_MODEL)

    compact_articles = [
        {
            "source": article["source"],
            "title": article["title"],
            "summary": article["summary"],
            "url": article["url"],
            "published": article.get("published", ""),
        }
        for article in articles[:3]
    ]

    prompt = f"""
あなたは「AI Compass」という個人用AI朝刊アプリの編集者です。
読者はAI初心者の会社員です。日本語だけで、落ち着いた実用的な説明にしてください。

下の記事候補を、必ず3件すべて使ってください。
各記事について、次のJSON形式だけを返してください。

{{
  "stories": [
    {{
      "japanese_title": "短くキャッチーな日本語タイトル",
      "summary": "初心者にもわかる2〜3文の要約",
      "work_usefulness": "仕事でどう役立つかを1〜2文で説明",
      "source": "元のsource",
      "url": "元のurl"
    }}
  ]
}}

禁止:
- 技術用語を増やす
- 不安をあおる
- 投資や暗号資産の話に寄せる
- 3件以外に増やす

記事候補:
{json.dumps(compact_articles, ensure_ascii=False, indent=2)}
"""

    response = client.responses.create(
        model=model,
        input=prompt,
        reasoning={"effort": "minimal"},
    )

    data = parse_json_response(response.output_text)
    stories = data.get("stories", [])

    if len(stories) != 3:
        raise RuntimeError("OpenAI did not return exactly 3 stories.")

    return stories


def generate_podcast_script(stories: list[dict[str, Any]]) -> str:
    client = get_client()
    model = os.getenv("OPENAI_SUMMARY_MODEL", DEFAULT_SUMMARY_MODEL)

    prompt = f"""
次の3本のAIニュースから、日本語の短い音声ニュース原稿を作ってください。

条件:
- 必ず3分以内で聞ける長さ
- 会話形式にしない
- 1人のナレーターが説明する原稿にする
- 日本語だけ
- 各ニュースについて「何が起きたか」「なぜ仕事に役立つか」を説明
- 最後に、今日試すとよい小さな行動を1つだけ提案
- Markdownや箇条書きは使わない
- 「先生」「生徒」「Teacher」「Student」という役割名は使わない
- 文字数は900〜1200字程度
- 冒頭で「この音声はAIによって生成されています」と自然に伝える

ニュース:
{json.dumps(stories, ensure_ascii=False, indent=2)}
"""

    response = client.responses.create(
        model=model,
        input=prompt,
        reasoning={"effort": "minimal"},
    )
    return response.output_text.strip()


def generate_podcast_audio(script: str, output_path: Path) -> None:
    client = get_client()
    tts_model = os.getenv("OPENAI_TTS_MODEL", DEFAULT_TTS_MODEL)
    voice = os.getenv("OPENAI_TTS_VOICE", DEFAULT_TTS_VOICE)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cleaned_script = strip_role_labels(script)
    with client.audio.speech.with_streaming_response.create(
        model=tts_model,
        voice=voice,
        input=cleaned_script,
        instructions="落ち着いた日本語の朝のニュース番組のように、聞き取りやすく自然に話してください。",
    ) as response:
        response.stream_to_file(output_path)

    create_wav_copy(output_path)


def strip_role_labels(text: str) -> str:
    return re.sub(
        r"(?im)^\s*(?:teacher|student|ai teacher|ai student|先生|生徒)\s*[:：]\s*",
        "",
        text,
    ).strip()


def create_wav_copy(mp3_path: Path) -> None:
    """Create a phone-friendly WAV copy when ffmpeg is available."""
    wav_path = mp3_path.with_suffix(".wav")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(mp3_path),
                "-ar",
                "44100",
                "-ac",
                "1",
                str(wav_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        # MP3 still works on most browsers, so WAV conversion is only a convenience.
        return


def parse_json_response(text: str) -> dict[str, Any]:
    """Handle plain JSON, or JSON accidentally wrapped in Markdown fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    if not cleaned.startswith("{"):
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

    return json.loads(cleaned)
