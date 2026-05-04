import os
import re
import asyncio
import datetime
import json
import time
import random
import requests
import gspread
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials

GOOGLE_CREDS_FILE = "/root/google_credentials.json"
SPREADSHEET_ID = "1nqBnh8WcEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo"
ANALYZER_URL = "http://150.241.116.28:8000/analyze"
SERVICE_ACCOUNT_EMAIL = "bosssss@rominb-assistant-495114.iam.gserviceaccount.com"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CRM_HEADERS = [
    "Дата", "Ник", "Ссылка на таблицу аудита",
    "Персональное сообщение", "Вариант (А/Б/В)",
    "Ответил (да/нет)", "Дата ответа",
    "Статус", "Оценка", "Комментарий",
]

SITES_HEADERS = [
    "Дата", "Ник Instagram", "Ссылка на сайт", "Заголовок сайта",
    "CTA", "Воронка", "Дизайн (1-10)", "Конверсионность (1-10)",
    "Что не так (топ 3)", "Потенциал заработка",
    "Сообщение А", "Сообщение Б", "Сообщение В", "Статус",
]

SITES_LIST_HEADERS = ["URL сайта"]

AUDIT_STAGES = [
    "1. Продуктовая линейка",
    "2. Упаковка профиля IG",
    "3. Ссылка в профиле",
    "4. Reels",
    "5. TG канал",
    "6. TG бот",
    "7. Монетизация",
]

AUDIT_COLUMNS = [
    "Этап",
    "Наблюдение (как сейчас)",
    "Почему это просаживает продажи",
    "Как должно быть",
    "Конкретные правки/задачи",
    "KPI",
]

AB_VARIANTS = ["А", "Б", "В"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gc():
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def _gemini(prompt: str) -> str:
    api_key = os.environ["GEMINI_API_KEY"]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/gemini-2.5-flash:generateContent?key={api_key}"
    )
    last_call = getattr(_gemini, "_last_call", 0.0)
    elapsed = time.time() - last_call
    if elapsed < 10:
        time.sleep(10 - elapsed)
    _gemini._last_call = time.time()

    for attempt in range(3):
        resp = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=90,
        )
        if resp.status_code == 429:
            time.sleep(30)
            continue
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    resp.raise_for_status()


def _parse_json_from_gemini(raw: str) -> dict:
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except Exception:
                continue
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _worksheet(name: str, headers: list):
    ss = _gc().open_by_key(SPREADSHEET_ID)
    try:
        ws = ss.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=name, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws


# ── A/B статистика ────────────────────────────────────────────────────────────

def _get_ab_stats() -> dict:
    stats = {v: {"sent": 0, "replied": 0} for v in AB_VARIANTS}
    try:
        gc = _gc()
        ss = gc.open_by_key(SPREADSHEET_ID)
        ws = ss.worksheet("CRM")
        rows = ws.get_all_values()
        if not rows:
            return stats
        headers = rows[0]
        try:
            var_idx = headers.index("Вариант (А/Б/В)")
            ans_idx = headers.index("Ответил (да/нет)")
        except ValueError:
            return stats
        for row in rows[1:]:
            if len(row) <= var_idx:
                continue
            variant = row[var_idx].strip().upper()
            if variant not in AB_VARIANTS:
                continue
            stats[variant]["sent"] += 1
            answered = row[ans_idx].strip().lower() if len(row) > ans_idx else ""
            if answered in ("да", "yes", "+", "1"):
                stats[variant]["replied"] += 1
    except Exception:
        pass
    return stats


def _pick_variant() -> str:
    stats = _get_ab_stats()
    best = None
    best_rate = 0.0
    for v, s in stats.items():
        if s["sent"] == 0:
            continue
        rate = s["replied"] / s["sent"]
        if s["replied"] >= 5 and rate > best_rate:
            best_rate = rate
            best = v
    if best:
        others = [v for v in AB_VARIANTS if v != best]
        weights = {best: 0.60, others[0]: 0.20, others[1]: 0.20}
        return random.choices(AB_VARIANTS, weights=[weights[v] for v in AB_VARIANTS])[0]
    return random.choice(AB_VARIANTS)


