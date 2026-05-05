### Статус: 05.05.2026 14:00
```markdown
# Roamaid Second Brain — Системный контекст

## Что работает
-   **Роль:** Автономный AI-агент для роста в соцсетях, управляемый через Telegram бот.
-   **Скиллы:** Анализ роликов, генерация тредов (ПАРАДОКС/ЦИФРЫ/БОЛЬ), полный аудит Instagram и сайтов, обучение из YouTube (`/learn`). Недавно добавлены: анализ вирусных тредов (`/analyze_threads`) и публикация постов в Threads (`/post_to_threads`).
-   **Команды бота:** `/audit`, `/audit_sites`, `/stats`, `/log`, `/learn`, `/analyze_threads`.
-   **Интеграции:** Gemini 2.0 Flash, instagrapi, yt-dlp + Whisper, Google Sheets API (для CRM, аккаунтов, сайтов ID: `1nqBnh8WCEyb...`), Telegram Bot API, zvonok.com webhook.
-   **Память:** 3-слойная архитектура: `/root/brain/memory/`, `/root/brain/daily/`, `/root/roamaid_second_brain/CLAUDE.md`.
-   **Правила:** Чтение `CLAUDE.md`, `git commit + push` после изменений, логирование в `/root/brain/daily/`, `.env` не трогать.

## Что сломано
-   **OpenClaw gateway:** Использует WebSocket вместо REST API и настроен через ChatGPT Plus OAuth, что ограничивает прямой доступ к другим AI-провайдерам.

## Следующий шаг (приоритет)
1.  **Генерация каруселей (`/root/skills/carousel_generator/`):** Gemini генерирует текст, Playwright рендерит HTML в PNG (требуется Chromium). Telegram превью для одобрения хозяином перед публикацией (Threads 4:5, Instagram 1:1, Stories 9:16).
2.  **Публикация в Threads (одобрение):** Внедрить обязательный процесс одобрения хозяином в Telegram перед использованием функции публикации.

## Ключевые файлы и серверы
-   **Файлы:**
    -   `/root/bot.py` (Telegram бот)
    -   `/root/audit_agent.py` (Агент аудита Instagram)
    -   `/root/skills/` (Директория всех скиллов)
    -   `/root/brain/` (Директория памяти)
    -   `/root/roamaid_second_brain/CLAUDE.md` (Системный контекст, правила)
    -   `.env` (Секреты конфигурации)
-   **Серверы:**
    -   `150.241.116.28:8000` (Social Analyzer API)
    -   `2.27.36.182` (Telegram бот, все агенты)
```

---
*Автосжатие через Gemini*