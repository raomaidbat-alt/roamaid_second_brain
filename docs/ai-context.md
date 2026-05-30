### Статус: 30.05.2026 06:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент Roamaid Second Brain для роста в соцсетях, управляемый исключительно через Telegram.

## Что работает
*   **Роль:** Автономный агент для роста в соцсетях, взаимодействие через Telegram-бот.
*   **Серверы:** Social Analyzer API (`150.241.116.28:8000`), Telegram бот + все агенты (`2.27.36.182`).
*   **Основные компоненты:** Telegram бот (`/root/bot.py`), агент аудита Instagram (`/root/audit_agent.py`).
*   **Рабочие скиллы:** Анализ роликов, генерация тредов, полный аудит Instagram, аудит сайтов, обучение из YouTube, анализ вирусных тредов (✅), публикация в Threads (✅).
*   **Рабочие команды бота:** `/audit`, `/audit_sites`, `/stats`, `/log`, `/learn`, `/analyze_threads`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
*   **Память:** Трехслойная архитектура (`/root/brain/memory/`, `/root/brain/daily/`, `/root/roamaid_second_brain/CLAUDE.md`).
*   **Правила работы:** Чтение `CLAUDE.md` при старте, `git commit + push`, логирование, защита `.env`.

## Что сломано
В предоставленном системном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст слайдов, Playwright рендерит HTML → PNG (требует установки Chromium). Поддержка форматов: Threads (4:5), Instagram (1:1), Stories (9:16).
2.  **Публикация в Threads с одобрением:** Внедрение обязательного одобрения хозяином через Telegram перед фактической публикацией контента в Threads.

## Ключевые файлы и серверы
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + агенты)
*   **Ключевые файлы/директории:**
    *   `/root/bot.py`
    *   `/root/audit_agent.py`
    *   `/root/skills/` (все скиллы)
    *   `/root/brain/` (система памяти)
    *   `/root/roamaid_second_brain/CLAUDE.md` (системный контекст)
    *   `.env` (секреты окружения)
    *   Google Sheets ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`
```

---
*Автосжатие через Gemini*