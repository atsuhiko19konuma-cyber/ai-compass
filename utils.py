import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path


DATA_DIR = Path("data")


def today_string() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_today_dir() -> Path:
    return DATA_DIR / today_string()


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_text(value: str) -> str:
    text = unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
