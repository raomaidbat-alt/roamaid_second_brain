### Статус: 17.05.2026 14:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент для роста в соцсетях, управляется через Telegram бот.

## Что работает
*   **Ядро:** `/root/bot.py` (Telegram бот) и `/root/audit_agent.py` (аудит Instagram).
*   **Скиллы:** Анализ роликов (YT/IG), генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), аудит IG/сайтов, обучение из YT (`/learn`), анализ вирусных тредов (`/analyze_threads`), публикация в Threads (`/post_to_threads`).
*   **Команды бота:** `/audit`, `/audit_sites`, `/stats`, `/log`, `/learn`, `/analyze_threads`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
*   **Память:** Трехслойная система: `/root/brain/memory/`, `/root/brain/daily/`, системный контекст.
*   **Правила работы:** Чтение контекста, `git commit + push`, логирование в `daily/`, защита `.env`.

## Что сломано
В предоставленном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст, Playwright рендерит HTML в PNG (требуется установка Chromium). Поддержка форматов: Threads 4:5, Instagram 1:1, Stories 9:16.
2.  **Публикация в Threads с одобрением:** Внедрить обязательное одобрение хозяином через Telegram перед любой публикацией в Threads.

## Ключевые файлы и серверы
*   **Файлы/Директории:**
    *   `/root/bot.py`
    *   `/root/audit_agent.py`
    *   `/root/skills/`
    *   `/root/brain/`
    *   `/root/roamaid_second_brain/CLAUDE.md`
    *   `.env`
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + все агенты)
```

---
*Автосжатие через Gemini*