import os
import json
import smtplib
import asyncio
import logging
import random
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import anthropic as _anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

CONTACTS_FILE = "/root/outreach/contacts.json"
LOG_FILE = "/root/outreach/outreach.log"
EMAIL_CONFIG_FILE = "/root/outreach/email_config.json"

outreach_logger = logging.getLogger("outreach")
outreach_logger.setLevel(logging.INFO)
if not outreach_logger.handlers:
    _fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    outreach_logger.addHandler(_fh)


# ── Storage helpers ────────────────────────────────────────────────────────────

def load_contacts() -> list:
    if not os.path.exists(CONTACTS_FILE):
        return []
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contacts(contacts: list) -> None:
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)


def add_contact(contact: dict) -> None:
    contacts = load_contacts()
    contacts.append({
        "name": contact.get("name", ""),
        "telegram": contact.get("telegram", ""),
        "email": contact.get("email", ""),
        "audit_type": contact.get("audit_type", "funnel"),
        "audit_data": contact.get("audit_data", ""),
        "status": "pending",
        "created_at": datetime.datetime.utcnow().isoformat(),
    })
    save_contacts(contacts)


def load_email_config():
    if not os.path.exists(EMAIL_CONFIG_FILE):
        return None
    with open(EMAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_email_config(login: str, app_password: str) -> None:
    with open(EMAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"login": login, "app_password": app_password}, f)


def get_stats() -> dict:
    contacts = load_contacts()
    stats = {"total": len(contacts), "pending": 0, "sent": 0, "failed": 0}
    for c in contacts:
        status = c.get("status", "pending")
        if status in stats:
            stats[status] += 1
    return stats


# ── Message generation ─────────────────────────────────────────────────────────

def generate_message(contact: dict) -> str:
    name = contact.get("name", "")
    audit_type = contact.get("audit_type", "funnel")
    audit_data = contact.get("audit_data", "")
    channel = "Telegram-сообщение" if audit_type == "funnel" else "email"

    prompt = (
        f"Ты эксперт по маркетингу. Напиши персональное {channel} для потенциального клиента.\n\n"
        f"Имя: {name}\n"
        f"Тип аудита: {'воронки продаж' if audit_type == 'funnel' else 'сайта'}\n"
        f"Данные аудита: {audit_data}\n\n"
        "Требования:\n"
        "- Персональное обращение по имени\n"
        "- Упомяни 1-2 конкретные проблемы из данных аудита\n"
        "- Предложи бесплатный аудит как следующий шаг\n"
        "- Призыв к действию: ответить на сообщение\n"
        "- Длина: 4-6 предложений\n"
        "- Тон: дружелюбный, профессиональный, без давления\n"
        "- Только чистый текст, без markdown и HTML"
    )

    if _ANTHROPIC_AVAILABLE and os.environ.get("ANTHROPIC_API_KEY"):
        client = _anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    # Fallback: basic template without AI
    outreach_logger.warning("Anthropic unavailable — using template message")
    if audit_type == "funnel":
        return (
            f"Привет, {name}! Изучил твою воронку и нашёл несколько точек роста. "
            f"{audit_data[:200] if audit_data else ''} "
            "Готов сделать бесплатный аудит и показать конкретные цифры. "
            "Напиши в ответ — договоримся о 30-минутном разборе."
        )
    return (
        f"Привет, {name}! Проанализировал твой сайт и вижу зоны для улучшения конверсии. "
        f"{audit_data[:200] if audit_data else ''} "
        "Предлагаю бесплатный аудит с конкретными рекомендациями. "
        "Ответь на это письмо — пришлю детальный разбор."
    )


# ── Sending ────────────────────────────────────────────────────────────────────

async def send_telegram_message(bot, telegram: str, message: str) -> bool:
    try:
        # get_chat works for usernames the bot has interacted with
        chat = await bot.get_chat(telegram)
        await bot.send_message(chat_id=chat.id, text=message)
        return True
    except Exception as e:
        outreach_logger.error(f"Telegram send error → {telegram}: {e}")
        return False


def send_email(to_email: str, name: str, message: str, email_config: dict) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = email_config["login"]
        msg["To"] = to_email
        msg["Subject"] = f"Персональный аудит для {name}"
        msg.attach(MIMEText(message, "plain", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(email_config["login"], email_config["app_password"])
            server.send_message(msg)
        return True
    except Exception as e:
        outreach_logger.error(f"Email send error → {to_email}: {e}")
        return False


# ── Main outreach runner ───────────────────────────────────────────────────────

async def run_outreach(bot) -> dict:
    contacts = load_contacts()
    email_config = load_email_config()

    pending = [c for c in contacts if c.get("status") == "pending"]
    stats = {"sent": 0, "failed": 0, "skipped": len(contacts) - len(pending)}

    outreach_logger.info(f"Outreach started: {len(pending)} pending contacts")

    pending_indices = [i for i, c in enumerate(contacts) if c.get("status") == "pending"]

    for seq, idx in enumerate(pending_indices):
        contact = contacts[idx]
        name = contact.get("name", "Unknown")
        audit_type = contact.get("audit_type", "")

        try:
            message = generate_message(contact)
            outreach_logger.info(f"Message generated for {name} ({audit_type})")
        except Exception as e:
            outreach_logger.error(f"Message generation failed for {name}: {e}")
            contacts[idx]["status"] = "failed"
            stats["failed"] += 1
            save_contacts(contacts)
            continue

        success = False

        if audit_type == "funnel":
            telegram = contact.get("telegram", "").strip()
            if not telegram:
                outreach_logger.warning(f"No Telegram username for {name}")
                contacts[idx]["status"] = "failed"
                stats["failed"] += 1
                save_contacts(contacts)
                continue
            success = await send_telegram_message(bot, telegram, message)

        elif audit_type == "site":
            email = contact.get("email", "").strip()
            if not email:
                outreach_logger.warning(f"No email for {name}")
                contacts[idx]["status"] = "failed"
                stats["failed"] += 1
                save_contacts(contacts)
                continue
            if not email_config:
                outreach_logger.error("Email config not configured")
                contacts[idx]["status"] = "failed"
                stats["failed"] += 1
                save_contacts(contacts)
                continue
            success = send_email(email, name, message, email_config)

        else:
            outreach_logger.warning(f"Unknown audit_type '{audit_type}' for {name}")
            contacts[idx]["status"] = "failed"
            stats["failed"] += 1
            save_contacts(contacts)
            continue

        contacts[idx]["status"] = "sent" if success else "failed"
        contacts[idx]["sent_at"] = datetime.datetime.utcnow().isoformat()
        if success:
            stats["sent"] += 1
            outreach_logger.info(f"Sent to {name} ({'Telegram' if audit_type == 'funnel' else 'Email'})")
        else:
            stats["failed"] += 1

        save_contacts(contacts)

        # Delay between sends (skip after the last one)
        if seq < len(pending_indices) - 1:
            delay = random.randint(30, 60)
            outreach_logger.info(f"Waiting {delay}s before next send...")
            await asyncio.sleep(delay)

    outreach_logger.info(
        f"Outreach done: sent={stats['sent']}, failed={stats['failed']}, skipped={stats['skipped']}"
    )
    return stats
