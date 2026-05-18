### Статус: 18.05.2026 06:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент для роста в соцсетях, управляемый через Telegram бот.

## Что работает
*   **Ядро и Скиллы:** `/root/bot.py` (Telegram бот), `/root/audit_agent.py` (аудит Instagram). Работают скиллы для анализа YouTube/Instagram роликов, генерации тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), аудита Instagram аккаунтов и сайтов, обучения из YouTube видео (`/learn`), анализа вирусных тредов (`/analyze_threads`) и публикации в Threads (`/post_to_threads`).
*   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [youtube url]`, `/analyze_threads`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
*   **Память:** Трехслойная архитектура: `/root/brain/memory/` (факты), `/root/brain/daily/` (ежедневные заметки), `/root/roamaid_second_brain/CLAUDE.md` (системный контекст).
*   **Правила работы:** Всегда читать контекст, `git commit + push` после изменений, логировать в `/root/brain/daily/`, не изменять `.env`.

## Что сломано
В предоставленном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст, Playwright рендерит HTML в PNG (требуется установка Chromium). Поддерживаемые форматы: Threads 4:5, Instagram 1:1, Stories 9:16.
2.  **Публикация в Threads с одобрением:** Внедрить обязательное одобрение хозяином через Telegram перед любой публикацией.

## Ключевые файлы и серверы
*   **Файлы/Директории:**
    *   `/root/bot.py`
    *   `/root/audit_agent.py`
    *   `/root/skills/` (включая `analyze_reel/`, `generate_thread/`, `audit_account/`, `audit_website/`, `learn_from_video/`, `analyze_threads/`, `post_to_threads/`, `carousel_generator/`)
    *   `/root/brain/` (включая `memory/`, `daily/`)
    *   `/root/roamaid_second_brain/CLAUDE.md`
    *   `.env`
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + все агенты)
```

---
*Автосжатие через Gemini*