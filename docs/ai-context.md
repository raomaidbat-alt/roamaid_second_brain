### Статус: 19.05.2026 00:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент для роста в соцсетях, управляемый через Telegram бот. Твой хозяин общается с тобой только через Telegram.

## Что работает
*   **Функционал:** Аудит Instagram (`/audit`) и сайтов (`/audit_sites`), анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), обучение из YouTube (`/learn`), анализ вирусных тредов (`/analyze_threads`), публикация в Threads (`/post_to_threads`).
*   **Команды бота:** `/audit`, `/audit_sites`, `/stats`, `/log`, `/learn`, `/analyze_threads`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
*   **Память:** Трехслойная (факты, ежедневные заметки, системный контекст).
*   **Правила работы:** Читать системный контекст, `git commit + push`, логировать действия, не изменять `.env`.

## Что сломано
В предоставленном системном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Реализовать генерацию текста слайдов (Gemini) и рендеринг HTML в PNG (Playwright, требуется Chromium). Поддержка форматов: Threads 4:5, Instagram 1:1, Stories 9:16.
2.  **Публикация в Threads с одобрением:** Внедрить обязательное одобрение хозяином через Telegram перед любой публикацией в Threads.

## Ключевые файлы и серверы
*   **Файлы/Директории:**
    *   `/root/bot.py` (Telegram бот)
    *   `/root/audit_agent.py` (Аудит Instagram)
    *   `/root/skills/` (все скиллы)
    *   `/root/brain/` (память)
    *   `/root/roamaid_second_brain/CLAUDE.md` (системный контекст)
    *   `.env` (секреты)
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + агенты)
```

---
*Автосжатие через Gemini*