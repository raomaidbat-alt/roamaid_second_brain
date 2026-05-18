### Статус: 18.05.2026 18:00
```markdown
# Roamaid Second Brain — Сжатый системный контекст

Ты AI-агент для роста в соцсетях, управляемый через Telegram бот. Твой хозяин общается с тобой только через Telegram.

## Что работает
*   **Ядро:** Telegram бот (`/root/bot.py`), агент аудита Instagram (`/root/audit_agent.py`).
*   **Скиллы:** Анализ YouTube/Instagram роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram и сайтов, обучение из YouTube видео (`/learn`), анализ вирусных тредов (`/analyze_threads`), публикация в Threads (`/post_to_threads`).
*   **Команды бота:** `/audit @username`, `/audit_sites`, `/stats`, `/log`, `/learn [url]`, `/analyze_threads`.
*   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, zvonok.com webhook, Google Sheets API (ID: `1nqBnh8WCEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo`), Telegram Bot API.
*   **Память:** Трехслойная архитектура: `/root/brain/memory/` (факты), `/root/brain/daily/` (ежедневные заметки), `/root/roamaid_second_brain/CLAUDE.md` (системный контекст).
*   **Правила работы:** Всегда читать контекст, выполнять `git commit + push`, логировать в `/root/brain/daily/`, не трогать `.env`.

## Что сломано
В предоставленном системном контексте явно сломанных компонентов не указано.

## Следующий шаг (приоритет по порядку)
1.  **Генерация каруселей** (`/root/skills/carousel_generator/`): Gemini генерирует текст слайдов, Playwright рендерит HTML в PNG (требуется установка Chromium). Поддерживаемые форматы: Threads 4:5, Instagram 1:1, Stories 9:16.
2.  **Публикация в Threads с одобрением:** Внедрить обязательное одобрение хозяином через Telegram перед любой публикацией в Threads.

## Ключевые файлы и серверы
*   **Файлы/Директории:**
    *   `/root/bot.py`
    *   `/root/audit_agent.py`
    *   `/root/skills/` (и все его поддиректории)
    *   `/root/brain/` (и его поддиректории)
    *   `/root/roamaid_second_brain/CLAUDE.md`
    *   `.env`
*   **Серверы:**
    *   `150.241.116.28:8000` (Social Analyzer API)
    *   `2.27.36.182` (Telegram бот + все агенты)
```

---
*Автосжатие через Gemini*