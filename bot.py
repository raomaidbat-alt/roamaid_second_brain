import os
import re
import io
import json
import time
import random
import asyncio
import datetime
import logging
import traceback
import urllib.parse
import requests
import gspread
import aiohttp
import aiohttp.web
import phonenumbers
from phonenumbers import geocoder as ph_geocoder, carrier as ph_carrier
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import NetworkError, RetryAfter, TimedOut
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from audit_agent import run_audit, run_audit_sites, get_ab_stats_text
import daily_logger
from skills.learn_from_video.skill import learn_from_video
from outreach.outreach_manager import (
    add_contact,
    get_stats as outreach_get_stats,
    load_email_config,
    run_outreach,
    save_email_config,
)
from skills.analyze_threads.skill import analyze_threads
from skills.post_to_threads.skill import post_to_threads, post_thread_series
try:
    from skills.generate_thread.skill import (
        generate_thread as adaptive_generate_thread,
        record_thread_win,
    )
except Exception as e:
    print(f"Adaptive thread skill unavailable: {e}")
    adaptive_generate_thread = None
    record_thread_win = None

OWNER_CHAT_ID = None

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
ANALYZER_URL = "http://150.241.116.28:8000/analyze"
WHISPER_URL = "http://150.241.116.28:8000/transcribe-file"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)
FEEDBACK_FILE = "/root/feedback.json"
GOOGLE_CREDS_FILE = "/root/google_credentials.json"
SPREADSHEET_ID = "1nqBnh8WcEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo"
BOT_ERROR_LOG = "/root/bot_errors.log"

