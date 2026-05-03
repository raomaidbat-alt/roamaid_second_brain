import asyncio
import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

LESSONS_DIR = Path("/root/brain/raw/lessons")
LESSONS_DIR.mkdir(parents=True, exist_ok=True)


def download_and_transcribe(url: str) -> dict:
    """Скачивает аудио и транскрибирует через Whisper на сервере 1"""
    import requests

    # Сначала пробуем через наш API на сервере 1
    try:
        # Скачиваем аудио локально через yt-dlp
        audio_path = f"/tmp/learn_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        result = subprocess.run([
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", audio_path,
            "--no-playlist",
            url
        ], capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            return {"error": f"yt-dlp failed: {result.stderr}"}

        # Получаем метаданные
        meta_result = subprocess.run([
            "yt-dlp", "--dump-json", "--no-playlist", url
        ], capture_output=True, text=True, timeout=60)

        title = "Unknown"
        duration = 0
        if meta_result.returncode == 0:
            meta = json.loads(meta_result.stdout)
            title = meta.get("title", "Unknown")
            duration = meta.get("duration", 0)

        # Транскрибируем через API сервера 1
        server1 = os.getenv("SERVER1_URL", "http://150.241.116.28:8000")
        with open(audio_path, "rb") as f:
            resp = requests.post(
                f"{server1}/transcribe-file",
                files={"file": f},
                timeout=600
            )

        os.remove(audio_path)

        if resp.status_code == 200:
            transcript = resp.json().get("text", "")
            return {
                "title": title,
                "url": url,
                "duration_min": round(duration / 60, 1),
                "transcript": transcript
            }
        else:
            return {"error": f"Transcribe API error: {resp.status_code}"}

    except Exception as e:
        return {"error": str(e)}


def extract_skills_with_gemini(data: dict) -> dict:
    """Gemini анализирует транскрипт и извлекает скиллы"""

    transcript = data.get("transcript", "")
    # Берём первые 30000 символов если длинный
    if len(transcript) > 30000:
        transcript = transcript[:30000] + "\n\n[транскрипт обрезан...]"

    prompt = f"""Ты эксперт по AI-агентам, автоматизации и контент-маркетингу.

Проанализируй транскрипт видео "{data.get('title')}" и извлеки всё полезное.

ТРАНСКРИПТ:
{transcript}

Ответь строго в JSON формате:
{{
  "summary": "краткое резюме видео в 3-4 предложениях",
  "key_insights": [
    "инсайт 1",
    "инсайт 2",
    "инсайт 3",
    "инсайт 4",
    "инсайт 5"
  ],
  "applicable_skills": [
    {{
      "name": "название скилла",
      "description": "что делает",
      "priority": "HIGH/MEDIUM/LOW",
      "how_to_implement": "как внедрить в нашу систему (Telegram бот + Gemini + Google Sheets + instagrapi)"
    }}
  ],
  "memory_facts": [
    "факт для сохранения в brain/memory"
  ],
  "action_items": [
    "конкретное действие которое стоит сделать"
  ],
  "rating": "насколько полезно видео 1-10"
}}

Отвечай ТОЛЬКО JSON без markdown."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception as e:
        return {"error": f"Gemini error: {str(e)}"}


def save_lesson(data: dict, analysis: dict) -> str:
    """Сохраняет урок в brain/raw/lessons/"""
    title_clean = re.sub(r'[^\w\s-]', '', data.get('title', 'lesson'))
    title_clean = re.sub(r'\s+', '_', title_clean)[:50]
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"{date_str}_{title_clean}.md"
    filepath = LESSONS_DIR / filename

    skills_text = ""
    for s in analysis.get("applicable_skills", []):
        skills_text += f"""
### {s['name']} [{s['priority']}]
{s['description']}
**Внедрение:** {s['how_to_implement']}
"""

    insights_text = "\n".join([f"- {i}" for i in analysis.get("key_insights", [])])
    actions_text = "\n".join([f"- [ ] {a}" for a in analysis.get("action_items", [])])
    facts_text = "\n".join([f"- {f}" for f in analysis.get("memory_facts", [])])

    content = f"""# {data.get('title')}

**URL:** {data.get('url')}
**Длительность:** {data.get('duration_min')} мин
**Дата:** {datetime.now().strftime('%d.%m.%Y')}
**Рейтинг:** {analysis.get('rating')}/10

## Резюме
{analysis.get('summary')}

## Ключевые инсайты
{insights_text}

## Скиллы для внедрения
{skills_text}

## Действия
{actions_text}

## Факты для памяти
{facts_text}
"""

    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def format_telegram_response(data: dict, analysis: dict, filepath: str) -> str:
    """Форматирует ответ для Telegram"""
    priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

    skills_text = ""
    for s in analysis.get("applicable_skills", [])[:5]:
        emoji = priority_emoji.get(s.get("priority", "LOW"), "⚪")
        skills_text += f"{emoji} *{s['name']}* — {s['description']}\n"

    insights_text = "\n".join([
        f"{i+1}. {ins}"
        for i, ins in enumerate(analysis.get("key_insights", [])[:5])
    ])

    actions_text = "\n".join([
        f"• {a}"
        for a in analysis.get("action_items", [])[:3]
    ])

    return f"""🎓 *УРОК СОХРАНЁН*
📹 {data.get('title')}
⏱ {data.get('duration_min')} мин | ⭐ {analysis.get('rating')}/10

📝 *Резюме:*
{analysis.get('summary')}

💡 *Топ инсайты:*
{insights_text}

🛠 *Скиллы для внедрения:*
{skills_text}
⚡ *Действия:*
{actions_text}

💾 Сохранено: `{filepath}`

_Напиши "добавь скилл [название]" чтобы я создал файл скилла_"""


async def learn_from_video(url: str) -> str:
    """Главная функция — полный пайплайн обучения"""
    # 1. Скачать и транскрибировать
    data = download_and_transcribe(url)
    if "error" in data:
        return f"❌ Ошибка загрузки: {data['error']}"

    # 2. Анализ через Gemini
    analysis = extract_skills_with_gemini(data)
    if "error" in analysis:
        return f"❌ Ошибка анализа: {analysis['error']}"

    # 3. Сохранить урок
    filepath = save_lesson(data, analysis)

    # 4. Вернуть форматированный ответ
    return format_telegram_response(data, analysis, filepath)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python skill.py <youtube_url>")
        sys.exit(1)
    result = asyncio.run(learn_from_video(sys.argv[1]))
    print(result)
