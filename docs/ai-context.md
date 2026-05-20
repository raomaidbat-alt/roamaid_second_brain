### Статус: 21.05.2026 00:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент для роста в соцсетях, управляемый через Telegram бот. Хозяин общается только через Telegram.

## Что работает
*   **Основные функции:** Аудит Instagram (`/audit`), аудит сайтов (`/audit_sites`), анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), обучение из YouTube (`/learn`), анализ вирусных тредов (`/analyze_threads`), и публикация в Threads (`/post_to_threads`). Для Threads требуются `THREADS_USERNAME` и `THREADS_PASSWORD` в окружении.
*   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [url]`, `/analyze_threads [username/url]`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
*   **Архитектура памяти:** Трехслойная: факты (`/root/brain/memory/`), ежедневные заметки (`/root/brain/daily/`), системный контекст (`/root/roamaid_second_brain/CLAUDE.md`).
*   **Правила работы:** Читать `CLAUDE.md` в начале сессии, `git commit + push` после изменений, логировать важные действия в `/root/brain/daily/`, не трогать `.env`.

## Что сломано
В предоставленном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Создание текста слайдов (Gemini), рендеринг HTML→PNG (Playwright, требуется Chromium), поддержка форматов (Threads 4:5, Instagram 1:1, Stories 9:16). Предпросмотр и одобрение хозяином в Telegram.
2.  **Публикация в Threads с одобрением:** Внедрение обязательного одобрения хозяином через Telegram перед любой публикацией в Threads.

## Ключевые файлы и серверы
*   **Файлы/Директории:** `/root/bot.py`, `/root/audit_agent.py`, `/root/skills/` (все скиллы), `/root/brain/` (память), `/root/roamaid_second_brain/CLAUDE.md` (системный контекст), `.env` (секреты).
*   **Серверы:** `150.241.116.28:8000` (Social Analyzer API), `2.27.36.182` (Telegram бот + все агенты).
```

---
*Автосжатие через Gemini*