logging.basicConfig(
    filename=BOT_ERROR_LOG,
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

REELS_HEADERS = ["дата", "платформа", "url", "автор", "просмотры", "лайки", "длительность", "транскрипция", "оценка"]
ACTIVITY_HEADERS = ["дата", "тип", "количество", "заметка"]

HOOK_TYPES = ["ПАРАДОКС", "ЦИФРЫ", "БОЛЬ"]


# ── Google Sheets ─────────────────────────────────────────────────────────────

def _gc():
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def _worksheet(name: str, headers: list):
    ss = _gc().open_by_key(SPREADSHEET_ID)
    try:
        ws = ss.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=name, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws


def sheets_append_reel(url: str, platform: str, author: str, views, likes, duration, transcript: str):
    ws = _worksheet("Ролики", REELS_HEADERS)
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    ws.append_row([date, platform, url, author or "", views or "", likes or "", duration or "", transcript or "", ""])


def sheets_update_reel_rating(url: str, rating_emoji: str):
    try:
        ws = _worksheet("Ролики", REELS_HEADERS)
        cell = ws.find(url, in_column=3)
        if cell:
            ws.update_cell(cell.row, 9, rating_emoji)
    except Exception as e:
        print(f"Sheets rating update error: {e}")


def sheets_append_activity(type_: str, count: int, note: str = ""):
    ws = _worksheet("Активность", ACTIVITY_HEADERS)
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    ws.append_row([date, type_, count, note or ""])


# ── Helpers ───────────────────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    if "instagram.com" in url:
        return "Instagram"
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    return "Unknown"


def parse_activity(text: str) -> list:
    results = []
    patterns = [
        (r'(\d+)\s*звонк\w*', 'звонок'),
        (r'(\d+)\s*рассылк\w*', 'рассылка'),
        (r'(\d+)\s*встреч\w*', 'встреча'),
    ]
    for pattern, type_ in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            results.append({"type": type_, "count": int(m.group(1))})
    return results


_last_gemini_call = 0.0

def gemini(prompt: str) -> str:
    global _last_gemini_call
    for attempt in range(3):
        # пауза 10 сек между запросами
        elapsed = time.time() - _last_gemini_call
        if elapsed < 10:
            time.sleep(10 - elapsed)
        _last_gemini_call = time.time()

        resp = requests.post(
            GEMINI_URL,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=90,
        )
        if resp.status_code == 429:
            time.sleep(30)
            continue
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    resp.raise_for_status()


def _load_feedback_stats() -> str:
    if not os.path.exists(FEEDBACK_FILE):
        return ""
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
        counts = {}
        for r in records:
            hook = r.get("hook_type", "")
            rating = r.get("rating", "")
            if hook and rating == "good":
                counts[hook] = counts.get(hook, 0) + 1
        if counts:
            best = max(counts, key=counts.get)
            return f"По прошлым данным лучше всего заходит формат {best} ({counts[best]} положительных оценок). Учти это при генерации."
        return ""
    except Exception:
        return ""


def generate_thread(data: dict) -> list:
    if adaptive_generate_thread is not None:
        try:
            return adaptive_generate_thread(data)
        except Exception as e:
            print(f"Adaptive thread generation failed, fallback to legacy prompt: {e}")

    content = data.get("content", data)
    transcript = content.get("transcript") or data.get("transcript") or ""
    meta = data.get("meta", {})
    author = meta.get("author") or meta.get("uploader") or "блогера"
    likes = meta.get("like_count") or ""
    views = meta.get("view_count") or ""
    caption = content.get("caption", "")

    feedback_hint = _load_feedback_stats()

    hook_descriptions = """
ПАРАДОКС — формат: "{Описание блогера}, у которого есть {что есть}, но нет {чего нет}"
Пример: "Эксперт с 80к подписчиками и 3 млн просмотров, у которого есть аудитория, но нет стабильного дохода"

ЦИФРЫ — формат: "При {X} подписчиках он зарабатывает только {Y} — хотя мог бы {Z}"
Пример: "При 45к подписчиках он зарабатывает 30к в месяц — хотя мог бы 300к"

БОЛЬ — формат: "{Имя}, {X} подписчиков, {конкретная боль которая мешает зарабатывать}"
Пример: "Антон, 120к подписчиков, каждый месяц теряет 200к рублей потому что не умеет продавать в директе"
"""

    prompt = f"""Ты копирайтер и эксперт по Instagram-маркетингу. Пишешь треды в стиле rominb_bull — живые, с конкретными цифрами, без воды и официоза.

Данные ролика:
Автор: {author}
Просмотры: {views}
Лайки: {likes}
Описание: {caption[:500] if caption else "(нет)"}
Транскрипция: {transcript[:1000] if transcript else "(недоступна)"}

{feedback_hint}

Сгенерируй 3 варианта треда с разными крючками. Используй эти форматы крючков:
{hook_descriptions}

Структура каждого треда (9 постов):
- Пост 1: крючок по своему формату — конкретный, цепляющий, с реальными цифрами из данных ролика
- Посты 2-6: конкретные цифры воронки, что именно не работает и почему, анализ монетизации
- Посты 7-8: что нужно сделать конкретно — ровно 3 шага, без воды
- Пост 9 (последний): CTA — "напиши слово РАЗБОР в комментариях, промпты забирай в закрепе t.me/+H1I_MHFuv603ZTdi"

Правила стиля:
- Каждый пост 3-5 предложений
- Конкретные цифры везде — если нет реальных, рассчитай логично
- Живой язык, без официоза и клише
- Без звёздочек, решёток и markdown
- Посты разделяй символом ---

Выведи строго в этом формате:

===ПАРАДОКС===
[9 постов через ---]

===ЦИФРЫ===
[9 постов через ---]

===БОЛЬ===
[9 постов через ---]"""

    raw = gemini(prompt)

    variants = []
    for hook_type in ["ПАРАДОКС", "ЦИФРЫ", "БОЛЬ"]:
        pattern = rf"==={hook_type}===(.*?)(?====|\Z)"
        m = re.search(pattern, raw, re.DOTALL)
        if m:
            block = m.group(1).strip()
            posts = [p.strip() for p in block.split("---") if p.strip()]
            variants.append({"hook_type": hook_type, "posts": posts})

    if not variants:
        posts = [p.strip() for p in raw.split("---") if p.strip()]
        variants = [{"hook_type": "ПАРАДОКС", "posts": posts}]

    return variants


def save_feedback(url: str, rating: str, hook_type: str, thread_preview: str) -> None:
    records = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
    records.append({
        "ts": datetime.datetime.utcnow().isoformat(),
        "url": url,
        "rating": rating,
        "hook_type": hook_type,
        "thread_preview": thread_preview[:200],
    })
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# ── Zvonok helpers ───────────────────────────────────────────────────────────

def _get_phone_region(phone: str) -> str:
    try:
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 11 and digits[0] in ('7', '8'):
            normalized = '+7' + digits[1:]
        elif len(digits) == 10:
            normalized = '+7' + digits
        else:
            normalized = '+' + digits
        parsed = phonenumbers.parse(normalized)
        region = ph_geocoder.description_for_number(parsed, "ru")
        op = ph_carrier.name_for_number(parsed, "ru")
        parts = []
        if region:
            parts.append(region)
        if op:
            parts.append(f"({op})")
        return " ".join(parts) if parts else "Россия"
    except Exception:
        return "Неизвестно"


async def _search_phone(phone: str) -> str:
    query = urllib.parse.quote(f"{phone} кто звонит")
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                html = await resp.text()
        snippets = re.findall(r'class="result__snippet">(.*?)</a>', html, re.DOTALL)
        if snippets:
            clean = re.sub(r'<[^>]+>', '', snippets[0]).strip()
            return clean[:300] if clean else "Нет информации"
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        if titles:
            clean = re.sub(r'<[^>]+>', '', titles[0]).strip()
            return clean[:300] if clean else "Нет информации"
        return "Не найдено в открытом доступе"
    except asyncio.TimeoutError:
        return "Поиск превысил таймаут"
    except Exception as e:
        return f"Ошибка поиска: {str(e)[:100]}"


async def handle_zvonok(request: aiohttp.web.Request) -> aiohttp.web.Response:
    ct_phone = request.rel_url.query.get("ct_phone", "")
    button_num = request.rel_url.query.get("button_num", "")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    region = _get_phone_region(ct_phone)
    search_result = await _search_phone(ct_phone)

    text = (
        f"📞 Новая заявка со звонка!\n"
        f"Номер: {ct_phone}\n"
        f"Кнопка: {button_num}\n"
        f"Регион: {region}\n"
        f"Кто это может быть: {search_result}\n"
        f"Время: {now}"
    )

    daily_logger.log_zvonok(ct_phone, region)
    if OWNER_CHAT_ID:
        try:
            await app.bot.send_message(OWNER_CHAT_ID, text)
        except Exception as e:
            print(f"Ошибка отправки в Telegram: {e}")
    else:
        print(f"[zvonok] OWNER_CHAT_ID не определён. {text}")

    return aiohttp.web.Response(text="OK")


# ── Handlers ──────────────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global OWNER_CHAT_ID
    OWNER_CHAT_ID = update.message.chat_id
    text = update.message.text.strip()

    if context.user_data.get("awaiting_activity"):
        context.user_data["awaiting_activity"] = False
        await _save_activity_from_text(text, update, context)
        return

    if "outreach_step" in context.user_data:
        done, reply = _next_outreach_step(context, text)
        await update.message.reply_text(reply)
        return

    if "email_setup_step" in context.user_data:
        done, reply = _next_email_step(context, text)
        await update.message.reply_text(reply)
        return

    yt_match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/\S+|youtu\.be/\S+))', text)
    if yt_match and re.search(r'\b(учись|learn)\b', text, re.IGNORECASE):
        url = yt_match.group(1)
        await update.message.reply_text("⏳ Скачиваю и анализирую видео, это займёт 2-5 минут...")
        result = await learn_from_video(url)
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i+4000], parse_mode="Markdown")
        return

    threads_match = re.search(r'(https?://(?:www\.)?threads\.net/@[\w./\-]+)', text)
    if threads_match:
        url = threads_match.group(1)
        await update.message.reply_text("⏳ Анализирую Threads, подожди...")
        result = await analyze_threads(url)
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i+4000])
        adapted_match = re.search(r'АДАПТАЦИЯ ДЛЯ НАШЕЙ НИШИ:\n(.*)', result, re.DOTALL)
        if adapted_match:
            context.user_data["pending_thread_text"] = adapted_match.group(1).strip()
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Опубликовать тред", callback_data="threads_publish_confirm"),
                InlineKeyboardButton("❌ Не публиковать", callback_data="threads_publish_cancel"),
            ]])
            await update.message.reply_text(
                "Опубликовать адаптированный тред в Threads?", reply_markup=keyboard
            )
        return

    if not any(x in text for x in ["instagram.com", "youtube.com", "youtu.be"]):
        return

    await update.message.reply_text("⏳ Анализирую видео, подожди...")

    try:
        res = requests.post(ANALYZER_URL, json={"url": text}, timeout=120)
        res.raise_for_status()
        data = res.json()

        content = data.get("content") or {}
        meta = data.get("meta") or {}
        transcript = content.get("transcript") or data.get("transcript") or ""
        author = meta.get("author") or meta.get("uploader") or ""
        views = meta.get("view_count") or meta.get("views") or ""
        likes = meta.get("like_count") or meta.get("likes") or ""
        duration = meta.get("duration") or ""
        platform = detect_platform(text)
        daily_logger.log_account_analyzed(author or text.split("/")[-1], str(views) if views else "")

        try:
            sheets_append_reel(text, platform, author, views, likes, duration, transcript)
        except Exception as e:
            print(f"Sheets append error: {e}")

        analysis_prompt = f"""Ты эксперт по контент-маркетингу. Проанализируй видео и ответь строго в этом формате без markdown, звёздочек, решёток и заголовков:

🎯 О чём ролик: [1-2 предложения]

✅ Что зашло:
— [пункт 1, 1 строка]
— [пункт 2, 1 строка]
— [пункт 3, 1 строка]

💡 Улучшения:
— [пункт 1, 1-2 строки]
— [пункт 2, 1-2 строки]
— [пункт 3, 1-2 строки]

🚀 Идеи для новых роликов:
— [пункт 1, 1 строка]
— [пункт 2, 1 строка]
— [пункт 3, 1 строка]

Итого не больше 30 строк. Только текст, никаких символов форматирования.

Транскрипция: {transcript if transcript else "(недоступна)"}
Данные: {json.dumps(data, ensure_ascii=False)}"""

        analysis = gemini(analysis_prompt)
        for i in range(0, len(analysis), 4000):
            await update.message.reply_text(analysis[i : i + 4000])

        await update.message.reply_text("🧵 Генерирую 3 варианта треда...")
        variants = generate_thread(data)
        daily_logger.log_thread_generated(author or "unknown", variants[0]["hook_type"] if variants else "")

        context.user_data["last_url"] = text
        context.user_data["thread_variants"] = variants
        context.user_data["chosen_hook"] = None

        preview_text = "Выбери формат треда — вот крючки (первый пост) каждого:\n\n"
        for i, v in enumerate(variants, 1):
            hook = v["posts"][0] if v["posts"] else ""
            hook_short = hook[:300] + ("..." if len(hook) > 300 else "")
            preview_text += f"━━━ Вариант {i} [{v['hook_type']}] ━━━\n{hook_short}\n\n"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"Вариант {i+1} — {v['hook_type']}", callback_data=f"thread_pick_{i}")
            for i, v in enumerate(variants)
        ]])

        await update.message.reply_text(preview_text[:4000], reply_markup=keyboard)

    except requests.exceptions.ConnectionError:
        await update.message.reply_text(
            "Не могу подключиться к серверу анализа (150.241.116.28:8000). Он запущен?"
        )
    except requests.exceptions.Timeout:
        await update.message.reply_text("Сервер анализа не ответил за 120 сек. Попробуй позже.")
    except requests.exceptions.HTTPError as e:
        await update.message.reply_text(f"Ошибка от сервера: {e}")
    except Exception as e:
        await update.message.reply_text(f"Неожиданная ошибка: {e}")


