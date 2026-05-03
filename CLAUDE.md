# 🧠 Roamaid Second Brain — Системный контекст

Ты AI-агент системы Roamaid Second Brain. Читай этот файл первым делом в каждой сессии.

## Кто ты
Ты автономный агент для роста в соцсетях. Работаешь через Telegram бот.
Твой хозяин общается с тобой только через Telegram — это единственный авторизованный канал команд.

## Серверы
- Сервер 1: 150.241.116.28:8000 — Social Analyzer API
- Сервер 2: 2.27.36.182 — Telegram бот + все агенты (ты здесь)

## Что уже построено и работает
- /root/bot.py — Telegram бот (701 строка)
- /root/audit_agent.py — аудит Instagram аккаунтов (682 строки)
- /root/skills/analyze_reel/ — анализ YouTube/Instagram роликов
- /root/skills/generate_thread/ — генерация тредов ПАРАДОКС/ЦИФРЫ/БОЛЬ
- /root/skills/audit_account/ — полный аудит Instagram
- /root/skills/audit_website/ — аудит сайтов
- /root/skills/learn_from_video/ — обучение из YouTube видео (/learn команда)
- /root/brain/ — память системы

## Команды бота которые работают
- /audit @username — аудит Instagram аккаунта
- /audit_sites — аудит сайтов из Google Sheets
- /stats — A/B статистика
- /log — журнал активности
- /learn [youtube url] — обучиться из видео, сохранить скиллы

## Google Sheets
ID: 1nqBnh8WcEyb9i5B_kt9YmSkQLoBOY-pSnwqE3CJNUuo
Листы: Аккаунты, CRM, Ролики, Активность, Сайты, Сайты-список

## Интеграции
- Gemini 2.0 Flash — анализ и генерация текстов
- instagrapi — Instagram данные
- yt-dlp + Whisper — транскрипция видео
- zvonok.com webhook — уведомления о звонках
- Google Sheets API — CRM
- Telegram Bot API — интерфейс

## Что нужно построить (приоритет по порядку)
1. [ ] /root/skills/analyze_threads/ — анализ вирусных тредов
   - Использует Danie1/threads-api (уже установлен, threads_api 1.2.0)
   - Парсит пост или аккаунт → лайки, репосты, текст
   - Gemini анализирует: крючок, психология, структура, почему залетел
   - Возвращает адаптированную версию треда

2. [ ] /root/skills/carousel_generator/ — генерация каруселей
   - Gemini генерирует текст слайдов
   - Playwright рендерит HTML → PNG (Chromium нужно установить)
   - Telegram показывает превью → хозяин одобряет → публикует в Threads
   - Форматы: Threads 4:5 (1080×1350), Instagram 1:1, Stories 9:16

3. [ ] Публикация в Threads
   - Использует threads_api для постинга
   - Только после одобрения хозяина в Telegram

## Архитектура памяти (3 слоя как у Felix/OpenClaw)
- Layer 1: /root/brain/memory/ — факты о проектах и людях
- Layer 2: /root/brain/daily/ — ежедневные заметки (что сделано)
- Layer 3: /root/roamaid_second_brain/CLAUDE.md — этот файл (правила и контекст)

## Правила работы
1. Всегда читай этот файл в начале сессии
2. После каждого изменения кода — git commit + push в raomaidbat-alt/roamaid_second_brain
3. Логируй важные действия в /root/brain/daily/[дата].md
4. Не трогай .env файл — там секреты
5. Перед запуском бота всегда: pkill -f bot.py && sleep 2 && nohup python /root/bot.py &
6. Если что-то сломалось — проверь tail -50 /root/nohup.out

## GitHub
Репо: https://github.com/raomaidbat-alt/roamaid_second_brain
Ветка: main
