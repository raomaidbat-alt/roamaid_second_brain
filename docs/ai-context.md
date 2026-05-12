### Статус: 13.05.2026 02:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты автономный AI-агент для роста в соцсетях, управляемый исключительно через Telegram бот.

## Что работает
-   **Ядро:** Telegram бот (`/root/bot.py`) и агент аудита Instagram (`/root/audit_agent.py`).
-   **Скиллы:** Анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram, аудит сайтов, обучение из YouTube видео (`/learn`), анализ вирусных тредов (`/analyze_threads`), публикация постов/тредов в Threads (`/post_to_threads`).
-   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [url]`, `/analyze_threads [@username или URL]`.
-   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
-   **Память (3 слоя):** `/root/brain/memory/` (факты), `/root/brain/daily/` (ежедневные заметки), `/root/roamaid_second_brain/CLAUDE.md` (правила и контекст).
-   **Правила работы:** Всегда читать `CLAUDE.md`, `git commit + push` после изменений, логировать важные действия, не трогать `.env`.

## Что сломано
В предоставленном контексте нет явно указанных сломанных компонентов.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст, Playwright рендерит HTML в PNG (требуется Chromium). Требуется механизм одобрения хозяином через Telegram перед публикацией (форматы: Threads 4:5, Instagram 1:1, Stories 9:16).
2.  **Публикация в Threads с одобрением:** Внедрить обязательное одобрение хозяина через Telegram для любой публикации в Threads.

## Ключевые файлы и серверы
-   **Файлы/Директории:**
    -   `/root/bot.py` (Telegram бот)
    -   `/root/audit_agent.py` (Аудит Instagram)
    -   `/root/skills/` (Директория всех скиллов)
    -   `/root/brain/` (Директория памяти)
    -   `/root/roamaid_second_brain/CLAUDE.md` (Системный контекст, правила)
    -   `.env` (Секреты конфигурации)
-   **Серверы:**
    -   `150.241.116.28:8000` (Social Analyzer API)
    -   `2.27.36.182` (Telegram бот + все агенты)
```

---
*Автосжатие через Gemini*