# ── Website analysis ──────────────────────────────────────────────────────────

def _fetch_site_content(url: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    meta_desc = ""
    for tag in soup.find_all("meta"):
        if tag.get("name", "").lower() == "description":
            meta_desc = tag.get("content", "")
            break

    h1 = " | ".join(t.get_text(strip=True) for t in soup.find_all("h1"))[:300]
    h2s = " | ".join(t.get_text(strip=True) for t in soup.find_all("h2"))[:300]

    cta_texts = []
    for tag in soup.find_all(["button", "a"]):
        text = tag.get_text(strip=True)
        cls = " ".join(tag.get("class", []))
        href = tag.get("href", "")
        if any(kw in text.lower() for kw in ["купить", "заказать", "записаться", "получить", "попробовать",
                                               "оставить", "начать", "узнать", "подписаться", "скачать",
                                               "buy", "get", "start", "sign", "join", "contact"]):
            cta_texts.append(text)
        elif any(kw in cls.lower() for kw in ["btn", "button", "cta"]):
            if text:
                cta_texts.append(text)
    ctas = " | ".join(cta_texts[:10])

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = re.sub(r'\s+', ' ', soup.get_text(separator=" ")).strip()[:4000]

    return {
        "url": url,
        "title": title,
        "meta_desc": meta_desc,
        "h1": h1,
        "h2s": h2s,
        "ctas": ctas,
        "body_text": body_text,
    }


def _analyze_website(url: str, nick: str = "") -> dict:
    try:
        content = _fetch_site_content(url)
    except Exception as e:
        return {"error": str(e), "url": url}

    prompt = f"""Ты эксперт по конверсии лендингов и контент-маркетингу.
Проанализируй сайт по данным ниже. Все оценки конкретные, с примерами из текста.

URL: {content['url']}
Заголовок: {content['title']}
H1: {content['h1']}
H2: {content['h2s']}
Мета-описание: {content['meta_desc']}
CTA кнопки: {content['ctas'] or '(не найдены)'}
Текст страницы: {content['body_text']}

Сделай анализ по 7 разделам. ВАЖНО: сообщения А/Б/В пиши строго на ВЫ, никакого "ты".
Плейсхолдер {{ссылка на таблицу}} оставь как есть — не заменяй его.

Верни строго JSON (без markdown-обёрток):
{{
  "title": "заголовок сайта",
  "cta": "главный CTA или нет",
  "funnel": "описание воронки 2-3 предложения",
  "design_score": 7,
  "conversion_score": 5,
  "problems": ["проблема 1 конкретно", "проблема 2 конкретно", "проблема 3 конкретно"],
  "revenue_potential": "потенциал заработка 1-2 предложения с цифрами",
  "sections": {{
    "first_screen": "анализ первого экрана — оффер, заголовок, CTA",
    "funnel": "анализ воронки — куда ведёт, логика шагов",
    "social_proof": "социальные доказательства — отзывы, кейсы, цифры",
    "product_line": "продуктовая линейка — что продаётся, цены, офферы",
    "mobile": "мобильная версия — признаки адаптивности",
    "speed": "скорость — признаки медленной загрузки, тяжёлые блоки",
    "conversion": "итоговый анализ конверсионности"
  }},
  "msg_a": "Вариант А (ЦИФРЫ): {{имя}}, доброго дня! случайно попал на Ваш сайт — [конкретные цифры/факты]. Заметил что при таком трафике Вы могли бы зарабатывать в 2-3 раза больше... [3 наблюдения]. вот аудит → {{ссылка на таблицу}} посмотрите если интересно)",
  "msg_b": "Вариант Б (БОЛЬ): {{имя}}, доброго дня! попал на Ваш сайт — [конкретная боль что мешает конверсии]. Вижу что продукт сильный, но есть пара вещей которые тормозят продажи... [3 боли]. вот аудит → {{ссылка на таблицу}}",
  "msg_c": "Вариант В (КОМПЛИМЕНТ): {{имя}}, доброго дня! попал на Ваш сайт — редко встречаю [что хорошо] в нише [ниша]. При этом заметил кое-что в воронке что можно докрутить... [3 наблюдения]. вот аудит → {{ссылка на таблицу}}"
}}"""

    raw = _gemini(prompt)
    data = _parse_json_from_gemini(raw)

    if not data:
        data = {
            "title": content["title"],
            "cta": content["ctas"] or "не найден",
            "funnel": "не удалось определить",
            "design_score": 0,
            "conversion_score": 0,
            "problems": ["ошибка парсинга ответа Gemini"],
            "revenue_potential": "—",
            "sections": {},
            "msg_a": "", "msg_b": "", "msg_c": "",
        }

    data["url"] = url
    data["nick"] = nick
    return data


def _append_to_sites(nick: str, url: str, data: dict, sheet_url: str = ""):
    ws = _worksheet("Сайты", SITES_HEADERS)
    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    problems = " | ".join(data.get("problems", []))
    msg_a = data.get("msg_a", "").replace("{ссылка на таблицу}", sheet_url)
    msg_b = data.get("msg_b", "").replace("{ссылка на таблицу}", sheet_url)
    msg_c = data.get("msg_c", "").replace("{ссылка на таблицу}", sheet_url)
    ws.append_row([
        date_str,
        f"@{nick}" if nick else "",
        url,
        data.get("title", ""),
        data.get("cta", ""),
        data.get("funnel", ""),
        data.get("design_score", ""),
        data.get("conversion_score", ""),
        problems,
        data.get("revenue_potential", ""),
        msg_a,
        msg_b,
        msg_c,
        "",  # Статус — заполняется вручную
    ])


def _read_sites_list() -> list:
    try:
        ws = _worksheet("Сайты-список", SITES_LIST_HEADERS)
        values = ws.col_values(1)
        return [v.strip() for v in values if v.strip() and v.strip().lower() != "url сайта"]
    except Exception:
        return []


# ── Instagram account analysis ────────────────────────────────────────────────

def _analyze_account(nick: str) -> dict:
    """Fetch factual Instagram profile data from the analyzer /profile endpoint.

    Important: /analyze is for individual media URLs; profile URLs through yt-dlp
    can return “No info returned”. For audits we need bio, links, recent posts/Reels,
    counts and captions, so use /profile.
    """
    try:
        res = requests.post(ANALYZER_URL.replace("/analyze", "/profile"), json={"username": nick}, timeout=120)
        res.raise_for_status()
        data = res.json()
        data["status"] = data.get("status", "ok")
        return data
    except Exception as e:
        return {"status": "error", "error": str(e), "username": nick}


def _extract_bio_url(analyzer_data: dict) -> str:
    for link in analyzer_data.get("bio_links", []) or []:
        url = link.get("url", "") if isinstance(link, dict) else ""
        if url.startswith("http"):
            return url
    external = analyzer_data.get("external_url", "") or ""
    if external.startswith("http"):
        return external
    text = " ".join([analyzer_data.get("bio", "") or ""] + [p.get("caption", "") for p in analyzer_data.get("posts", []) or []])
    urls = re.findall(r'https?://[^\s\)\]\>]+', text)
    return urls[0] if urls else ""


def _generate_audit(nick: str, analyzer_data: dict) -> dict:
    data_str = json.dumps(analyzer_data, ensure_ascii=False)[:3000] if analyzer_data else "(данные недоступны)"

    stage_schema = json.dumps([
        {
            "stage": s,
            "observation": "наблюдение как сейчас — конкретно",
            "why_drops_sales": "почему это просаживает продажи — конкретно",
            "how_it_should_be": "как должно быть — конкретно",
            "tasks": "конкретные правки/задачи с цифрами",
            "kpi": "измеримый KPI",
        }
        for s in AUDIT_STAGES
    ], ensure_ascii=False, indent=2)

    prompt = f"""Ты эксперт по контент-маркетингу и монетизации Instagram.
Проанализируй аккаунт @{nick} на основе данных: {data_str}

Заполни аудит по каждому из 7 этапов. Будь конкретным: реальные цифры, конкретные наблюдения.

ВАЖНО: все три сообщения пиши строго на ВЫ/Вам/Ваш. Оставь плейсхолдер {{ссылка на таблицу}} как есть.

Этапы:
1. Продуктовая линейка — оффер, для кого, линейка продуктов, цены
2. Упаковка профиля IG — шапка, CTA, понятно ли куда идти
3. Ссылка в профиле — одна/много, есть ли TG бот
4. Reels — просмотры, форматы, CTA в конце роликов
5. TG канал — есть ли, подписчики, активность, воронка
6. TG бот — автоматизация продаж
7. Монетизация — текущий доход, потенциал в рублях

Вариант А (ЦИФРЫ):
{nick}, доброго дня! случайно попал на Ваш профиль — [X подписчиков, Y просмотров].
Заметил что при таких цифрах Вы могли бы зарабатывать в 2-3 раза больше...
[наблюдение 1], [наблюдение 2], [наблюдение 3]
работал с Абдурап Мурзаев — 10 рилсов, +415к | кейс (https://drive.google.com/file/d/1r1DJQWU5G3djxgGLcIP-9jj-JfawQcNV/view)
вот аудит → {{ссылка на таблицу}} посмотрите если интересно)

Вариант Б (БОЛЬ):
{nick}, доброго дня! случайно попал на Ваш ролик про [тема] — смотрел не отрываясь.
Вижу что контент у Вас сильный, но есть пара вещей которые тормозят монетизацию...
[боль 1], [боль 2], [боль 3] [кейс] вот аудит → {{ссылка на таблицу}}

Вариант В (КОМПЛИМЕНТ):
{nick}, доброго дня! случайно попал на Ваш профиль — редко встречаю такой контент в нише [ниша].
При этом заметил кое-что в воронке что можно докрутить...
[наблюдение 1], [наблюдение 2], [наблюдение 3] [кейс] вот аудит → {{ссылка на таблицу}}

Верни строго JSON (без markdown):
{{
  "stages": {stage_schema},
  "msg_a": "вариант А полностью",
  "msg_b": "вариант Б полностью",
  "msg_c": "вариант В полностью"
}}"""

    raw = _gemini(prompt)
    data = _parse_json_from_gemini(raw)

    if "stages" not in data or not isinstance(data["stages"], list):
        data["stages"] = []
    existing = {s.get("stage", ""): s for s in data["stages"]}
    data["stages"] = []
    for stage_name in AUDIT_STAGES:
        s = existing.get(stage_name, {})
        data["stages"].append({
            "stage": stage_name,
            "observation": s.get("observation", "—"),
            "why_drops_sales": s.get("why_drops_sales", "—"),
            "how_it_should_be": s.get("how_it_should_be", "—"),
            "tasks": s.get("tasks", "—"),
            "kpi": s.get("kpi", "—"),
        })

    fallback = (
        f"{nick}, доброго дня!\n"
        "случайно попал на Ваш профиль — вижу хороший потенциал.\n"
        "работал с Абдурап Мурзаев — 10 рилсов, +415к | "
        "кейс (https://drive.google.com/file/d/1r1DJQWU5G3djxgGLcIP-9jj-JfawQcNV/view)\n\n"
        "вот аудит → {ссылка на таблицу}\nпосмотрите если интересно)"
    )
    for key in ("msg_a", "msg_b", "msg_c"):
        if not data.get(key):
            data[key] = fallback

    return data


def _create_audit_spreadsheet(nick: str, audit_data: dict) -> str:
    gc = _gc()
    ss = gc.open_by_key(SPREADSHEET_ID)

    sheet_title = f"Аудит - {nick}"[:50]
    try:
        ws = ss.worksheet(sheet_title)
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=sheet_title, rows=100, cols=6)

    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    ncols = len(AUDIT_COLUMNS)
    empty_row = [""] * ncols

    rows = [
        [f"Аудит аккаунта @{nick}"] + [""] * (ncols - 1),
        [f"Дата: {date_str}"] + [""] * (ncols - 1),
        empty_row,
        AUDIT_COLUMNS,
    ]
    for stage in audit_data.get("stages", []):
        rows.append([
            stage.get("stage", ""),
            stage.get("observation", "—"),
            stage.get("why_drops_sales", "—"),
            stage.get("how_it_should_be", "—"),
            stage.get("tasks", "—"),
            stage.get("kpi", "—"),
        ])

    ws.update("A1", rows)

    col_last = chr(ord("A") + ncols - 1)
    ws.format(f"A1:{col_last}1", {"textFormat": {"bold": True, "fontSize": 14}})
    ws.format(f"A4:{col_last}4", {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    })
    data_start_row = 5
    for i in range(len(AUDIT_STAGES)):
        r = data_start_row + i
        ws.format(f"A{r}:A{r}", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 0.98},
        })

    return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={ws.id}"


