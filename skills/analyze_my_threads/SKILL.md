---
name: analyze_my_threads
description: Track Roman's own Threads account, analyze top-performing posts through Gemini, write Threads analytics to Google Sheets, update prompt memory, and send weekly Telegram reports.
---

# analyze_my_threads

Use `/root/skills/analyze_my_threads/skill.py` for Roman's own Threads performance loop.

Core commands:

```bash
python3 /root/skills/analyze_my_threads/skill.py analyze
python3 /root/skills/analyze_my_threads/skill.py report
```

Environment expected from `/root/roamaid_second_brain/.env` or shell:

- `THREADS_USERNAME`, `THREADS_PASSWORD` — Threads login
- `GEMINI_API_KEY` — Gemini analysis
- `TELEGRAM_TOKEN` — report delivery
- optional `TELEGRAM_CHAT_ID` — defaults to Roman `375420313`

Outputs:

- Google Sheet `Threads-аналитика`
- `/root/brain/memory/my_threads_patterns.md`
- updates `/root/skills/generate_thread/skill.py` prompt memory by making it read `my_threads_patterns.md`
