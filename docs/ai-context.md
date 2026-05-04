### Статус: 04.05.2026 19:36
```markdown
# Roamaid Second Brain — Системный контекст

Ты AI-агент системы Roamaid Second Brain, предназначенный для роста в соцсетях, управляемый через Telegram бот.

## Что работает
*   **Система:** Автономный AI-агент для роста в соцсетях, управляемый через Telegram бот (`/root/bot.py`).
*   **Скиллы и Команды:** Аудит Instagram аккаунтов (`/root/audit_agent.py`), анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram/сайтов (`/audit_sites`), обучение из YouTube видео (`/learn`). Недавно завершены: анализ вирусных тредов (`/analyze_threads`) и публикация в Threads (`/post_to_threads`). Дополнительные команды: `/stats`, `/log`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, Google Sheets API (ID: `1nqBnh8WCEyb...`), Telegram Bot API, Zvonok.com webhook (на порту 8081).
*   **Память:** 3-слойная архитектура: `/root/brain/memory/` (факты), `/root/brain/daily/` (ежедневные заметки), `CLAUDE.md` (системные правила).
*   **Инфраструктура:** Dashboard задеплоен через PM2/Nginx на `http://2.27.36.182:8080`.
*   **Процессы:** Автоматический Git commit/push в `raomaidbat-alt/roamaid_second_brain`, логирование важных действий в `/root/brain/daily/`.

## Что сломано
*   **OpenClaw gateway:** Использует протокол WebSocket вместо REST API. Отсутствует прямой доступ к AI-провайдерам (нет API-ключей), настроен через ChatGPT Plus OAuth.

## Следующий шаг (приоритет)
1.  **Генерация каруселей (`/root/skills/carousel_generator/`):** Gemini генерирует текст слайдов, Playwright рендерит HTML в PNG (требуется Chromium). Реализовать предпросмотр в Telegram для одобрения хозяином, затем публикацию в Threads (4:5), Instagram (1:1), Stories (9:16).
2.  **Публикация в Threads:** Использование `threads_api` только после одобрения хозяина в Telegram.

## Ключевые файлы и серверы
*   **Файлы:**
    *   `/root/bot.py` (Telegram бот)
    *   `/root/audit_agent.py` (Аудит Instagram)
    *   `/root/skills/` (директория скиллов)
    *   `/root/brain/` (директория памяти)
    *   `/root/roamaid_second_brain/CLAUDE.md` (системный контекст)
    *   `.env` (секреты), `outreach/`, `dashboard/`, `daily_logger.py`, `daily_log.md`
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот, все агенты, Dashboard на :8080)
```

---
*Автосжатие через Gemini*