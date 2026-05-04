"""Self-learning Threads generator for Roamaid Second Brain.

Reads winning thread lessons from /root/brain/memory/thread_wins.md and injects
those rules into every Gemini prompt. The bot can record chosen winners and add
new reusable rules after each iteration.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

THREAD_WINS_FILE = Path("/root/brain/memory/thread_wins.md")
MY_THREADS_PATTERNS_FILE = Path("/root/brain/memory/my_threads_patterns.md")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={GEMINI_API_KEY}"
)
HOOK_TYPES = ("ПАРАДОКС", "ЦИФРЫ", "БОЛЬ")
_last_gemini_call = 0.0


DEFAULT_MEMORY = """# Thread Wins — самообучающаяся память генератора тредов

Этот файл читается при каждой генерации треда. Записывай сюда победившие варианты
и правила, чтобы Gemini становился точнее с каждым разом.

## Формат записи

```markdown
### [YYYY-MM-DD] — [тип крючка: ПАРАДОКС/ЦИФРЫ/БОЛЬ]
- **Источник**: URL или @аккаунт
- **Крючок**: первое предложение треда
- **Почему зашло**: конкретная причина (цифры, формулировка, боль)
- **Правило**: обобщённое правило для будущих промптов
- **Изменение промпта**: что теперь добавлять/усиливать
```

---

## Правила (добавляются автоматически через improve_prompt_from_lesson)

<!-- RULES_START -->
<!-- RULES_END -->

---

## Записи побед

<!-- WINS_START -->
<!-- WINS_END -->
"""


def ensure_memory_file() -> None:
    THREAD_WINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not THREAD_WINS_FILE.exists():
        THREAD_WINS_FILE.write_text(DEFAULT_MEMORY, encoding="utf-8")



def load_my_threads_patterns(max_chars: int = 8000) -> str:
    """Return performance-based Threads patterns from Roman's own account."""
    if not MY_THREADS_PATTERNS_FILE.exists():
        return ""
    text = MY_THREADS_PATTERNS_FILE.read_text(encoding="utf-8")
    return text[-max_chars:] if len(text) > max_chars else text

def load_thread_wins(max_chars: int = 8000) -> str:
    """Return compact thread-win memory for prompt injection."""
    ensure_memory_file()
    text = THREAD_WINS_FILE.read_text(encoding="utf-8")
    return text[-max_chars:] if len(text) > max_chars else text


def _extract(data: dict[str, Any], *paths: tuple[str, ...], default: str = "") -> str:
    for path in paths:
        cur: Any = data
        for key in path:
            if isinstance(cur, dict):
                cur = cur.get(key)
            else:
                cur = None
            if cur is None:
                break
        if cur not in (None, ""):
            return str(cur)
    return default


def build_thread_prompt(data: dict[str, Any]) -> str:
    """Build adaptive prompt using source data and accumulated winning rules."""
    transcript = _extract(data, ("content", "transcript"), ("transcript",))
    caption = _extract(data, ("content", "caption"))
    author = _extract(data, ("meta", "author"), ("meta", "uploader"), default="блогера")
    views = _extract(data, ("meta", "view_count"), ("meta", "views"), default="неизвестно")
    likes = _extract(data, ("meta", "like_count"), ("meta", "likes"), default="неизвестно")
    followers = _extract(data, ("meta", "followers"), ("profile", "followers"), default="неизвестно")
    wins = load_thread_wins()
    my_patterns = load_my_threads_patterns()

    return f"""Ты главный автор вирусных тредов для Threads/Instagram в системе Roamaid Second Brain.
Твоя задача — сделать 3 варианта треда, которые хочется дочитать, сохранить и отправить другу.

ДАННЫЕ ИСТОЧНИКА:
Автор: {author}
Подписчики: {followers}
Просмотры: {views}
Лайки: {likes}
Описание: {caption[:1200] if caption else "(нет)"}
Транскрипция: {transcript[:5000] if transcript else "(недоступна)"}

ПАМЯТЬ ПОБЕД И ПРАВИЛА, КОТОРЫЕ УЖЕ СРАБОТАЛИ:
{wins}

ПАТТЕРНЫ МОЕГО THREADS АККАУНТА ПО МЕТРИКАМ:
{my_patterns}

Сгенерируй 3 варианта треда с разными крючками:

ПАРАДОКС — столкни сильный внешний актив с внутренней дырой в монетизации.
Формат: "{author}, у которого есть X, но нет Y".

ЦИФРЫ — начни с денежного/вороночного разрыва.
Формат: "При X подписчиках/просмотрах он зарабатывает только Y — хотя мог бы Z".

БОЛЬ — назови конкретную потерю, которую человек уже чувствует.
Формат: "{author}, X подписчиков, каждый месяц теряет Y из-за Z".

СТРУКТУРА КАЖДОГО ТРЕДА — 9 постов:
1. Крючок: конкретный, с цифрой/контрастом/потерей, без общих слов.
2-3. Почему это проблема: что в контенте/воронке ломает деньги.
4-6. Разбор механики: аудитория → доверие → заявка → продажа. Добавь логичные расчёты, если нет точных цифр.
7-8. Что делать: ровно 3 практических шага, максимально прикладных.
9. CTA: "напиши слово РАЗБОР в комментариях, промпты забирай в закрепе t.me/+H1I_MHFuv603ZTdi"

ПРАВИЛА СТИЛЯ:
- Каждый пост 3-5 предложений.
- Пиши живо, резко и конкретно: без воды, официоза, хэштегов, markdown и звёздочек.
- Не выдумывай точные факты о человеке; если данных нет — считай логично и явно: "даже если взять консервативно".
- Первый пост каждого варианта должен быть самостоятельным сильным хуком.
- Посты разделяй строкой ---.

ВЫВЕДИ СТРОГО В ФОРМАТЕ:
===ПАРАДОКС===
[9 постов через ---]
===ЦИФРЫ===
[9 постов через ---]
===БОЛЬ===
[9 постов через ---]"""


