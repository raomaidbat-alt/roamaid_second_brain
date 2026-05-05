### Статус: 05.05.2026 08:00
```markdown
# Roamaid Second Brain — Сжатый Системный Контекст

## Что работает
-   **Ядро & Агенты:** Telegram бот (`/root/bot.py`), агент аудита Instagram (`/root/audit_agent.py`). Работает на `2.27.36.182`.
-   **API:** Social Analyzer API (`150.241.116.28:8000`).
-   **Скиллы (завершенные):** Анализ роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), аудит Instagram/сайтов, обучение из YouTube (`/learn`). Недавно добавлены: анализ вирусных тредов (`/analyze_threads`) и публикация постов в Threads (`/post_to_threads`).
-   **Команды бота:** `/audit`, `/audit_sites`, `/stats`, `/log`, `/learn`, `/analyze_threads`.
-   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, Google Sheets API (ID: `1nqBnh8WCEyb...` для CRM, аккаунтов, сайтов), Telegram Bot API, zvonok.com webhook.
-   **Память:** 3-слойная архитектура: `/root/brain/memory/`, `/root/brain/daily/`, `/root/roamaid_second_brain/CLAUDE.md`.
-   **Операционные правила:** Чтение `CLAUDE.md`, `git commit + push` после изменений, логирование в `/root/brain/daily/`, `.env` не трогать.

## Что сломано
-   **OpenClaw gateway:** Использует WebSocket вместо REST API и настроен через ChatGPT Plus OAuth, что ограничивает прямой доступ к AI-провайдерам (информация из `docs/ai-context.md`).

## Следующий шаг (приоритет)
1.  **Генерация каруселей (`/root/skills/carousel_generator/`):**
    *   Gemini генерирует текст слайдов.
    *   Playwright рендерит HTML в PNG (требуется Chromium).
    *   Telegram превью для одобрения хозяином.
    *   Публикация в Threads (4:5), Instagram (1:1), Stories (9:16).
2.  **Публикация в Threads (поток одобрения):** Реализовать *процесс одобрения* хозяином в Telegram перед использованием уже существующей функции `post_to_threads`.

## Ключевые файлы и серверы
-   **Файлы:**
    -   `/root/bot.py` (Telegram бот)
    -   `/root/audit_agent.py` (Агент аудита Instagram)
    -   `/root/skills/` (Директория всех скиллов)
    -   `/root/brain/` (Директория памяти)
    -   `/root/roamaid_second_brain/CLAUDE.md` (Системный контекст)
    -   `.env` (Секреты конфигурации)
-   **Серверы:**
    -   `150.241.116.28:8000` (Social Analyzer API)
    -   `2.27.36.182` (Telegram бот, все агенты)
```

---
*Автосжатие через Gemini*