def _append_to_crm(nick: str, sheet_url: str, personal_message: str, variant: str):
    gc = _gc()
    ss = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = ss.worksheet("CRM")
        existing_headers = ws.row_values(1)
        if existing_headers != CRM_HEADERS:
            ws.delete_rows(1)
            ws.insert_row(CRM_HEADERS, 1)
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title="CRM", rows=1000, cols=len(CRM_HEADERS))
        ws.append_row(CRM_HEADERS)

    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    ws.append_row([date_str, f"@{nick}", sheet_url, personal_message, variant, "", "", "", "", ""])


def _read_accounts_from_sheets() -> list:
    gc = _gc()
    ss = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = ss.worksheet("Аккаунты")
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title="Аккаунты", rows=1000, cols=1)
        ws.update("A1", [["Ник"]])
        return []
    values = ws.col_values(1)
    return [v.strip().lstrip("@") for v in values if v.strip() and v.strip().lower() != "ник"]


# ── Main entry points ─────────────────────────────────────────────────────────

async def run_audit(bot, chat_id: int):
    loop = asyncio.get_event_loop()

    try:
        accounts = await loop.run_in_executor(None, _read_accounts_from_sheets)
    except Exception as e:
        await bot.send_message(chat_id, f"Не могу прочитать Google Sheets: {e}")
        return

    total = len(accounts)
    if not total:
        await bot.send_message(chat_id, "Список аккаунтов пустой.")
        return

    await bot.send_message(chat_id, f"Начинаю аудит {total} аккаунтов...")

    results = []
    batch = []

    for i, nick in enumerate(accounts, 1):
        try:
            await bot.send_message(chat_id, f"[{i}/{total}] Обрабатываю @{nick}...")

            analyzer_data = await loop.run_in_executor(None, _analyze_account, nick)
            audit_data = await loop.run_in_executor(None, _generate_audit, nick, analyzer_data)

            msg_a = audit_data.pop("msg_a", "")
            msg_b = audit_data.pop("msg_b", "")
            msg_c = audit_data.pop("msg_c", "")
            messages = {"А": msg_a, "Б": msg_b, "В": msg_c}

            sheet_url = await loop.run_in_executor(None, _create_audit_spreadsheet, nick, audit_data)

            variant = await loop.run_in_executor(None, _pick_variant)
            chosen_msg = messages[variant].replace("{ссылка на таблицу}", sheet_url)

            await loop.run_in_executor(None, _append_to_crm, nick, sheet_url, chosen_msg, variant)

            # Проверяем есть ли сайт в bio
            bio_url = _extract_bio_url(analyzer_data)
            if bio_url:
                try:
                    await bot.send_message(chat_id, f"  Нашёл сайт в bio @{nick}: {bio_url} — анализирую...")
                    site_data = await loop.run_in_executor(None, _analyze_website, bio_url, nick)
                    if "error" not in site_data:
                        await loop.run_in_executor(None, _append_to_sites, nick, bio_url, site_data, sheet_url)
                        await bot.send_message(
                            chat_id,
                            f"  Сайт @{nick} записан в лист Сайты "
                            f"(дизайн: {site_data.get('design_score', '?')}/10, "
                            f"конверсия: {site_data.get('conversion_score', '?')}/10)"
                        )
                except Exception as e:
                    await bot.send_message(chat_id, f"  Ошибка анализа сайта @{nick}: {e}")

            results.append((nick, sheet_url, variant))
            batch.append((nick, sheet_url, variant))

        except Exception as e:
            results.append((nick, None, "—"))
            batch.append((nick, None, "—"))
            await bot.send_message(chat_id, f"Ошибка для @{nick}: {e}")

        if i % 5 == 0:
            lines = [f"Обработано {i}/{total}"]
            for n, url, var in batch[-5:]:
                lines.append(f"— @{n} [{var}]: {url or 'ошибка'}")
            await bot.send_message(chat_id, "\n".join(lines))
            batch = []

    success = [(n, u, v) for n, u, v in results if u]
    failed = [n for n, u, v in results if not u]

    lines = [f"Аудит завершён! Успешно: {len(success)}/{total}\n"]
    for nick, url, var in success:
        lines.append(f"— @{nick} [{var}]: {url}")
    if failed:
        lines.append(f"\nОшибки ({len(failed)}): {', '.join('@' + n for n in failed)}")

    text = "\n".join(lines)
    for chunk in range(0, len(text), 4000):
        await bot.send_message(chat_id, text[chunk:chunk + 4000])


