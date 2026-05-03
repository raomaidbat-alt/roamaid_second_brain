# 🧠 Roamaid Second Brain

> AI-агент для автономного роста в соцсетях. Находит клиентов, анализирует вирусный контент, генерирует карусели и треды, публикует с твоего одобрения.

## Что умеет

- 🔍 **Hunter** — ищет клиентов в Instagram, делает аудит, пишет персональные сообщения
- 🎬 **Analyzer** — разбирает почему ролик/тред залетел (крючок, психология, структура)
- ✍️ **Creator** — генерирует треды и карусели, публикует в Threads с одобрения
- 🎓 **Learning** — кидаешь видео → бот извлекает скиллы и обучается

## Стек

- **LLM:** Gemini 2.0 Flash
- **Интерфейс:** Telegram Bot
- **Соцсети:** Instagram (instagrapi), Threads, YouTube (yt-dlp)
- **Транскрипция:** Whisper
- **Память:** markdown notes + CLAUDE.md
- **CRM:** Google Sheets

## Архитектура

## Быстрый старт

```bash
git clone https://github.com/raomaidbat-alt/roamaid_second_brain
cd roamaid_second_brain
cp config/.env.example config/.env
# Заполни .env своими ключами
pip install -r requirements.txt
python bot.py
```

## Скиллы

| Скилл | Описание |
|-------|----------|
| analyze_reel | Анализ YouTube/Instagram роликов |
| analyze_threads | Анализ вирусных тредов |
| generate_thread | Генерация тредов ПАРАДОКС/ЦИФРЫ/БОЛЬ |
| audit_account | Полный аудит Instagram аккаунта |
| audit_website | Аудит сайта + сообщения |
| learn_from_video | Обучение из YouTube видео |
| carousel_generator | Генерация каруселей → публикация |

## Команды бота

| Команда | Действие |
|---------|----------|
| /audit @username | Аудит Instagram аккаунта |
| /audit_sites | Аудит сайтов из таблицы |
| /learn [youtube url] | Обучиться из видео |
| /stats | A/B статистика |
| /log | Журнал активности |

## Лицензия

MIT
