"""funnel_analyzer - Анализ воронки клиента Instagram"""

import os, re, json, asyncio, logging, random
from typing import List, Dict, Optional
from datetime import datetime
import requests, gspread
from google.oauth2.service_account import Credentials

API_SERVER = "http://150.241.116.28:8000"
GOOGLE_CREDS_FILE = "/root/google_credentials.json"
NEW_SHEETS_ID = "1UzCKnVA36dBCc3B_W-Rv0GRagX9MMMivSD1-YOYmHrg"

logger = logging.getLogger("funnel_analyzer")

def collect_instagram_data(username: str, max_posts: int = 10) -> Optional[Dict]:
    """Собирает данные из Instagram"""
    username = username.strip("@").strip()
    if not username:
        return None
    
    try:
        profile_resp = requests.post(f"{API_SERVER}/profile", json={"username": username}, timeout=10)
        profile_data = profile_resp.json()
        if "detail" in profile_data:
            return None
        
        posts = profile_data.get("posts", [])[:max_posts]
        hashtags = set()
        for post in posts:
            hashtags.update(re.findall(r'#\w+', post.get("caption", "")))
        
        bio = profile_data.get("bio", "")
        links = re.findall(r'https?://[^\s]+', bio)
        
        return {
            "username": username,
            "bio": bio,
            "followers": profile_data.get("followers", 0),
            "posts": posts,
            "hashtags": list(hashtags),
            "links": links,
        }
    except:
        return None

def detect_niche(data: Dict) -> str:
    """Определяет нишу"""
    bio = data.get("bio", "").lower()
    hashtags = " ".join([tag.lower() for tag in data.get("hashtags", [])])
    
    niche_keywords = {
        "маркетологи": ["маркетинг", "рост", "funnel", "воронка", "продажи", "growth"],
        "психологи": ["психолог", "консультация", "психология", "терапия", "coaching"],
        "юристы": ["юрист", "закон", "консультация", "адвокат"],
        "дизайнеры": ["дизайн", "дизайнер", "ui", "ux", "графика"],
        "художники": ["художник", "арт", "искусство", "рисунок", "живопись"],
        "фитнес": ["фитнес", "спорт", "тренировка", "gym", "fitness"],
    }
    
    combined = f"{bio} {hashtags}"
    scores = {n: sum(combined.count(k) for k in kw) for n, kw in niche_keywords.items()}
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "другое"

def calculate_metrics(data: Dict, niche: str) -> Dict:
    """Считает метрики"""
    niche_metrics = {
        "маркетологи": {"avg_check": 10000, "revenue_mult": 1.5},
        "психологи": {"avg_check": 5000, "revenue_mult": 1.2},
        "юристы": {"avg_check": 50000, "revenue_mult": 1.8},
        "дизайнеры": {"avg_check": 25000, "revenue_mult": 1.4},
        "художники": {"avg_check": 15000, "revenue_mult": 1.3},
        "фитнес": {"avg_check": 3000, "revenue_mult": 2.0},
    }
    
    metrics = niche_metrics.get(niche, {"avg_check": 10000, "revenue_mult": 1.5})
    
    followers = data.get("followers", 1000)
    monthly_views = max(int(followers * 0.3 * 4), 1000)
    clicked = int(monthly_views * 0.04)
    converted = int(clicked * 0.05)
    revenue = converted * metrics["avg_check"]
    
    return {
        "monthly_views": monthly_views,
        "potential_revenue": int(revenue * metrics["revenue_mult"]),
        "conversion": f"{(converted / monthly_views * 100):.1f}%" if monthly_views > 0 else "0%",
    }

def save_to_sheets(username: str, niche: str, metrics: Dict) -> bool:
    """Записывает в Sheets"""
    try:
        creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(NEW_SHEETS_ID)
        
        try:
            ws = sheet.worksheet("Funnel Analysis")
        except:
            ws = sheet.add_worksheet("Funnel Analysis", 1000, 10)
            ws.append_row(["Дата", "Ник", "Ниша", "Instagram", "Telegram", "PDF", "Сообщение", "Статус", "Ответил", "Потенциал"])
        
        variant = random.choice(["A", "B", "C"])
        
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d"),
            f"@{username}",
            niche,
            f"https://instagram.com/{username}",
            "",
            "",
            f"Вариант {variant}",
            "pending",
            "",
            f"₽{metrics.get('potential_revenue', 0):,}"
        ])
        return True
    except:
        return False

async def analyze_funnels(usernames: List[str], category_filter: Optional[str] = None) -> str:
    """Основная функция"""
    if not usernames:
        return "❌ Укажи никнеймы"
    
    results = []
    errors = 0
    
    for i, username in enumerate(usernames, 1):
        try:
            data = collect_instagram_data(username)
            if not data:
                errors += 1
                continue
            
            niche = detect_niche(data)
            
            if category_filter and category_filter.lower() not in niche.lower():
                continue
            
            metrics = calculate_metrics(data, niche)
            save_to_sheets(username, niche, metrics)
            
            results.append((username, niche, metrics.get("potential_revenue", 0)))
            
        except Exception as e:
            errors += 1
        
        await asyncio.sleep(0.2)
    
    output = f"✅ **Анализ завершён ({len(results)}/{len(usernames)})**\n\n"
    
    if results:
        output += "**Топ по потенциалу:**\n"
        for username, niche, revenue in sorted(results, key=lambda x: x[2], reverse=True)[:10]:
            output += f"• @{username} ({niche}) — ₽{revenue:,}/мес\n"
    
    output += f"\n📊 Всего проанализировано: {len(results)}\n"
    output += f"❌ Ошибок: {errors}\n"
    output += "✅ Результаты в Google Sheets"
    
    return output
