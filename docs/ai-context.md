### Статус: 20.05.2026 06:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент для роста в соцсетях, управляемый через Telegram бот. Хозяин общается только через Telegram.

## Что работает
*   **Функционал:** Аудит Instagram (`/audit`) и сайтов (`/audit_sites`), анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), обучение из YouTube (`/learn`), анализ вирусных тредов (`/analyze_threads`), публикация в Threads (`/post_to_threads`). Для Threads требуется `THREADS_USERNAME` и `THREADS_PASSWORD` в окружении.
*   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [url]`, `/analyze_threads [username/url]`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo` для CRM, аккаунтов, роликов), Telegram Bot API.
*   **Архитектура:** Трехслойная память: факты о проектах (`/root/brain/memory/`), ежедневные заметки (`/root/brain/daily/`), системный контекст (`/root/roamaid_second_brain/CLAUDE.md`).
*   **Правила:** Читать `CLAUDE.md`, `git commit + push` после изменений, логировать важные действия, не трогать `.env`.

## Что сломано
В предоставленном контексте явно сломанных компонентов не указано.

<h2>Следующий шаг (приоритет по порядку)</h2>
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`):
    *   Разработка генерации текста слайдов с помощью Gemini.
    *   Рендеринг HTML в PNG с использованием Playwright (требуется установка Chromium).
    *   Поддержка форматов: Threads 4:5 (1080×1350), Instagram 1:1, Stories 9:16.
    *   Предварительный просмотр в Telegram для одобрения хозяином перед публикацией в Threads.
2.  **Публикация в Threads с одобрением:** Внедрение обязательного одобрения хозяином через Telegram перед любой окончательной публикацией в Threads.

## Ключевые файлы и серверы
*   **Файлы/Директории:**
    *   `/root/bot.py` (Telegram бот)
    *   `/root/audit_agent.py` (Аудит Instagram)
    *   `/root/skills/` (все скиллы, включая `/analyze_reel/`, `/generate_thread/`, `/audit_account/`, `/audit_website/`, `/learn_from_video/`, `/analyze_threads/`, `/post_to_threads/`, `/carousel_generator/`)
    *   `/root/brain/` (память системы)
    *   `/root/roamaid_second_brain/CLAUDE.md` (системный контекст и правила)
    *   `.env` (секреты, не трогать)
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + все агенты)
```

---
*Автосжатие через Gemini*