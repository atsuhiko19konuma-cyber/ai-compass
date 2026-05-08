import argparse
import json
import os
from datetime import datetime

from dotenv import load_dotenv

from news_sources import fetch_articles, select_top_articles
from podcast_generator import (
    generate_podcast_audio,
    generate_podcast_script,
    generate_story_summaries,
)
from utils import get_today_dir, save_json, today_string


def generate_daily_news(force: bool = False) -> dict:
    """Create today's briefing once and save it in data/YYYY-MM-DD."""
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Please add it to your .env file.")

    today_dir = get_today_dir()
    news_path = today_dir / "news.json"
    script_path = today_dir / "podcast.txt"
    audio_path = today_dir / "podcast.mp3"

    if news_path.exists() and script_path.exists() and audio_path.exists() and not force:
        return {
            "status": "skipped",
            "message": "Today's briefing already exists.",
            "folder": str(today_dir),
        }

    today_dir.mkdir(parents=True, exist_ok=True)

    print("1/5 RSSからAIニュースを取得しています...")
    articles = fetch_articles()
    print(f"取得した記事数: {len(articles)}")

    print("2/5 実用性の高い3本を選んでいます...")
    selected_articles = select_top_articles(articles, limit=3)

    if len(selected_articles) < 3:
        raise RuntimeError("Could not find 3 usable AI news stories from RSS feeds.")

    for index, article in enumerate(selected_articles, start=1):
        print(f"  {index}. {article['source']}: {article['title']}")

    print("3/5 日本語の要約を作っています...")
    stories = generate_story_summaries(selected_articles)

    print("4/5 3分以内の音声原稿を作っています...")
    podcast_script = generate_podcast_script(stories)

    print("5/5 1つの声で短い音声を作っています...")
    generate_podcast_audio(podcast_script, audio_path)

    payload = {
        "date": today_string(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stories": stories,
    }

    save_json(news_path, payload)
    script_path.write_text(podcast_script, encoding="utf-8")

    print("完了しました。")

    return {
        "status": "created",
        "folder": str(today_dir),
        "stories": len(stories),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate today's AI Compass briefing.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate today's files even if they already exist.",
    )
    args = parser.parse_args()

    result = generate_daily_news(force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
