
## Dashboard fixed and extended
- Dashboard PM2 process was stopped; restarted it.
- Dashboard available at http://2.27.36.182:8080/
- Added Analytics block: “Мой Instagram: топ посты + агент промптов”.
- New endpoint: POST /analytics/profile with Instagram username/profile URL.
- It fetches profile through Social Analyzer /profile, ranks top posts by views/likes/comments, and generates prompt-agent recommendations for Roman-style Threads.
- Threads generation prompt updated: human Roman style, longer clear trigger-driven writing, story-selling, mandatory CTA: https://t.me/+H1I_MHFuv603ZTdi

## Adaptive Threads prompt update
Dashboard Threads generator now calls `adaptive_threads_rules()` before every new thread generation. It reads:
- manually parsed analytics posts (`posts_data.json`),
- top Instagram profile posts (`profile_insights.json`),
- generated threads with metrics (`generated_threads.json`).

It scores content by views + weighted likes/comments/reposts + ER and injects adaptive rules into the prompt, so the writing automatically shifts toward hooks/topics/conflicts that perform with Roman's audience. If AI is unavailable, it falls back to the top metric examples.
