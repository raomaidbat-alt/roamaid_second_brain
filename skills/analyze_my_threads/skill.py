#!/usr/bin/env python3
"""Analyze Roman's own Threads account and adapt thread-generation prompts.

Pipeline:
- fetch latest Threads posts via threads_api;
- sort by likes + reposts + comments;
- analyze top 5 with Gemini;
- save rows to Google Sheets "Threads-аналитика";
- update /root/brain/memory/my_threads_patterns.md;
- ensure generate_thread skill reads that memory;
- optionally send weekly Telegram report.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

ROOT = Path("/root")
ENV_FILES = [Path("/root/roamaid_second_brain/.env"), Path("/root/.env")]
GOOGLE_CREDS_FILE = Path("/root/google_credentials.json")
SPREADSHEET_ID = "1nqBnh8WcEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo"
SHEET_NAME = "Threads-аналитика"
HEADERS = ["дата", "текст поста", "лайки", "репосты", "комменты", "тип крючка", "score", "привёл_клиентов (да/нет)"]
PATTERNS_FILE = Path("/root/brain/memory/my_threads_patterns.md")
REPO_PATTERNS_FILE = Path("/root/roamaid_second_brain/brain/memory/my_threads_patterns.md")
GENERATE_THREAD_FILES = [Path("/root/skills/generate_thread/skill.py"), Path("/root/roamaid_second_brain/skills/generate_thread/skill.py")]
SESSION_FILE = Path("/tmp/.threads_session.json")
ROMAN_CHAT_ID = "375420313"
ROMAN_CHANNEL = "https://t.me/+H1I_MHFuv603ZTdi"
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_last_gemini_call = 0.0


@dataclass
class ThreadPost:
    id: str = ""
    code: str = ""
    url: str = ""
    text: str = ""
    likes: int = 0
    reposts: int = 0
    comments: int = 0
    author: str = ""
    created_at: str = ""

    @property
    def score(self) -> int:
        return int(self.likes or 0) + int(self.reposts or 0) + int(self.comments or 0)


def load_env() -> None:
    for path in ENV_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def gemini_url() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"


def gemini(prompt: str, timeout: int = 90) -> str:
    global _last_gemini_call
    last: Optional[requests.Response] = None
    for attempt in range(3):
        elapsed = time.time() - _last_gemini_call
        if elapsed < 10:
            time.sleep(10 - elapsed)
        _last_gemini_call = time.time()
        resp = requests.post(gemini_url(), json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=timeout)
        last = resp
        if resp.status_code in (429, 503) and attempt < 2:
            time.sleep(30 if resp.status_code == 429 else 15)
            continue
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    assert last is not None
    last.raise_for_status()
    raise RuntimeError("Gemini request failed")


def _get_attr(obj: Any, path: str, default: Any = None) -> Any:
    cur = obj
    for part in path.split("."):
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
    return default if cur is None else cur


def extract_post(post: Any) -> ThreadPost:
    caption = _get_attr(post, "caption.text", "") or _get_attr(post, "text", "") or ""
    user = _get_attr(post, "user", None)
    username = _get_attr(user, "username", "") or os.getenv("MY_THREADS_USERNAME", os.getenv("THREADS_USERNAME", ""))
    info = _get_attr(post, "text_post_app_info", None)
    share_info = _get_attr(info, "share_info", None)
    reposts = (
        _get_attr(info, "repost_count", 0)
        or _get_attr(info, "reshare_count", 0)
        or _get_attr(share_info, "repost_count", 0)
        or _get_attr(share_info, "reshare_count", 0)
        or 0
    )
    comments = _get_attr(info, "direct_reply_count", 0) or _get_attr(post, "reply_count", 0) or 0
    code = _get_attr(post, "code", "") or ""
    return ThreadPost(
        id=str(_get_attr(post, "pk", "") or _get_attr(post, "id", "") or ""),
        code=code,
        url=f"https://www.threads.net/@{username}/post/{code}" if code and username else "",
        text=caption,
        likes=int(_get_attr(post, "like_count", 0) or 0),
        reposts=int(reposts or 0),
        comments=int(comments or 0),
        author=username,
        created_at=str(_get_attr(post, "taken_at", "") or _get_attr(post, "created_at", "") or ""),
    )


async def fetch_latest_posts(username: str, count: int = 20) -> List[ThreadPost]:
    if not os.getenv("THREADS_USERNAME") or not os.getenv("THREADS_PASSWORD"):
        raise RuntimeError("THREADS_USERNAME / THREADS_PASSWORD are not set")
    try:
        from threads_api.src.threads_api import ThreadsAPI
    except Exception as exc:
        raise RuntimeError(
            "Не удалось импортировать threads_api. На этом хосте пакет установлен, но может быть несовместим с Python 3.8/instagrapi. "
            "Проверь окружение threads_api. Исходная ошибка: %s" % exc
        )

    api = ThreadsAPI()
    try:
        await api.login(os.getenv("THREADS_USERNAME"), os.getenv("THREADS_PASSWORD"), cached_token_path=str(SESSION_FILE))
        user_id = await api.get_user_id_from_username(username.lstrip("@"))
        data = await api.get_user_threads(user_id, count=count)
        posts: List[ThreadPost] = []
        for thread in (getattr(data, "threads", None) or []):
            for item in (getattr(thread, "thread_items", None) or []):
                post = getattr(item, "post", None)
                if not post:
                    continue
                info = getattr(post, "text_post_app_info", None)
                if info and getattr(info, "is_reply", False):
                    continue
                posts.append(extract_post(post))
                if len(posts) >= count:
                    break
            if len(posts) >= count:
                break
        return posts[:count]
    finally:
        try:
            await api.close_gracefully()
        except Exception:
            pass


def analyze_top_posts(top_posts: List[ThreadPost]) -> Dict[str, Any]:
    payload = []
    for p in top_posts:
        item = asdict(p)
        item["score"] = p.score
        payload.append(item)
    prompt = f"""Ты Gemini-аналитик контента Романа. Проанализируй топ-5 Threads постов по метрикам.