async def handle_thread_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.split("_")[-1])
    variants = context.user_data.get("thread_variants", [])

    if idx >= len(variants):
        await query.edit_message_text("Что-то пошло не так, попробуй заново.")
        return

    chosen = variants[idx]
    hook_type = chosen["hook_type"]
    posts = chosen["posts"]

    context.user_data["chosen_hook"] = hook_type
    context.user_data["last_thread"] = posts[0] if posts else ""
    context.user_data["last_thread_posts"] = posts

    await query.edit_message_text(f"Отправляю тред — формат {hook_type}...")

    for i, post in enumerate(posts, 1):
        await query.message.reply_text(f"[{i}/{len(posts)}]\n\n{post}")

    url = context.user_data.get("last_url", "")
    save_feedback(url, "chosen", hook_type, posts[0] if posts else "")
    daily_logger.log_thread_chosen(url.split("/")[-2] if "/" in url else url, hook_type)

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("👍 Зашло", callback_data="feedback_good"),
        InlineKeyboardButton("👎 Не то", callback_data="feedback_bad"),
    ]])
    await query.message.reply_text(
        "Тред готов 👆 Как зашло? Запомню и улучшу следующий.",
        reply_markup=keyboard,
    )


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rating = "good" if query.data == "feedback_good" else "bad"
    url = context.user_data.get("last_url", "")
    hook_type = context.user_data.get("chosen_hook", "")
    thread_preview = context.user_data.get("last_thread", "")
    rating_emoji = "👍" if rating == "good" else "👎"

    save_feedback(url, rating, hook_type, thread_preview)

    if rating == "good" and record_thread_win is not None:
        try:
            record_thread_win(
                source=url,
                hook_type=hook_type,
                winning_hook=thread_preview,
                why_it_worked="Хозяин отметил вариант как зашедший через Telegram feedback 👍.",
                reusable_rule=(
                    f"Усиливать формат {hook_type}: сохранять похожую механику крючка, "
                    "конкретику и структуру победившего треда."
                ),
                prompt_change="Добавлять этот победивший паттерн в память и учитывать при следующих генерациях.",
            )
        except Exception as e:
            print(f"Thread win memory write error: {e}")

    if url:
        try:
            sheets_update_reel_rating(url, rating_emoji)
        except Exception as e:
            print(f"Sheets rating error: {e}")

    emoji = "🔥" if rating == "good" else "📝"
    reply = "Отлично, буду делать больше в таком стиле!" if rating == "good" else "Понял, постараюсь улучшить!"
    await query.edit_message_text(f"{emoji} {reply}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global OWNER_CHAT_ID
    OWNER_CHAT_ID = update.message.chat_id
    await update.message.reply_text("🎤 Транскрибирую голосовое...")

    try:
        tg_file = await context.bot.get_file(update.message.voice.file_id)
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        buf.seek(0)

        resp = requests.post(
            WHISPER_URL,
            files={"file": ("voice.ogg", buf, "audio/ogg")},
            timeout=300,
        )
        resp.raise_for_status()
        transcript = resp.json().get("text", "")

    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            context.user_data["awaiting_activity"] = True
            await update.message.reply_text(
                "⚠️ Сервер транскрипции недоступен.\n\n"
                "Напиши активность текстом, например:\n"
                "<code>15 звонков, 3 рассылки, 2 встречи</code>",
                parse_mode="HTML",
            )
            return
        await update.message.reply_text(f"Ошибка сервера транскрипции: {e}")
        return
    except requests.exceptions.ConnectionError:
        context.user_data["awaiting_activity"] = True
        await update.message.reply_text(
            "⚠️ Не могу подключиться к серверу транскрипции.\n\n"
            "Напиши активность текстом, например:\n"
            "<code>15 звонков, 3 рассылки, 2 встречи</code>",
            parse_mode="HTML",
        )
        return
    except requests.exceptions.Timeout:
        await update.message.reply_text("Сервер транскрипции не ответил за 60 сек.")
        return
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
        return

    await _save_activity_from_text(transcript, update, context)


async def handle_audit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    asyncio.create_task(run_audit(context.bot, chat_id))
    await update.message.reply_text("🚀 Запускаю аудит аккаунтов из accounts.txt...")



async def handle_audit_sites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    asyncio.create_task(run_audit_sites(context.bot, chat_id))
    await update.message.reply_text(
        "Запускаю анализ сайтов из листа Сайты-список..." + chr(10) +
        "Отчёт буду присылать каждые 3 сайта."
    )

async def handle_analyze_threads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Укажи ссылку или аккаунт:\n"
            "/analyze_threads https://www.threads.net/@username\n"
            "/analyze_threads https://www.threads.net/@user/post/CODE\n"
            "/analyze_threads @username"
        )
        return
    target = args[0]
    await update.message.reply_text("⏳ Анализирую Threads, подожди...")
    result = await analyze_threads(target)
    for i in range(0, len(result), 4000):
        await update.message.reply_text(result[i:i+4000])

    # Offer to post the adapted thread
    adapted_match = re.search(r'АДАПТАЦИЯ ДЛЯ НАШЕЙ НИШИ:\n(.*)', result, re.DOTALL)
    if adapted_match:
        context.user_data["pending_thread_text"] = adapted_match.group(1).strip()
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Опубликовать тред", callback_data="threads_publish_confirm"),
            InlineKeyboardButton("❌ Не публиковать", callback_data="threads_publish_cancel"),
        ]])
        await update.message.reply_text("Опубликовать адаптированный тред в Threads?", reply_markup=keyboard)


