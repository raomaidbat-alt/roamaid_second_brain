
## Dashboard fixed and extended
- Dashboard PM2 process was stopped; restarted it.
- Dashboard available at http://2.27.36.182:8080/
- Added Analytics block: “Мой Instagram: топ посты + агент промптов”.
- New endpoint: POST /analytics/profile with Instagram username/profile URL.
- It fetches profile through Social Analyzer /profile, ranks top posts by views/likes/comments, and generates prompt-agent recommendations for Roman-style Threads.
- Threads generation prompt updated: human Roman style, longer clear trigger-driven writing, story-selling, mandatory CTA: https://t.me/+H1I_MHFuv603ZTdi
