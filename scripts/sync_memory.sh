#!/bin/bash
DATE=$(date '+%Y-%m-%d %H:%M')

# Сжимаем контекст через Gemini
python3 /root/roamaid_second_brain/scripts/compress_memory.py

# Копируем актуальные файлы
cp /root/bot.py /root/roamaid_second_brain/
cp /root/audit_agent.py /root/roamaid_second_brain/
cp -r /root/skills/* /root/roamaid_second_brain/skills/ 2>/dev/null

# Пушим в GitHub
cd /root/roamaid_second_brain
git add .
git commit -m "auto-sync: $DATE" --allow-empty
git push origin main

echo "✅ Готово: $DATE"
