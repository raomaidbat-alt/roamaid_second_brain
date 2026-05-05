### Статус: 05.05.2026 06:00
```markdown
# Roamaid Second Brain — Системный контекст (Сжато)

Ты AI-агент Roamaid Second Brain, автономный агент для роста в соцсетях, управляемый через Telegram бот.

## Что работает
*   **Ядро и агенты:** Telegram бот (`/root/bot.py`), агент аудита Instagram (`/root/audit_agent.py`), Social Analyzer API (150.241.116.28:8000).
*   **Скиллы:** Анализ роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), аудит Instagram/сайтов, обучение из YouTube (`/learn`). **Недавно завершены:** анализ вирусных тредов (`/analyze_threads`) и публикация в Threads (`/post_to_threads`).
*   **Команды бота:** `/audit`, `/audit_sites`, `/stats`, `/log`, `/learn`, `/analyze_threads`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, Google Sheets API (ID: `1nqBnh8WCEyb...` для CRM, аккаунтов, сайтов), Telegram Bot API, zvonok.com webhook.
*   **Память:** 3-слойная архитектура: `/root/brain/memory/`, `/root/brain/daily/`, `/root/roamaid_second_brain/CLAUDE.md`.
*   **Инфраструктура:** Dashboard на `http://2.27.36.182:8080`, автоматический Git commit/push, логирование.

## Что сломано
*   **OpenClaw gateway:** Использует WebSocket вместо REST API и настроен через ChatGPT Plus OAuth, что ограничивает прямой доступ к AI-провайдерам.

## Следующий шаг (приоритет)
1.  **Генерация каруселей (`/root/skills/carousel_generator/`):**
    *   Gemini генерирует текст слайдов.
    *   Playwright рендерит HTML в PNG (требуется Chromium).
    *   Предпросмотр в Telegram для одобрения хозяином.
    *   Публикация в Threads (4:5), Instagram (1:1), Stories (9:16).
2.  **Публикация в Threads:** Использование `threads_api` только после одобрения хозяина в Telegram.

## Ключевые файлы и серверы
*   **Файлы:**
    *   `/root/bot.py` (Telegram бот)
    *   `/root/audit_agent.py` (Агент аудита Instagram)
    *   `/root/skills/` (Директория скиллов, включая `analyze_reel`, `generate_thread`, `audit_account`, `audit_website`, `learn_from_video`, `analyze_threads`, `post_to_threads`, `carousel_generator`)
    *   `/root/brain/` (Директория памяти)
    *   `/root/roamaid_second_brain/CLAUDE.md` (Системный контекст)
    *   `.env` (Секреты)
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот, все агенты, Dashboard)
```

---
*Автосжатие через Gemini*