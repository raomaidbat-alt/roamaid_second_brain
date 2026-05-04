### Статус: 04.05.2026 17:19
Вот сжатый системный контекст:

**Что работает:**
*   **Ядро:** Telegram бот (`/root/bot.py`), агенты для аудита Instagram (`/root/audit_agent.py`), анализа YouTube/Instagram роликов, генерации тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полного аудита Instagram, аудита сайтов, обучения из YouTube видео.
*   **Команды:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [youtube url]`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook (порт 8081), Google Sheets API, Telegram Bot API.
*   **Google Sheets:** ID `1nqBnh8WcEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo` (Аккаунты, CRM, Ролики, Активность, Сайты, Сайты-список).
*   **Память:** 3-слойная архитектура (`/root/brain/memory/`, `/root/brain/daily/`, `/root/roamaid_second_brain/CLAUDE.md`).
*   **Недавние внедрения:** Анализ вирусных тредов (`/root/skills/analyze_threads/`) с адаптированным тредом и кнопкой публикации; публикация в Threads (`/root/skills/post_to_threads/`); Dashboard развернут на `http://2.27.36.182:8080`.

**Что сломано:**
*   **OpenClaw gateway:** Использует WebSocket (не REST API). Отсутствует прямой доступ к AI-провайдерам (нет API-ключей), настроен через ChatGPT Plus OAuth.

**Следующий шаг (приоритет по порядку):**
1.  **Генерация каруселей (`/root/skills/carousel_generator/`):** Gemini генерирует текст слайдов, Playwright (требуется Chromium) рендерит HTML → PNG. Предпросмотр в Telegram для одобрения, затем публикация (Threads 4:5, Instagram 1:1, Stories 9:16).
2.  **Публикация в Threads:** Использование `threads_api` только после одобрения хозяина в Telegram.

**Ключевые файлы и серверы:**
*   **Файлы:**
    *   `/root/bot.py` (Telegram бот)
    *   `/root/audit_agent.py` (Аудит Instagram)
    *   `/root/skills/` (директория со скиллами)
    *   `/root/brain/` (директория памяти)
    *   `/root/roamaid_second_brain/CLAUDE.md` (системный контекст)
    *   `.env` (конфиденциальные переменные, не трогать)
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот, все агенты, Dashboard)

---
*Автосжатие через Gemini*