Нужно определить:
- тип крючка: ПАРАДОКС/ЦИФРЫ/БОЛЬ/ИСТОРИЯ;
- структуру поста;
- почему мог привести к действию: подписка / запрос / переход / сохранение;
- повторяющиеся паттерны в топах;
- как улучшить промпт генератора новых тредов.

Важно: Роман пишет как человек, длинно и понятно, триггерно, через историю, не как учитель. CTA всегда в канал {ROMAN_CHANNEL}.

Верни СТРОГО JSON без markdown:
{{
  "posts": [{{"text_start":"...", "hook_type":"...", "structure":"...", "why_action":"...", "client_action":"да/нет"}}],
  "repeating_patterns": ["..."],
  "prompt_rules": ["..."],
  "weekly_recommendations": ["..."]
}}

ПОСТЫ:
{json.dumps(payload, ensure_ascii=False)[:9000]}
"""
    raw = gemini(prompt, timeout=120)
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"posts": [], "repeating_patterns": [raw], "prompt_rules": [raw], "weekly_recommendations": []}


def ensure_sheet():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    gc = gspread.authorize(Credentials.from_service_account_file(str(GOOGLE_CREDS_FILE), scopes=scopes))
    ss = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = ss.worksheet(SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS)
    values = ws.get_all_values()
    if not values or values[0] != HEADERS:
        ws.resize(rows=max(len(values) + 1, 1000), cols=len(HEADERS))
        ws.update("A1:H1", [HEADERS])
    return ws


def append_sheet_rows(posts: List[ThreadPost], analysis: Dict[str, Any]) -> None:
    ws = ensure_sheet()
    analyzed = analysis.get("posts") or []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for idx, post in enumerate(posts):
        item = analyzed[idx] if idx < len(analyzed) and isinstance(analyzed[idx], dict) else {}
        rows.append([
            now,
            post.text[:4500],
            post.likes,
            post.reposts,
            post.comments,
            item.get("hook_type", ""),
            post.score,
            item.get("client_action", "нет"),
        ])
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")


def update_patterns_file(top_posts: List[ThreadPost], analysis: Dict[str, Any]) -> str:
    PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPO_PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# My Threads Patterns — что реально заходит у аудитории Романа",
        "",
        f"Обновлено: {now}",
        f"CTA всегда: {ROMAN_CHANNEL}",
        "",
        "## Топ-5 последних постов",
    ]
    for i, post in enumerate(top_posts, 1):
        lines.append(f"{i}. score={post.score}, likes={post.likes}, reposts={post.reposts}, comments={post.comments}")
        lines.append(f"   {post.text[:500].replace(chr(10), ' ')}")
    lines += ["", "## Повторяющиеся паттерны"]
    for p in analysis.get("repeating_patterns") or []:
        lines.append(f"- {p}")
    lines += ["", "## Правила для генератора тредов"]
    for p in analysis.get("prompt_rules") or []:
        lines.append(f"- {p}")
    lines += ["", "## Рекомендации"]
    for p in analysis.get("weekly_recommendations") or []:
        lines.append(f"- {p}")
    text = "\n".join(lines).strip() + "\n"
    PATTERNS_FILE.write_text(text, encoding="utf-8")
    REPO_PATTERNS_FILE.write_text(text, encoding="utf-8")
    return text


def patch_generate_thread_skill() -> None:
    for path in GENERATE_THREAD_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "MY_THREADS_PATTERNS_FILE" not in text:
            text = text.replace(
                "THREAD_WINS_FILE = Path(\"/root/brain/memory/thread_wins.md\")",
                "THREAD_WINS_FILE = Path(\"/root/brain/memory/thread_wins.md\")\nMY_THREADS_PATTERNS_FILE = Path(\"/root/brain/memory/my_threads_patterns.md\")",
            )
        if "def load_my_threads_patterns" not in text:
            marker = "def load_thread_wins(max_chars: int = 8000) -> str:\n"
            block = '''\ndef load_my_threads_patterns(max_chars: int = 8000) -> str:\n    """Return performance-based Threads patterns from Roman's own account."""\n    if not MY_THREADS_PATTERNS_FILE.exists():\n        return ""\n    text = MY_THREADS_PATTERNS_FILE.read_text(encoding="utf-8")\n    return text[-max_chars:] if len(text) > max_chars else text\n\n'''
            text = text.replace(marker, block + marker)
        if "my_patterns = load_my_threads_patterns()" not in text:
            text = text.replace("wins = load_thread_wins()", "wins = load_thread_wins()\n    my_patterns = load_my_threads_patterns()")
            text = text.replace(
                "ПАМЯТЬ ПОБЕД И ПРАВИЛА, КОТОРЫЕ УЖЕ СРАБОТАЛИ:\n{wins}",
                "ПАМЯТЬ ПОБЕД И ПРАВИЛА, КОТОРЫЕ УЖЕ СРАБОТАЛИ:\n{wins}\n\nПАТТЕРНЫ МОЕГО THREADS АККАУНТА ПО МЕТРИКАМ:\n{my_patterns}",
            )
        path.write_text(text, encoding="utf-8")


