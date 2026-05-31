### Статус: 01.06.2026 00:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент Roamaid Second Brain для роста в соцсетях, управляемый исключительно через Telegram.

## Что работает
*   **Роль:** Автономный агент для роста в соцсетях.
*   **Серверы:** Social Analyzer API (`150.241.116.28:8000`), Telegram бот + агенты (`2.27.36.182`).
*   **Ключевые компоненты:** `/root/bot.py` (Telegram бот), `/root/audit_agent.py` (аудит Instagram), `/root/brain/` (память).
*   **Рабочие скиллы:** Анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram, аудит сайтов, обучение из YouTube видео, **анализ вирусных тредов**, **публикация в Threads**.
*   **Рабочие команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [youtube url]`, `/analyze_threads @username или URL поста`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YpSnwqE3CJNUuo`), Telegram Bot API.
*   **Память:** Трехслойная архитектура (`/root/brain/memory/`, `/root/brain/daily/`, `CLAUDE.md`).
*   **Правила работы:** Чтение `CLAUDE.md` при старте, `git commit + push`, логирование действий, защита `.env`.

## Что сломано
В предоставленном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст, Playwright рендерит HTML → PNG (требует Chromium). Реализовать предпросмотр в Telegram и одобрение хозяином. Поддержка форматов: Threads (4:5), Instagram (1:1), Stories (9:16).
2.  **Публикация в Threads с одобрением хозяина:** Использование `threads_api` для постинга только после одобрения хозяином в Telegram.

## Ключевые файлы и серверы
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + агенты)
*   **Ключевые файлы/директории:**
    *   `/root/bot.py`
    *   `/root/audit_agent.py`
    *   `/root/skills/`
    *   `/root/brain/`
    *   `/root/roamaid_second_brain/CLAUDE.md`
    *   `.env`
    *   Google Sheets ID: `1nqBnh8WCEyb9i5B_kt9YpSnwqE3CJNUuo`
```

---
*Автосжатие через Gemini*