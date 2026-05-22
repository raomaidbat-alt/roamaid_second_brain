### Статус: 22.05.2026 18:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент для роста в соцсетях, управляемый через Telegram бот. Хозяин общается только через Telegram.

## Что работает
*   **Основные компоненты:** Telegram бот (`/root/bot.py`), агент аудита Instagram (`/root/audit_agent.py`), анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram и сайтов, обучение из YouTube видео.
*   **Выполненные задачи:** Анализ вирусных тредов (`/root/skills/analyze_threads/`) и публикация в Threads (`/root/skills/post_to_threads/`). Обе требуют `THREADS_USERNAME` и `THREADS_PASSWORD` в окружении.
*   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [youtube url]`, `/analyze_threads @username или URL поста`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
*   **Архитектура памяти:** Трехслойная: факты (`/root/brain/memory/`), ежедневные заметки (`/root/brain/daily/`), системный контекст (`/root/roamaid_second_brain/CLAUDE.md`).
*   **Правила работы:** Всегда читать `CLAUDE.md`, `git commit + push`, логировать в `/root/brain/daily/`, не трогать `.env`.

## Что сломано
В предоставленном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст слайдов. Playwright рендерит HTML→PNG (требуется установка Chromium). Поддержка форматов Threads (4:5), Instagram (1:1), Stories (9:16). Предусматривается предпросмотр и одобрение хозяином в Telegram.
2.  **Публикация в Threads с одобрением:** Внедрить обязательное одобрение хозяином через Telegram перед любой публикацией.

## Ключевые файлы и серверы
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + все агенты)
*   **Файлы/Директории:** `/root/bot.py`, `/root/audit_agent.py`, `/root/skills/` (все скиллы), `/root/brain/` (память), `/root/roamaid_second_brain/CLAUDE.md` (системный контекст), `.env` (секреты).
```

---
*Автосжатие через Gemini*