def weekly_report_text(top_posts: List[ThreadPost], analysis: Dict[str, Any]) -> str:
    top = top_posts[0] if top_posts else ThreadPost(text="нет данных")
    patterns = "\n".join(f"• {x}" for x in (analysis.get("repeating_patterns") or [])[:5]) or "• пока мало данных"
    recs = "\n".join(f"• {x}" for x in (analysis.get("weekly_recommendations") or [])[:5]) or "• продолжать тестировать историю + контраст + живую боль"
    return (
        "🧵 Еженедельный отчёт Threads\n\n"
        f"Топ пост недели: score={top.score}, ❤️ {top.likes}, 🔁 {top.reposts}, 💬 {top.comments}\n"
        f"{top.text[:700]}\n\n"
        "Что сработало:\n" + patterns + "\n\n"
        "Рекомендации на следующую неделю:\n" + recs
    )


def send_telegram(text: str) -> None:
    token = os.getenv("TELEGRAM_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("OWNER_CHAT_ID") or ROMAN_CHAT_ID
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not set")
    for i in range(0, len(text), 3900):
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text[i:i+3900]},
            timeout=30,
        )
        resp.raise_for_status()


async def run_analysis(send_report: bool = False) -> Dict[str, Any]:
    load_env()
    username = os.getenv("MY_THREADS_USERNAME") or os.getenv("THREADS_TARGET_USERNAME") or os.getenv("THREADS_USERNAME")
    if not username:
        raise RuntimeError("Set MY_THREADS_USERNAME or THREADS_USERNAME")
    posts = await fetch_latest_posts(username, count=20)
    ranked = sorted(posts, key=lambda p: p.score, reverse=True)
    top5 = ranked[:5]
    analysis = analyze_top_posts(top5)
    append_sheet_rows(top5, analysis)
    update_patterns_file(top5, analysis)
    patch_generate_thread_skill()
    if send_report:
        send_telegram(weekly_report_text(top5, analysis))
    return {"ok": True, "username": username, "analyzed": len(top5), "top_score": top5[0].score if top5 else 0}


async def run_report() -> Dict[str, Any]:
    load_env()
    username = os.getenv("MY_THREADS_USERNAME") or os.getenv("THREADS_TARGET_USERNAME") or os.getenv("THREADS_USERNAME")
    posts = await fetch_latest_posts(username, count=20)
    top5 = sorted(posts, key=lambda p: p.score, reverse=True)[:5]
    analysis = analyze_top_posts(top5)
    send_telegram(weekly_report_text(top5, analysis))
    return {"ok": True, "reported": True, "top_score": top5[0].score if top5 else 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["analyze", "report", "analyze_and_report"], nargs="?", default="analyze")
    args = parser.parse_args()
    if args.command == "report":
        result = asyncio.run(run_report())
    else:
        result = asyncio.run(run_analysis(send_report=args.command == "analyze_and_report"))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
