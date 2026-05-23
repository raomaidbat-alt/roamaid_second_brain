### Статус: 23.05.2026 16:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент для роста в соцсетях, управляемый через Telegram бот. Хозяин общается только через Telegram.

## Что работает
*   **Серверы:** Social Analyzer API (150.241.116.28:8000), Telegram бот + агенты (2.27.36.182, ты здесь).
*   **Основные компоненты:** Telegram бот (`/root/bot.py`), аудит Instagram (`/root/audit_agent.py`).
*   **Скиллы (рабочие):** Анализ роликов (`/analyze_reel/`), генерация тредов (`/generate_thread/`), полный аудит Instagram (`/audit_account/`), аудит сайтов (`/audit_website/`), обучение из YouTube (`/learn_from_video/`).
*   **Недавно реализовано:** Анализ вирусных тредов (`/analyze_threads/`) и публикация в Threads (`/post_to_threads/`). Оба требуют `THREADS_USERNAME` и `THREADS_PASSWORD` в окружении.
*   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [url]`, `/analyze_threads @username или URL`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
*   **Память:** Трехслойная система (`/root/brain/memory/`, `/root/brain/daily/`, `CLAUDE.md`).
*   **Правила:** Чтение `CLAUDE.md`, `git commit + push`, логирование, запрет на изменение `.env`.

## Что сломано
В предоставленном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст слайдов. Playwright (требует Chromium) рендерит HTML в PNG для форматов Threads (4:5), Instagram (1:1), Stories (9:16). Предусмотрен предварительный просмотр и одобрение хозяином в Telegram.
2.  **Публикация в Threads с одобрением:** Внедрение обязательного одобрения хозяином через Telegram перед любой публикацией в Threads, используя `threads_api`.

## Ключевые файлы и серверы
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + агенты)
*   **Файлы/Директории:**
    *   `/root/bot.py`
    *   `/root/audit_agent.py`
    *   `/root/skills/` (все скиллы)
    *   `/root/brain/` (система памяти)
    *   `/root/roamaid_second_brain/CLAUDE.md` (системный контекст)
    *   `.env` (секреты окружения)
```

---
*Автосжатие через Gemini*