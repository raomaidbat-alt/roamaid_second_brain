### Статус: 13.05.2026 06:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст
### Статус: 13.05.2026 04:00

Ты автономный AI-агент для роста в соцсетях, управляемый исключительно через Telegram бот.

## Что работает
-   **Ядро:** Telegram бот (`/root/bot.py`) и агент аудита Instagram (`/root/audit_agent.py`).
-   **Скиллы:** Анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram, аудит сайтов, обучение из YouTube видео (`/learn`), анализ вирусных тредов (`/analyze_threads`), публикация постов/тредов в Threads (`/post_to_threads`).
-   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [url]`, `/analyze_threads [@username или URL]`.
-   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
-   **Память:** Трехслойная система (`/root/brain/memory/`, `/root/brain/daily/`, `/root/roamaid_second_brain/CLAUDE.md`).
-   **Правила:** Чтение `CLAUDE.md`, `git commit + push` после изменений, логирование в `daily/`, защита `.env`.

## Что сломано
В предоставленном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст слайдов, Playwright рендерит HTML в PNG (требуется Chromium). Поддержка форматов Threads 4:5, Instagram 1:1, Stories 9:16.
2.  **Публикация в Threads с одобрением:** Внедрить обязательное одобрение хозяином через Telegram для любой публикации в Threads, включая карусели.

## Ключевые файлы и серверы
-   **Файлы/Директории:**
    -   `/root/bot.py` (Telegram бот)
    -   `/root/audit_agent.py` (Аудит Instagram)
    -   `/root/skills/` (Директория скиллов)
    -   `/root/brain/` (Директория памяти)
    -   `/root/roamaid_second_brain/CLAUDE.md` (Системный контекст, правила)
    -   `.env` (Секреты конфигурации)
-   **Серверы:**
    -   `150.241.116.28:8000` (Social Analyzer API)
    -   `2.27.36.182` (Telegram бот + все агенты)
```

---
*Автосжатие через Gemini*