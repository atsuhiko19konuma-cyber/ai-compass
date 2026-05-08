import hmac
import os
from pathlib import Path

import streamlit as st
from openai import OpenAIError

from generate_daily_news import generate_daily_news
from utils import get_today_dir, load_json, today_string


st.set_page_config(
    page_title="AI Compass",
    page_icon="AI",
    layout="centered",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    .stApp {
        background: #ffffff;
        color: #172033;
    }
    .main .block-container {
        max-width: 720px;
        padding: 1.2rem 1rem 3rem;
    }
    h1 {
        font-size: 2.1rem !important;
        letter-spacing: 0 !important;
        margin-bottom: 0.2rem !important;
    }
    .subtle {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 1.1rem;
    }
    .hero {
        border: 1px solid #dbeafe;
        border-radius: 14px;
        padding: 1rem;
        background: #f8fbff;
        margin: 1rem 0 1.2rem;
    }
    .card {
        border: 1px solid #e5eaf3;
        border-radius: 14px;
        padding: 1rem;
        margin: 0.85rem 0;
        background: #ffffff;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
    }
    .badge {
        display: inline-block;
        color: #2563eb;
        background: #eff6ff;
        border-radius: 999px;
        padding: 0.18rem 0.55rem;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }
    .story-title {
        font-weight: 800;
        font-size: 1.08rem;
        line-height: 1.45;
        margin-bottom: 0.55rem;
    }
    .label {
        font-weight: 800;
        color: #1d4ed8;
        margin-top: 0.75rem;
        margin-bottom: 0.2rem;
    }
    .small {
        color: #64748b;
        font-size: 0.88rem;
        line-height: 1.55;
    }
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        background: #eff6ff;
        font-weight: 800;
        min-height: 3rem;
    }
    audio {
        width: 100%;
        margin-top: 0.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def require_password_if_configured() -> bool:
    """Keep local use password-free, but allow a simple guard when deployed."""
    expected_password = os.getenv("APP_PASSWORD")
    if not expected_password:
        return True

    if st.session_state.get("password_ok"):
        return True

    st.title("AI Compass")
    entered_password = st.text_input("パスワード", type="password")

    if entered_password:
        if hmac.compare_digest(entered_password, expected_password):
            st.session_state["password_ok"] = True
            st.rerun()
        else:
            st.error("パスワードが違います。")

    return False


def show_empty_state() -> None:
    st.markdown(
        """
        <div class="hero">
            <strong>今日のニュースはまだありません。</strong><br>
            <span class="small">下のボタンで、今日のAI朝刊を作成できます。生成は1日1回だけ保存されます。</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("今日のAI朝刊を作成する"):
        with st.spinner("RSSを読み込み、3本に絞り、音声を作っています..."):
            try:
                generate_daily_news(force=False)
                st.success("今日のAI朝刊を作成しました。ページを更新します。")
                st.rerun()
            except OpenAIError as exc:
                message = str(exc)
                if "insufficient_quota" in message or "exceeded your current quota" in message:
                    st.error("OpenAI APIの利用枠または支払い設定が原因で作成できませんでした。")
                    st.info(
                        "OpenAI PlatformのBilling画面で支払い方法・残高・利用上限を確認してください。"
                    )
                else:
                    st.error(f"OpenAI APIでエラーが発生しました: {exc}")
            except Exception as exc:
                st.error(f"作成に失敗しました: {exc}")
                st.info("APIキー、ネットワーク、RSS取得状況を確認してください。")


def render_story(index: int, story: dict) -> None:
    source = story.get("source", "AI News")
    original_url = story.get("url", "")
    source_line = f"{source}"
    if original_url:
        source_line = f'<a href="{original_url}" target="_blank">{source}</a>'

    st.markdown(
        f"""
        <div class="card">
            <div class="badge">Story {index}</div>
            <div class="story-title">{story.get("japanese_title", "タイトルなし")}</div>
            <div>{story.get("summary", "")}</div>
            <div class="label">仕事でどう役立つ？</div>
            <div>{story.get("work_usefulness", "")}</div>
            <div class="small" style="margin-top: 0.75rem;">出典: {source_line}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    if not require_password_if_configured():
        return

    today = today_string()
    today_dir = get_today_dir()
    news_path = today_dir / "news.json"
    audio_path = today_dir / "podcast.mp3"
    wav_audio_path = today_dir / "podcast.wav"
    script_path = today_dir / "podcast.txt"

    st.title("AI Compass")
    st.markdown(f'<div class="subtle">{today} のAI朝刊</div>', unsafe_allow_html=True)

    if not news_path.exists():
        show_empty_state()
        return

    news = load_json(news_path)
    stories = news.get("stories", [])

    st.markdown(
        """
        <div class="hero">
            <strong>今日の3本を、3分以内で。</strong><br>
            <span class="small">この音声はAIによって生成されています。</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if wav_audio_path.exists():
        st.audio(wav_audio_path.read_bytes(), format="audio/wav")
    elif audio_path.exists():
        st.audio(audio_path.read_bytes(), format="audio/mp3")
    else:
        st.warning("音声ファイルがまだありません。もう一度生成してください。")

    with st.expander("台本を読む"):
        if script_path.exists():
            st.text(Path(script_path).read_text(encoding="utf-8"))
        else:
            st.write("台本ファイルが見つかりません。")

    st.subheader("今日のニュース")
    for index, story in enumerate(stories[:3], start=1):
        render_story(index, story)

    st.markdown(
        '<div class="small">同じ日に再生成したい場合は、ターミナルで '
        '<code>python generate_daily_news.py --force</code> を実行してください。</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
