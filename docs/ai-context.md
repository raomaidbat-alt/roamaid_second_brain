### Статус: 05.05.2026 00:00
```markdown
# Roamaid Second Brain — Системный контекст (Сжато)

Ты AI-агент системы Roamaid Second Brain для роста в соцсетях, управляемый через Telegram бот.

## Что работает
*   **Система и Команды:** `/root/bot.py` (Telegram бот), `/root/audit_agent.py` (аудит Instagram). Скиллы: анализ роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram/сайтов (`/audit_sites`), обучение из YouTube (`/learn`). Недавно завершены: анализ вирусных тредов (`/analyze_threads`) и публикация в Threads (`/post_to_threads`). Дополнительные команды: `/stats`, `/log`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, Google Sheets API (ID: `1nqBnh8WCEyb...`), Telegram Bot API, Zvonok.com webhook (порт 8081). Google Sheets используются для Аккаунтов, CRM, Роликов, Активности, Сайтов.
*   **Память:** 3-слойная архитектура: `/root/brain/memory/` (факты), `/root/brain/daily/` (ежедневные заметки), `/root/roamaid_second_brain/CLAUDE.md` (системные правила).
*   **Инфраструктура/Процессы:** Dashboard на `http://2.27.36.182:8080` (PM2/Nginx). Автоматический Git commit/push в `raomaidbat-alt/roamaid_second_brain`, логирование в `/root/brain/daily/`.

## Что сломано
*   **OpenClaw gateway:** Использует WebSocket вместо REST API. Отсутствует прямой доступ к AI-провайдерам (нет API-ключей), настроен через ChatGPT Plus OAuth.

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