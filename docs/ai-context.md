### Статус: 08.05.2026 23:00
```markdown
# Roamaid Second Brain — Системный контекст (Сжато)

Ты автономный AI-агент для роста в соцсетях, управляемый исключительно через Telegram бот.

## Что работает
-   **Ядро:** Telegram бот (`/root/bot.py`), агент аудита Instagram (`/root/audit_agent.py`).
-   **Скиллы:** Анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram, аудит сайтов, обучение из YouTube видео (`/learn`), анализ вирусных тредов (`/analyze_threads`), публикация постов в Threads (`/post_to_threads`).
-   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [youtube url]`, `/analyze_threads @username или URL`.
-   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API, Telegram Bot API.
-   **Память (3 слоя):** `/root/brain/memory/` (факты), `/root/brain/daily/` (ежедневные заметки), `/root/roamaid_second_brain/CLAUDE.md` (правила и контекст).
-   **Правила:** Всегда читать `CLAUDE.md`, `git commit + push` после изменений, логировать важные действия, не трогать `.env`.

## Что сломано
В предоставленном системном контексте нет явно указанных сломанных компонентов или ошибок.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст слайдов, Playwright рендерит HTML в PNG (требуется установка Chromium). Требуется механизм одобрения хозяином через Telegram перед публикацией (форматы: Threads 4:5, Instagram 1:1, Stories 9:16).
2.  **Публикация в Threads с одобрением:** Внедрить обязательное одобрение хозяина через Telegram для любой публикации в Threads.

## Ключевые файлы и серверы
-   **Файлы:**
    -   `/root/bot.py` (Telegram бот)
    -   `/root/audit_agent.py` (Аудит Instagram)
    -   `/root/skills/` (Директория всех скиллов)
    -   `/root/brain/` (Директория памяти)
    -   `/root/roamaid_second_brain/CLAUDE.md` (Системный контекст, правила)
    -   `.env` (Секреты конфигурации)
    -   Google Sheets ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo` (Листы: Аккаунты, CRM, Ролики, Активность, Сайты, Сайты-список)
-   **Серверы:**
    -   `150.241.116.28:8000` (Social Analyzer API)
    -   `2.27.36.182` (Telegram бот + все агенты)
```

---
*Автосжатие через Gemini*