---
name: post_to_threads
description: Публикует текстовый пост или тред-серию в Threads. Поддерживает изображения. Только после одобрения хозяина в Telegram.
triggers:
  - опубликуй в threads
  - запостить в тредс
  - публикуй тред
---

# post_to_threads

## Что делает

Публикует пост в Threads от имени аккаунта из .env.
- `post_to_threads(text, image_paths)` — один пост (опционально с фото)
- `post_thread_series(posts)` — серия постов как тред (каждый следующий — ответ предыдущему)

## Зависимости

- `THREADS_USERNAME`, `THREADS_PASSWORD` в .env
- `threads_api` (1.2.0), `instagrapi`

## Важно

Публиковать только после явного подтверждения хозяина в Telegram (кнопка "Опубликовать").
