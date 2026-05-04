import os
import requests
from pathlib import Path
from datetime import datetime


def _load_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key and Path("/root/.env").exists():
        for line in Path("/root/.env").read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                break
    return key


GEMINI_API_KEY = _load_key()
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)


def call_gemini(prompt: str) -> str:
    resp = requests.post(
        GEMINI_URL,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def compress_context():
    files_to_read = [
        "/root/roamaid_second_brain/CLAUDE.md",
        "/root/roamaid_second_brain/docs/ai-context.md",
        "/root/brain/daily/" + datetime.now().strftime("%Y-%m-%d") + ".md",
    ]

    content = ""
    for f in files_to_read:
        if Path(f).exists():
            content += f"\n\n=== {f} ===\n"
            content += Path(f).read_text(encoding="utf-8")[:3000]

    prompt = f"""Сожми этот контекст системы в максимум 500 токенов.
Сохрани только:
- что работает
- что сломано
- следующий шаг
- ключевые файлы и серверы

КОНТЕКСТ:
{content}

Ответь строго в формате markdown, максимум 500 токенов."""

    response = call_gemini(prompt)

    output = f"""### Статус: {datetime.now().strftime('%d.%m.%Y %H:%M')}
{response}

---
*Автосжатие через Gemini*"""

    Path("/root/roamaid_second_brain/docs/ai-context.md").write_text(output, encoding="utf-8")
    print("✅ Контекст сжат")


if __name__ == "__main__":
    compress_context()