async def run_audit_sites(bot, chat_id: int):
    loop = asyncio.get_event_loop()

    try:
        urls = await loop.run_in_executor(None, _read_sites_list)
    except Exception as e:
        await bot.send_message(chat_id, f"Не могу прочитать лист Сайты-список: {e}")
        return

    total = len(urls)
    if not total:
        await bot.send_message(
            chat_id,
            "Лист Сайты-список пустой.\n"
            "Добавь URL в колонку A листа Сайты-список и попробуй снова."
        )
        return

    await bot.send_message(chat_id, f"Анализирую {total} сайтов...")

    results = []
    for i, url in enumerate(urls, 1):
        try:
            await bot.send_message(chat_id, f"[{i}/{total}] {url}")
            site_data = await loop.run_in_executor(None, _analyze_website, url, "")
            if "error" in site_data:
                raise Exception(site_data["error"])
            await loop.run_in_executor(None, _append_to_sites, "", url, site_data, "")
            results.append((url, True, site_data))
        except Exception as e:
            results.append((url, False, {"error": str(e)}))
            await bot.send_message(chat_id, f"  Ошибка: {e}")

        # Промежуточный отчёт каждые 3 сайта
        if i % 3 == 0:
            batch = results[max(0, i - 3):i]
            lines = [f"Промежуточный отчёт [{i}/{total}]:"]
            for u, ok, d in batch:
                if ok:
                    lines.append(
                        f"— {u}\n"
                        f"  Дизайн: {d.get('design_score', '?')}/10  "
                        f"Конверсия: {d.get('conversion_score', '?')}/10\n"
                        f"  Проблемы: {'; '.join(d.get('problems', []))}"
                    )
                else:
                    lines.append(f"— {u}: ошибка — {d.get('error', '')}")
            await bot.send_message(chat_id, "\n".join(lines)[:4000])

    ok_count = sum(1 for _, ok, _ in results if ok)
    fail_count = total - ok_count
    lines = [f"Готово! Успешно: {ok_count}/{total}"]
    if fail_count:
        lines.append(f"Ошибки ({fail_count}):")
        for u, ok, d in results:
            if not ok:
                lines.append(f"— {u}: {d.get('error', '')}")
    lines.append(f"\nРезультаты в Google Sheets → лист Сайты")
    await bot.send_message(chat_id, "\n".join(lines)[:4000])


async def get_ab_stats_text() -> str:
    stats = _get_ab_stats()
    labels = {"А": "А (цифры)", "Б": "Б (боль)", "В": "В (комплимент)"}
    lines = ["Статистика сообщений:"]
    best_var, best_rate = None, -1.0
    for var in AB_VARIANTS:
        s = stats[var]
        sent, replied = s["sent"], s["replied"]
        rate = round(replied / sent * 100) if sent > 0 else 0
        lines.append(f"Вариант {labels[var]}: отправлено {sent}, ответили {replied} ({rate}%)")
        if sent > 0 and rate > best_rate:
            best_rate, best_var = rate, var
    if best_var and stats[best_var]["sent"] > 0:
        lines.append(f"\nЛучший вариант: {labels[best_var]}")
    else:
        lines.append("\nПока недостаточно данных")
    return "\n".join(lines)