async def handle_threads_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "threads_publish_cancel":
        await query.edit_message_text("❌ Публикация отменена.")
        return

    thread_text = context.user_data.get("pending_thread_text", "")
    if not thread_text:
        await query.edit_message_text("❌ Нет текста для публикации.")
        return

    await query.edit_message_text("⏳ Публикую тред в Threads...")

    # Split by --- into individual posts
    posts = [p.strip() for p in re.split(r'\n---\n', thread_text) if p.strip()]

    if len(posts) > 1:
        result = await post_thread_series(posts)
        if result["ok"]:
            urls = "\n".join(f"• {u}" for u in result["urls"] if u)
            await query.message.reply_text(f"✅ Тред опубликован ({len(posts)} постов)!\n\n{urls}")
        else:
            await query.message.reply_text(f"❌ Ошибка публикации: {result['error']}")
    else:
        result = await post_to_threads(thread_text)
        if result["ok"]:
            await query.message.reply_text(f"✅ Пост опубликован!\n{result['url']}")
        else:
            await query.message.reply_text(f"❌ Ошибка публикации: {result['error']}")

    context.user_data.pop("pending_thread_text", None)


async def handle_learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Укажи YouTube URL: /learn https://youtube.com/...")
        return
    url = args[0]
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("Укажи YouTube ссылку.")
        return
    await update.message.reply_text("⏳ Скачиваю и анализирую видео, это займёт 2-5 минут...")
    result = await learn_from_video(url)
    for i in range(0, len(result), 4000):
        await update.message.reply_text(result[i:i+4000], parse_mode="Markdown")


