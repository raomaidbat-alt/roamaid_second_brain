# Roman Ops Dashboard — Vercel

Отдельная Vercel-версия dashboard.

## Deploy

```bash
cd /root/roamaid_second_brain/vercel-dashboard
npx vercel --prod
```

Если нужен конкретный домен — добавь его в Vercel проекте или командой:

```bash
npx vercel domains add YOUR_DOMAIN
```

## Notes

- Vercel serverless не имеет доступа к `/root/brain`, PM2 и локальным файлам VPS.
- Поэтому эта версия — отдельный web-dashboard. Для живых данных лучше подключить GitHub/Google Sheets/API endpoints.
- Current VPS dashboard remains: http://2.27.36.182:8080/
