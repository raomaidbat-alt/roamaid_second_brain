### Статус: 04.05.2026 18:29
Вот сжатый системный контекст:

**Что работает:**
*   **Ядро системы:** AI-агент Roamaid Second Brain (для роста в соцсетях через Telegram). `/root/bot.py` (Telegram бот), `/root/audit_agent.py` (аудит Instagram).
*   **Скиллы:** Анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram, аудит сайтов, обучение из YouTube видео (`/learn`).
*   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [youtube url]`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook (порт 8081), Google Sheets API, Telegram Bot API.
*   **Google Sheets:** ID `1nqBnh8WcEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo` (Аккаунты, CRM, Ролики, Активность, Сайты, Сайты-список).
*   **Память:** 3-слойная архитектура (`/root/brain/memory/`, `/root/brain/daily/`, `CLAUDE.md`).
*   **Недавно завершено:** Анализ вирусных тредов (`/root/skills/analyze_threads/`) с адаптированным контентом и кнопкой публикации; публикация в Threads (`/root/skills/post_to_threads/`).
*   **Инфраструктура:** Dashboard развернут через PM2/Nginx на `http://2.27.36.182:8080`.
*   **Процесс:** Git commit + push в `raomaidbat-alt/roamaid_second_brain`, логирование в `/root/brain/daily/`.

**Что сломано:**
*   **OpenClaw gateway:** Использует WebSocket (не REST API). Отсутствует прямой доступ к AI-провайдерам (нет API-ключей), настроен через ChatGPT Plus OAuth.

**Следующий шаг (приоритет по порядку):**
1.  **Генерация каруселей (`/root/skills/carousel_generator/`):** Gemini генерирует текст, Playwright (требуется Chromium) рендерит HTML → PNG. Предпросмотр в Telegram для одобрения, затем публикация (Threads 4:5, Instagram 1:1, Stories 9:16).
2.  **Публикация в Threads:** Использование `threads_api` только после одобрения хозяина в Telegram.

**Ключевые файлы и серверы:**
*   **Файлы:**
    *   `/root/bot.py` (Telegram бот)
    *   `/root/audit_agent.py` (Аудит Instagram)
    *   `/root/skills/` (директория скиллов)
    *   `/root/brain/` (директория памяти)
    *   `/root/roamaid_second_brain/CLAUDE.md` (системный контекст)
    *   `.env` (секреты, не трогать)
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот, все агенты, Dashboard на :8080)

---
*Автосжатие через Gemini*