async def handle_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = daily_logger.get_today_stats()
    today = datetime.datetime.now().strftime("%d.%m.%Y")
    voice_str = ""
    if stats["voice"]:
        voice_str = f"\n• Записано активности: {stats['voice'][-1]}"
    text = (
        f"Сегодня {today}:\n"
        f"• Проанализировано аккаунтов: {stats['accounts']}\n"
        f"• Сгенерировано тредов: {stats['threads']}\n"
        f"• Аудитов проведено: {stats['audits']}\n"
        f"• Сайтов проанализировано: {stats['sites']}\n"
        f"• Новых заявок: {stats['leads']}"
        f"{voice_str}"
    )
    log_block = daily_logger.get_today_log()
    if log_block:
        entries = [l for l in log_block.split("\n") if l.startswith("- ")]
        if entries:
            text += "\n\nПоследние события:\n" + "\n".join(entries[-5:])
    await update.message.reply_text(text)


async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Считаю статистику...")
    loop = asyncio.get_event_loop()
    try:
        text = await loop.run_in_executor(None, lambda: asyncio.run(get_ab_stats_text()))
    except Exception:
        from audit_agent import _get_ab_stats
        stats = _get_ab_stats()
        labels = {"А": "А (цифры)", "Б": "Б (боль)", "В": "В (комплимент)"}
        lines = ["📊 Статистика сообщений:"]
        best_var, best_rate = None, -1.0
        for var in ["А", "Б", "В"]:
            s = stats[var]
            sent, replied = s["sent"], s["replied"]
            rate = round(replied / sent * 100) if sent > 0 else 0
            lines.append(f"Вариант {labels[var]}: отправлено {sent}, ответили {replied} ({rate}%)")
            if sent > 0 and rate > best_rate:
                best_rate, best_var = rate, var
        if best_var and stats[best_var]["sent"] > 0:
            lines.append(f"\n🏆 Лучший вариант: {labels[best_var]}")
        else:
            lines.append("\nПока недостаточно данных")
        text = "\n".join(lines)
    await update.message.reply_text(text)


