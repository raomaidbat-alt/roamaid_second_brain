import os
import re
import datetime

LOG_FILE = "/root/daily_log.md"


def _today() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def _time_now() -> str:
    return datetime.datetime.now().strftime("%H:%M")


def _ensure_today_header():
    today = _today()
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"# Ежедневный журнал бота\n\n## {today}\n")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if f"## {today}" not in content:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n## {today}\n")


def log(message: str):
    _ensure_today_header()
    entry = f"- {_time_now()} {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def log_account_analyzed(nick: str, followers: str = ""):
    suffix = f" ({followers} подписчиков)" if followers else ""
    log(f"Проанализирован аккаунт @{nick}{suffix}")


def log_thread_generated(nick: str, hook_type: str):
    log(f"Сгенерирован тред {hook_type} для @{nick}")


def log_thread_chosen(nick: str, hook_type: str):
    log(f"Выбран тред {hook_type} для @{nick}")


def log_zvonok(phone: str, region: str = ""):
    suffix = f" ({region})" if region else ""
    log(f"Новая заявка со звонка: {phone}{suffix}")


def log_voice_activity(activities: list):
    parts = ", ".join(f"{a['count']} {a['type']}" for a in activities)
    log(f"Голосовое: {parts}")


def log_audit_started(count: int):
    log(f"Запущен аудит {count} аккаунтов")


def log_audit_account(nick: str, variant: str):
    log(f"Аудит завершён @{nick} (вариант {variant})")


def log_site_analyzed(url: str, design: int = None, conv: int = None):
    scores = ""
    if design is not None:
        scores = f" (дизайн {design}/10, конверсия {conv}/10)"
    log(f"Аудит сайта: {url}{scores}")


def get_today_log() -> str:
    today = _today()
    if not os.path.exists(LOG_FILE):
        return ""
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    idx = content.find(f"## {today}")
    if idx == -1:
        return ""
    block = content[idx:]
    next_section = block.find("\n## ", 4)
    if next_section != -1:
        block = block[:next_section]
    return block


def get_today_stats() -> dict:
    block = get_today_log()
    return {
        "accounts": len(re.findall(r"Проанализирован аккаунт", block)),
        "threads": len(re.findall(r"Сгенерирован тред", block)),
        "leads": len(re.findall(r"Новая заявка", block)),
        "audits": len(re.findall(r"Аудит завершён", block)),
        "sites": len(re.findall(r"Аудит сайта", block)),
        "voice": re.findall(r"Голосовое: (.+)", block),
    }


def get_last_7_days_summary() -> str:
    if not os.path.exists(LOG_FILE):
        return "Лог пустой."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    days = re.findall(r"## (\d{4}-\d{2}-\d{2})\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not days:
        return "Лог пустой."
    lines = []
    for date, block in days[-7:]:
        accounts = len(re.findall(r"Проанализирован аккаунт", block))
        threads = len(re.findall(r"Сгенерирован тред", block))
        leads = len(re.findall(r"Новая заявка", block))
        audits = len(re.findall(r"Аудит завершён", block))
        sites = len(re.findall(r"Аудит сайта", block))
        parts = []
        if accounts:
            parts.append(f"аккаунтов: {accounts}")
        if threads:
            parts.append(f"тредов: {threads}")
        if leads:
            parts.append(f"заявок: {leads}")
        if audits:
            parts.append(f"аудитов: {audits}")
        if sites:
            parts.append(f"сайтов: {sites}")
        lines.append(f"{date}: {', '.join(parts) or 'нет данных'}")
    return "\n".join(lines)
