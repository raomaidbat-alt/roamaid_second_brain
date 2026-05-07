"""funnel_analyzer - анализ с расширенной фильтрацией"""

import asyncio
import logging

logger = logging.getLogger("funnel_analyzer")

# Расширенный список категорий
NICHE_KEYWORDS = {
    "юристы": ["юрист", "закон", "адвокат", "консультация", "право"],
    "маркетологи": ["маркетинг", "рост", "продажи", "smm", "growth", "реклама"],
    "психологи": ["психолог", "терапия", "консультация", "психология", "коучинг"],
    "дизайнеры": ["дизайн", "дизайнер", "ui", "ux", "графика"],
    "художники": ["художник", "арт", "искусство", "живопись", "рисунок"],
    "фитнес": ["фитнес", "тренер", "спорт", "тренировка", "gym", "fitness"],
    "красота": ["косметолог", "красота", "салон", "макияж", "мастер"],
    "недвижимость": ["риэлтор", "недвижимость", "квартира", "агент"],
    "нутрициологи": ["нутрициолог", "питание", "диета", "нутрициология"],
    "фотографы": ["фотограф", "фотография", "съемка", "фото"],
    "блогеры": ["блогер", "контент", "инфлюенсер", "блог"],
    "бизнес": ["бизнес", "предприниматель", "стартап", "инвестор"],
    "it": ["программист", "разработчик", "developer", "it", "tech"],
    "образование": ["преподаватель", "учитель", "образование", "курсы", "обучение"],
}

def detect_niche(bio: str) -> str:
    """Определяет нишу"""
    bio_lower = bio.lower()
    
    scores = {}
    for niche, keywords in NICHE_KEYWORDS.items():
        scores[niche] = sum(bio_lower.count(kw) for kw in keywords)
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "другое"

async def analyze_funnels(usernames, category_filter=None):
    """Анализ с фильтрацией"""
    if not usernames:
        return "❌ Укажи никнеймы"
    
    output = f"🔍 **Анализ {len(usernames)} профилей**\n"
    if category_filter:
        output += f"Фильтр: **{category_filter}**\n\n"
    else:
        output += "\n"
    
    results = []
    filtered_out = []
    
    for username in usernames:
        # ВРЕМЕННО: генерация случайной ниши
        # В реальности здесь будет API запрос к Instagram
        import random
        niche = random.choice(list(NICHE_KEYWORDS.keys()) + ["другое", "другое"])
        
        # Фильтрация
        if category_filter:
            # Проверяем вхождение (category_filter может быть часть слова)
            if category_filter.lower() not in niche.lower():
                filtered_out.append(f"@{username} ({niche})")
                continue
        
        revenue = random.randint(10000, 150000)
        results.append((username, niche, revenue))
    
    if results:
        output += "✅ **Результаты:**\n"
        for username, niche, revenue in sorted(results, key=lambda x: x[2], reverse=True):
            output += f"• @{username} ({niche}) — ₽{revenue:,}/мес\n"
    else:
        output += "❌ **Никто не подошёл под фильтр**\n"
    
    if filtered_out:
        output += f"\n⏭️ **Отфильтровано ({len(filtered_out)}):**\n"
        for item in filtered_out[:5]:
            output += f"• {item}\n"
        if len(filtered_out) > 5:
            output += f"...и ещё {len(filtered_out)-5}\n"
    
    output += f"\n📊 Найдено: {len(results)}/{len(usernames)}"
    
    # Показать доступные категории если нет совпадений
    if category_filter and not results:
        output += f"\n\n💡 **Доступные категории:**\n"
        output += ", ".join(sorted(NICHE_KEYWORDS.keys()))
    
    return output
