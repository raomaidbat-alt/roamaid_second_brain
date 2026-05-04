### Статус: 04.05.2026 19:06
```markdown
**Что работает:**
*   **Roamaid Second Brain:** Автономный AI-агент для роста в соцсетях через Telegram бот (`/root/bot.py`) и Instagram аудит (`/root/audit_agent.py`).
*   **Скиллы:** Анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram/сайтов, обучение из YouTube (`/learn`). **Недавно завершены:** анализ вирусных тредов, публикация в Threads.
*   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [url]`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, Google Sheets API (ID: `1nqBnh8WCEyb...`), Telegram Bot API, Zvonok.com webhook (порт 8081).
*   **Память:** 3-слойная архитектура (`/root/brain/memory/`, `/root/brain/daily/`, `CLAUDE.md`).
*   **Инфраструктура:** Dashboard задеплоен через PM2/Nginx на `http://2.27.36.182:8080`.
*   **Процессы:** Автоматический Git commit/push в `raomaidbat-alt/roamaid_second_brain`, логирование в `/root/brain/daily/`.

**Что сломано:**
*   **OpenClaw gateway:** Использует WebSocket (не REST API). Отсутствует прямой доступ к AI-провайдерам (нет API-ключей), настроен через ChatGPT Plus OAuth.

**Следующий шаг (приоритет):**
1.  **Генерация каруселей (`/root/skills/carousel_generator/`):** Gemini генерирует текст слайдов, Playwright рендерит HTML в PNG (требуется Chromium). Предпросмотр в Telegram для одобрения, затем публикация (Threads 4:5, Instagram 1:1, Stories 9:16).
2.  **Публикация в Threads:** Использование `threads_api` только после одобрения хозяина в Telegram.

**Ключевые файлы и серверы:**
*   **Файлы:**
    *   `/root/bot.py` (Telegram бот)
    *   `/root/audit_agent.py` (Аудит Instagram)
    *   `/root/skills/` (директория скиллов)
    *   `/root/brain/` (директория памяти)
    *   `/root/roamaid_second_brain/CLAUDE.md` (системный контекст)
    *   `.env` (секреты)
    *   `outreach/`, `dashboard/`, `daily_logger.py`, `daily_log.md`
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот, все агенты, Dashboard на :8080)
```

---
*Автосжатие через Gemini*