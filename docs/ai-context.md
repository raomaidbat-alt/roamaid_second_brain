### Статус: 05.05.2026 04:00
```markdown
# Roamaid Second Brain — Системный контекст

Ты AI-агент Roamaid Second Brain, автономный агент для роста в соцсетях, управляемый через Telegram бот.

## Что работает
*   **Ядро и агенты:** Telegram бот (`/root/bot.py`), агент аудита Instagram (`/root/audit_agent.py`).
*   **Скиллы:** Анализ роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram/сайтов (`/audit_website/`). Обучение из YouTube (`/learn`). Недавно завершены: анализ вирусных тредов (`/analyze_threads`) и публикация в Threads (`/post_to_threads`).
*   **Команды бота:** `/audit`, `/audit_sites`, `/stats`, `/log`, `/learn`, `/analyze_threads`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, Google Sheets API (ID: `1nqBnh8WCEyb...` для CRM, аккаунтов, сайтов), Telegram Bot API, zvonok.com webhook.
*   **Память:** 3-слойная архитектура: `/root/brain/memory/` (факты), `/root/brain/daily/` (ежедневные заметки), `/root/roamaid_second_brain/CLAUDE.md` (системные правила).
*   **Инфраструктура:** Dashboard на `http://2.27.36.182:8080`. Автоматический Git commit/push, логирование в `/root/brain/daily/`.

## Что сломано
*   **OpenClaw gateway:** Использует WebSocket вместо REST API. Нет прямого доступа к AI-провайдерам; настроен через ChatGPT Plus OAuth.

## Следующий шаг (приоритет)
1.  **Генерация каруселей (`/root/skills/carousel_generator/`):** Gemini генерирует текст, Playwright рендерит HTML в PNG (требуется Chromium). Реализовать предпросмотр в Telegram для одобрения, затем публикацию в Threads (4:5), Instagram (1:1), Stories (9:16).
2.  **Публикация в Threads:** Использование `threads_api` только после одобрения хозяина в Telegram.

## Ключевые файлы и серверы
*   **Файлы:** `/root/bot.py`, `/root/audit_agent.py`, `/root/skills/` (директория скиллов), `/root/brain/` (директория памяти), `/root/roamaid_second_brain/CLAUDE.md` (системный контекст), `.env` (секреты).
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот, все агенты, Dashboard)
```

---
*Автосжатие через Gemini*