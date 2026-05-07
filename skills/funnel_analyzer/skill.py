"""funnel_analyzer - полный анализ с Instagram API + Google Sheets"""

import asyncio
import logging
import requests
from datetime import datetime

logger = logging.getLogger("funnel_analyzer")

API_SERVER = "http://150.241.116.28:8000"
GOOGLE_CREDS_FILE = "/root/google_credentials.json"
NEW_SHEETS_ID = "1UzCKnVA36dBCc3B_W-Rv0GRagX9MMMivSD1-YOYmHrg"

NICHE_KEYWORDS = {
    "юристы": ["юрист", "закон", "адвокат", "право"],
    "маркетологи": ["маркетинг", "рост", "продажи", "smm", "реклама"],
    "психологи": ["психолог", "терапия", "консультация", "психология"],
    "дизайнеры": ["дизайн", "дизайнер", "ui", "ux", "графика"],
    "художники": ["художник", "арт", "искусство", "живопись"],
    "фитнес": ["фитнес", "тренер", "спорт", "gym", "тренировка"],
}

def collect_instagram_data(username: str):
    username = username.strip("@").strip()
    if not username:
        return None
    
    try:
        resp = requests.post(f"{API_SERVER}/profile", json={"username": username}, timeout=10)
        data = resp.json()
        
        if "detail" in data or "error" in str(data).lower():
            return None
        
        return {
            "username": username,
            "bio": data.get("bio", ""),
            "followers": data.get("followers", 0),
        }
    except:
        return None

def detect_niche(bio: str) -> str:
    if not bio:
        return "другое"
    
    bio_lower = bio.lower()
    scores = {}
    
    for niche, keywords in NICHE_KEYWORDS.items():
        scores[niche] = sum(bio_lower.count(kw) for kw in keywords)
    
    max_score = max(scores.values()) if scores.values() else 0
    return max(scores, key=scores.get) if max_score > 0 else "другое"

def calculate_revenue(followers: int, niche: str) -> int:
    multipliers = {"юристы": 2.0, "маркетологи": 1.5, "психологи": 1.3, "дизайнеры": 1.4, "художники": 1.2, "фитнес": 1.8}
    avg_checks = {"юристы": 50000, "маркетологи": 10000, "психологи": 5000, "дизайнеры": 25000, "художники": 15000, "фитнес": 3000}
    
    base = followers * 0.3 * 4 * 0.04 * 0.05
    mult = multipliers.get(niche, 1.0)
    avg_check = avg_checks.get(niche, 10000)
    
    revenue = int(base * avg_check * mult)
    return max(revenue, 5000)

def save_to_sheets(username: str, niche: str, followers: int, revenue: int) -> bool:
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(NEW_SHEETS_ID)
        
        try:
            ws = sheet.worksheet("Funnel Analysis")
        except:
            ws = sheet.add_worksheet("Funnel Analysis", 1000, 10)
            ws.append_row(["Дата", "Ник", "Ниша", "Подписчиков", "Instagram", "Telegram", "PDF", "Потенциал"])
        
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d"),
            f"@{username}",
            niche,
            followers,
            f"https://instagram.com/{username}",
            "",
            "",
            f"{revenue:,} руб/мес"
        ])
        
        return True
    except Exception as e:
        logger.error(f"Sheets error: {e}")
        return False

async def analyze_funnels(usernames, category_filter=None):
    if not usernames:
        return "Укажи никнеймы"
    
    output = f"Анализ {len(usernames)} профилей\n"
    if category_filter:
        output += f"Фильтр: {category_filter}\n\n"
    
    results = []
    errors = []
    filtered = []
    
    for username in usernames:
        data = collect_instagram_data(username)
        
        if not data:
            errors.append(username)
            continue
        
        niche = detect_niche(data["bio"])
        
        if category_filter and category_filter.lower() not in niche.lower():
            filtered.append(f"{username} ({niche})")
            continue
        
        revenue = calculate_revenue(data["followers"], niche)
        
        save_to_sheets(username, niche, data["followers"], revenue)
        
        results.append((username, niche, data["followers"], revenue))
        
        await asyncio.sleep(0.3)
    
    if results:
        output += "Результаты:\n"
        for username, niche, followers, revenue in sorted(results, key=lambda x: x[3], reverse=True):
            output += f"{username} ({niche})\n  {followers:,} подписчиков\n  {revenue:,} руб/мес\n\n"
    
    if filtered:
        output += f"Отфильтровано: {len(filtered)}\n"
        for item in filtered[:3]:
            output += f"  {item}\n"
    
    if errors:
        output += f"\nОшибки: {len(errors)}\n"
    
    output += f"\nПроанализировано: {len(results)}/{len(usernames)}"
    output += f"\nРезультаты в Google Sheets"
    
    return output