async def _save_activity_from_text(text: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    activities = parse_activity(text)
    if not activities:
        await update.message.reply_text(
            f"Транскрипция: {text}\n\nНе смог распознать активности. "
            "Напиши в формате: <code>15 звонков, 3 рассылки</code>",
            parse_mode="HTML",
        )
        return

    saved = []
    for item in activities:
        sheets_append_activity(item["type"], item["count"], text)
        saved.append(f"{item['count']} {item['type']}")
    daily_logger.log_voice_activity(activities)

    await update.message.reply_text(f"✅ Записал: {', '.join(saved)}")


# ── Outreach handlers ─────────────────────────────────────────────────────────

_OUTREACH_ADD_FIELDS = ["name", "telegram", "email", "audit_type", "audit_data"]
_OUTREACH_ADD_PROMPTS = {
    "name":       "Имя контакта:",
    "telegram":   "Telegram username (например @username) или - если нет:",
    "email":      "Email адрес или - если нет:",
    "audit_type": "Тип аудита — введи funnel (воронка) или site (сайт):",
    "audit_data": "Данные аудита для персонализации (опиши коротко что нашли):",
}
_SETUP_EMAIL_FIELDS = ["login", "app_password"]
_SETUP_EMAIL_PROMPTS = {
    "login":        "Gmail адрес (например you@gmail.com):",
    "app_password": "App Password от Gmail (16 символов без пробелов):",
}


async def handle_outreach_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from outreach.outreach_manager import load_contacts
    contacts = load_contacts()
    pending = [c for c in contacts if c.get("status") == "pending"]
    if not pending:
        await update.message.reply_text("Нет контактов со статусом pending. Добавь через /outreach_add.")
        return
    await update.message.reply_text(
        f"🚀 Запускаю рассылку: {len(pending)} контактов...\n"
        "Задержка 30-60 сек между сообщениями. Отчёт пришлю после завершения."
    )
    asyncio.create_task(_run_outreach_task(update.message.chat_id, context.bot))


async def _run_outreach_task(chat_id: int, bot):
    try:
        stats = await run_outreach(bot)
        text = (
            f"✅ Рассылка завершена!\n"
            f"• Отправлено: {stats['sent']}\n"
            f"• Ошибок: {stats['failed']}\n"
            f"• Пропущено: {stats['skipped']}"
        )
    except Exception as e:
        logger.error("Outreach task error", exc_info=True)
        text = f"❌ Ошибка рассылки: {e}"
    await bot.send_message(chat_id=chat_id, text=text)


async def handle_outreach_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["outreach_step"] = 0
    context.user_data["outreach_temp"] = {}
    first_field = _OUTREACH_ADD_FIELDS[0]
    await update.message.reply_text(
        f"Добавляем новый контакт. Шаг 1/{len(_OUTREACH_ADD_FIELDS)}\n\n"
        + _OUTREACH_ADD_PROMPTS[first_field]
    )


async def handle_outreach_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = outreach_get_stats()
    email_cfg = load_email_config()
    email_status = f"✅ {email_cfg['login']}" if email_cfg else "❌ не настроен"
    text = (
        f"📊 Статистика рассылки:\n"
        f"• Всего контактов: {stats['total']}\n"
        f"• Ожидает: {stats['pending']}\n"
        f"• Отправлено: {stats['sent']}\n"
        f"• Ошибок: {stats['failed']}\n\n"
        f"📧 Gmail: {email_status}"
    )
    await update.message.reply_text(text)


async def handle_setup_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email_setup_step"] = 0
    context.user_data["email_setup_temp"] = {}
    await update.message.reply_text(
        "Настройка Gmail для рассылки. Шаг 1/2\n\n"
        + _SETUP_EMAIL_PROMPTS["login"]
    )


def _next_outreach_step(context, value: str):
    """Advance outreach_add state machine. Returns (done, reply_text)."""
    step = context.user_data.get("outreach_step", 0)
    field = _OUTREACH_ADD_FIELDS[step]

    # Validate audit_type
    if field == "audit_type" and value.strip().lower() not in ("funnel", "site"):
        return False, "Введи funnel или site:"

    context.user_data["outreach_temp"][field] = value.strip() if value.strip() != "-" else ""
    step += 1
    context.user_data["outreach_step"] = step

    if step >= len(_OUTREACH_ADD_FIELDS):
        data = context.user_data.pop("outreach_temp")
        context.user_data.pop("outreach_step", None)
        add_contact(data)
        summary = (
            f"✅ Контакт добавлен!\n"
            f"• Имя: {data.get('name')}\n"
            f"• Telegram: {data.get('telegram') or '—'}\n"
            f"• Email: {data.get('email') or '—'}\n"
            f"• Тип аудита: {data.get('audit_type')}\n"
            f"• Статус: pending"
        )
        return True, summary

    next_field = _OUTREACH_ADD_FIELDS[step]
    prompt = f"Шаг {step + 1}/{len(_OUTREACH_ADD_FIELDS)}\n\n" + _OUTREACH_ADD_PROMPTS[next_field]
    return False, prompt


def _next_email_step(context, value: str):
    """Advance setup_email state machine. Returns (done, reply_text)."""
    step = context.user_data.get("email_setup_step", 0)
    field = _SETUP_EMAIL_FIELDS[step]
    context.user_data["email_setup_temp"][field] = value.strip()
    step += 1
    context.user_data["email_setup_step"] = step

    if step >= len(_SETUP_EMAIL_FIELDS):
        data = context.user_data.pop("email_setup_temp")
        context.user_data.pop("email_setup_step", None)
        save_email_config(data["login"], data["app_password"])
        return True, f"✅ Gmail настроен: {data['login']}"

    next_field = _SETUP_EMAIL_FIELDS[step]
    prompt = f"Шаг {step + 1}/2\n\n" + _SETUP_EMAIL_PROMPTS[next_field]
    return False, prompt


async def log_telegram_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log exceptions raised inside telegram handlers without changing bot behavior."""
    error = context.error
    exc_info = (type(error), error, error.__traceback__) if error else None
    logger.error("Telegram handler error. update=%r", update, exc_info=exc_info)


def build_application():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("audit", handle_audit))
    application.add_handler(CommandHandler("audit_sites", handle_audit_sites))
    application.add_handler(CommandHandler("learn", handle_learn))
    application.add_handler(CommandHandler("analyze_threads", handle_analyze_threads))
    application.add_handler(CommandHandler("stats", handle_stats))
    application.add_handler(CommandHandler("log", handle_log))
    application.add_handler(CommandHandler("outreach_start", handle_outreach_start))
    application.add_handler(CommandHandler("outreach_add", handle_outreach_add))
    application.add_handler(CommandHandler("outreach_status", handle_outreach_status))
    application.add_handler(CommandHandler("setup_email", handle_setup_email))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_thread_pick, pattern="^thread_pick_"))
    application.add_handler(CallbackQueryHandler(handle_threads_publish, pattern="^threads_publish_"))
    application.add_handler(CallbackQueryHandler(handle_feedback, pattern="^feedback_"))
    application.add_error_handler(log_telegram_error)
    return application


async def run_bot_once():
    """Run Telegram polling and the optional Zvonok web endpoint until stopped or failed."""
    global app
    app = build_application()

    web_app = aiohttp.web.Application()
    web_app.router.add_get("/zvonok", handle_zvonok)
    runner = aiohttp.web.AppRunner(web_app)
    site = None

    try:
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, "0.0.0.0", 8081)
        await site.start()
        print("Zvonok endpoint started on :8080/zvonok")
    except OSError as e:
        logger.error("Zvonok endpoint failed to start", exc_info=True)
        print(f"Zvonok endpoint failed to start: {e}")

    try:
        await app.initialize()
        await app.start()
        if app.updater is None:
            raise RuntimeError("Telegram updater is unavailable; cannot start polling")
        await app.updater.start_polling(drop_pending_updates=True)
        print("Bot polling started")
        await asyncio.Event().wait()
    finally:
        try:
            if app.updater is not None and app.updater.running:
                await app.updater.stop()
        except Exception:
            logger.error("Error stopping Telegram updater", exc_info=True)
        try:
            if app.running:
                await app.stop()
        except Exception:
            logger.error("Error stopping Telegram application", exc_info=True)
        try:
            await app.shutdown()
        except Exception:
            logger.error("Error shutting down Telegram application", exc_info=True)
        try:
            await runner.cleanup()
        except Exception:
            logger.error("Error cleaning up Zvonok web runner", exc_info=True)


async def main():
    reconnect_delay = 5
    max_reconnect_delay = 300

    while True:
        try:
            await run_bot_once()
            reconnect_delay = 5
        except asyncio.CancelledError:
            logger.error("Bot main loop cancelled")
            raise
        except (NetworkError, TimedOut, RetryAfter, aiohttp.ClientError, requests.exceptions.RequestException) as e:
            logger.error("Telegram/network error; reconnecting in %s seconds", reconnect_delay, exc_info=True)
            print(f"Network error: {e}. Reconnecting in {reconnect_delay}s...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
        except Exception as e:
            logger.error("Unhandled bot crash; restarting in %s seconds", reconnect_delay, exc_info=True)
            with open(BOT_ERROR_LOG, "a", encoding="utf-8") as f:
                f.write("\n--- Unhandled bot crash ---\n")
                f.write(traceback.format_exc())
            print(f"Unhandled error: {e}. Restarting in {reconnect_delay}s...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