def _gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")

    global _last_gemini_call
    last_response: requests.Response | None = None
    for attempt in range(3):
        elapsed = time.time() - _last_gemini_call
        if elapsed < 10:
            time.sleep(10 - elapsed)
        _last_gemini_call = time.time()

        response = requests.post(
            GEMINI_URL,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=90,
        )
        last_response = response
        if response.status_code == 429 and attempt < 2:
            time.sleep(30)
            continue
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    assert last_response is not None
    last_response.raise_for_status()
    raise RuntimeError("Gemini request failed")


def parse_thread_variants(raw: str) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for hook_type in HOOK_TYPES:
        match = re.search(rf"==={hook_type}===(.*?)(?=\n===|\Z)", raw, re.DOTALL)
        if not match:
            continue
        posts = [p.strip() for p in match.group(1).strip().split("---") if p.strip()]
        variants.append({"hook_type": hook_type, "posts": posts})

    if not variants:
        posts = [p.strip() for p in raw.split("---") if p.strip()]
        variants.append({"hook_type": "ПАРАДОКС", "posts": posts})
    return variants


def generate_thread(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate adaptive ПАРАДОКС/ЦИФРЫ/БОЛЬ variants."""
    prompt = build_thread_prompt(data)
    raw = _gemini(prompt)
    return parse_thread_variants(raw)


def _insert_before_marker(text: str, marker: str, block: str) -> str:
    if marker not in text:
        return text.rstrip() + "\n\n" + block.rstrip() + "\n"
    return text.replace(marker, block.rstrip() + "\n" + marker, 1)


def record_thread_win(
    source: str,
    hook_type: str,
    winning_hook: str,
    why_it_worked: str,
    reusable_rule: str,
    prompt_change: str = "",
) -> str:
    """Append a winning thread observation to thread_wins.md."""
    ensure_memory_file()
    date = datetime.now().strftime("%Y-%m-%d")
    block = f"""
### {date} — {hook_type}
- **Источник**: {source or "не указан"}
- **Крючок**: {winning_hook.strip()}
- **Почему зашло**: {why_it_worked.strip()}
- **Правило**: {reusable_rule.strip()}
- **Изменение промпта**: {prompt_change.strip() or reusable_rule.strip()}
"""
    text = THREAD_WINS_FILE.read_text(encoding="utf-8")
    text = _insert_before_marker(text, "<!-- WINS_END -->", block)
    THREAD_WINS_FILE.write_text(text, encoding="utf-8")
    return block.strip()


def improve_prompt_from_lesson(lesson_text: str) -> str:
    """Add an actionable writing rule extracted from a lesson/video analysis."""
    ensure_memory_file()
    rule = lesson_text.strip()
    if not rule:
        raise ValueError("lesson_text is empty")
    date = datetime.now().strftime("%Y-%m-%d")
    block = f"- [{date}] {rule}"
    text = THREAD_WINS_FILE.read_text(encoding="utf-8")
    text = _insert_before_marker(text, "<!-- RULES_END -->", block)
    THREAD_WINS_FILE.write_text(text, encoding="utf-8")
    return block


if __name__ == "__main__":
    import sys

    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(generate_thread(payload), ensure_ascii=False, indent=2))
