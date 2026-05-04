#!/usr/bin/env python3
import json
import os
import re
import subprocess
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None

BASE_DIR = Path('/root/dashboard')
TEMPLATE_DIR = BASE_DIR / 'templates'
DAILY_LOG = Path('/root/daily_log.md')
BRAIN_DIR = Path('/root/brain')
POSTS_DATA = BASE_DIR / 'posts_data.json'
CONTACTS_FILE = Path('/root/outreach/contacts.json')
FUNNELS_FILE = Path('/root/outreach/funnel_analyses.json')
GENERATED_THREADS = BASE_DIR / 'generated_threads.json'
AI_CACHE = BASE_DIR / '_ai_cache.json'
PROFILE_INSIGHTS = BASE_DIR / 'profile_insights.json'
SOCIAL_ANALYZER_PROFILE = os.getenv('SOCIAL_ANALYZER_PROFILE', 'http://150.241.116.28:8000/profile')
ROMAN_CHANNEL = 'https://t.me/+H1I_MHFuv603ZTdi'
MODEL = 'claude-sonnet-4-6'

app = FastAPI(title='Roman Ops Dashboard')
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.filters['tojson'] = lambda v: Markup(json.dumps(v, ensure_ascii=False))


# ── helpers ──────────────────────────────────────────────────────────────────

def ensure_files() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    for path in [POSTS_DATA, CONTACTS_FILE, FUNNELS_FILE, GENERATED_THREADS, AI_CACHE, PROFILE_INSIGHTS]:
        if not path.exists():
            path.write_text('{}' if path in (AI_CACHE, PROFILE_INSIGHTS) else '[]', encoding='utf-8')


def read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        text = path.read_text(encoding='utf-8').strip()
        return json.loads(text) if text else default
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def ai_cached(key: str, prompt: str, max_tokens: int = 1200, ttl: int = 3600) -> str:
    cache = read_json(AI_CACHE, {})
    entry = cache.get(key, {})
    if entry and datetime.now().timestamp() < entry.get('expires', 0):
        return entry['value']
    result = ai_call(prompt, max_tokens)
    cache[key] = {'value': result, 'expires': datetime.now().timestamp() + ttl}
    write_json(AI_CACHE, cache)
    return result


def invalidate_cache(key: str) -> None:
    cache = read_json(AI_CACHE, {})
    cache.pop(key, None)
    write_json(AI_CACHE, cache)


# ── pm2 ──────────────────────────────────────────────────────────────────────

def pm2_status() -> List[Dict[str, Any]]:
    try:
        raw = subprocess.check_output(['pm2', 'jlist'], stderr=subprocess.STDOUT, timeout=8)
        rows = json.loads(raw.decode('utf-8', 'replace'))
    except Exception:
        return [{'name': 'pm2', 'status': 'unavailable', 'pid': '-',
                 'restarts': '-', 'uptime': '-', 'memory': '-', 'cpu': '-'}]
    result = []
    for item in rows:
        env = item.get('pm2_env', {})
        mon = item.get('monit', {})
        uptime_ms = env.get('pm_uptime')
        uptime = '-'
        if uptime_ms:
            s = max(0, int((datetime.now().timestamp() * 1000 - uptime_ms) / 1000))
            uptime = '%dh %dm' % (s // 3600, (s % 3600) // 60)
        result.append({
            'name': item.get('name'),
            'status': env.get('status', 'unknown'),
            'pid': item.get('pid'),
            'restarts': env.get('restart_time', 0),
            'uptime': uptime,
            'memory': round(mon.get('memory', 0) / 1024 / 1024, 1),
            'cpu': mon.get('cpu', 0),
        })
    return result


# ── daily log ────────────────────────────────────────────────────────────────

def _get_today_block() -> str:
    if not DAILY_LOG.exists():
        return ''
    content = DAILY_LOG.read_text(encoding='utf-8', errors='replace')
    today = date.today().isoformat()
    idx = content.find(f'## {today}')
    if idx == -1:
        return ''
    block = content[idx:]
    nxt = block.find('\n## ', 4)
    return block[:nxt] if nxt != -1 else block


def today_stats() -> Dict[str, int]:
    block = _get_today_block()
    return {
        'accounts': len(re.findall(r'Проанализирован аккаунт', block)),
        'threads': len(re.findall(r'Сгенерирован тред', block)),
        'leads': len(re.findall(r'Новая заявка', block)),
        'audits': len(re.findall(r'Аудит завершён', block)),
        'sites': len(re.findall(r'Аудит сайта', block)),
    }


def last_events(n: int = 10) -> List[str]:
    block = _get_today_block()
    lines = [l.strip() for l in block.splitlines() if l.strip().startswith('-')]
    return lines[-n:]


# ── metrics helpers ───────────────────────────────────────────────────────────

def parse_number(text: str) -> int:
    if not text:
        return 0
    t = text.lower().replace(',', '.').replace(' ', '')
    m = re.search(r'(\d+(?:\.\d+)?)([kкmм]?)', t)
    if not m:
        return 0
    num = float(m.group(1))
    suf = m.group(2)
    if suf in ('k', 'к'):
        num *= 1000
    elif suf in ('m', 'м'):
        num *= 1_000_000
    return int(num)


def engagement_rate(views: int, likes: int, comments: int = 0, reposts: int = 0) -> float:
    return round((likes + comments + reposts) / views * 100, 2) if views else 0.0


def extract_metric(text: str, names: List[str]) -> int:
    for name in names:
        for pat in [
            r'%s\s*[:=\-]?\s*([\d\s.,]+[kкmм]?)' % re.escape(name),
            r'([\d\s.,]+[kкmм]?)\s*%s' % re.escape(name),
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return parse_number(m.group(1))
    return 0


# ── threads ──────────────────────────────────────────────────────────────────

def thread_files() -> List[Path]:
    if not BRAIN_DIR.exists():
        return []
    files = [p for p in BRAIN_DIR.rglob('*')
             if p.is_file() and p.suffix.lower() in ('.md', '.txt', '.json')]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:100]


def load_brain_threads() -> List[Dict[str, Any]]:
    result = []
    for path in thread_files():
        text = path.read_text(encoding='utf-8', errors='replace')
        views = extract_metric(text, ['views', 'view', 'просмотры', 'охваты', 'показы'])
        likes = extract_metric(text, ['likes', 'like', 'лайки', 'лайков'])
        reposts = extract_metric(text, ['reposts', 'repost', 'репосты', 'репостов', 'shares'])
        comments = extract_metric(text, ['comments', 'comment', 'комменты', 'комментарии'])
        title = next((l.strip('# -*') for l in text.splitlines() if l.strip()), path.name)
        result.append({
            'id': None,
            'source': 'brain',
            'path': str(path.relative_to(BRAIN_DIR)),
            'title': title[:140],
            'text': text[:2000],
            'views': views, 'likes': likes, 'comments': comments, 'reposts': reposts,
            'er': engagement_rate(views, likes, comments, reposts),
            'mtime': datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
        })
    return result


def load_threads() -> List[Dict[str, Any]]:
    generated = read_json(GENERATED_THREADS, [])
    enriched = []
    for item in generated:
        item.setdefault('id', str(uuid.uuid4()))
        item.setdefault('source', 'generated')
        item.setdefault('views', 0)
        item.setdefault('likes', 0)
        item.setdefault('comments', 0)
        item.setdefault('reposts', 0)
        item['er'] = engagement_rate(
            int(item.get('views') or 0), int(item.get('likes') or 0),
            int(item.get('comments') or 0), int(item.get('reposts') or 0),
        )
        enriched.append(item)
    return enriched + load_brain_threads()


# ── AI ───────────────────────────────────────────────────────────────────────

def ai_call(prompt: str, max_tokens: int = 1200) -> str:
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return 'AI недоступен: ANTHROPIC_API_KEY не задан.'
    if Anthropic is None:
        return 'AI недоступен: пакет anthropic не установлен.'
    try:
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=MODEL, max_tokens=max_tokens,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return '\n'.join(b.text for b in msg.content if getattr(b, 'type', '') == 'text').strip()
    except Exception as exc:
        return 'AI ошибка: %s' % exc




def adaptive_threads_rules(limit: int = 12) -> str:
    """Build lightweight prompt rules from what actually performs: views, likes, comments, ER."""
    posts = read_json(POSTS_DATA, [])
    profile = read_json(PROFILE_INSIGHTS, {})
    profile_posts = profile.get('top_posts') or []
    threads = read_json(GENERATED_THREADS, [])

    rows = []
    for p in posts:
        rows.append({
            'source': 'manual_metrics',
            'text': p.get('text') or p.get('caption') or p.get('url') or '',
            'views': int(p.get('views') or 0),
            'likes': int(p.get('likes') or 0),
            'comments': int(p.get('comments') or 0),
            'reposts': int(p.get('reposts') or 0),
            'er': float(p.get('er') or 0),
        })
    for p in profile_posts:
        rows.append({
            'source': 'instagram_profile_top',
            'text': p.get('caption') or '',
            'views': int(p.get('views') or 0),
            'likes': int(p.get('likes') or 0),
            'comments': int(p.get('comments') or 0),
            'reposts': 0,
            'er': float(p.get('er') or 0),
        })
    for t in threads:
        rows.append({
            'source': 'generated_thread',
            'text': (t.get('title') or '') + '\n' + (t.get('text') or '')[:800],
            'views': int(t.get('views') or 0),
            'likes': int(t.get('likes') or 0),
            'comments': int(t.get('comments') or 0),
            'reposts': int(t.get('reposts') or 0),
            'er': engagement_rate(int(t.get('views') or 0), int(t.get('likes') or 0), int(t.get('comments') or 0), int(t.get('reposts') or 0)),
        })

    rows = [r for r in rows if (r['views'] or r['likes'] or r['comments'] or r['er']) and r['text']]
    if not rows:
        return (
            'Пока мало метрик. Используй базовый Roman-style: история, контраст двух людей/бизнесов, живой конфликт клиента, честный вывод, CTA в канал. '
            'После появления просмотров/лайков/комментов промпт будет автоматически подстраиваться.'
        )

    def score(r):
        return r['views'] + r['likes'] * 25 + r['comments'] * 120 + r['reposts'] * 180 + int(r['er'] * 100)
    top = sorted(rows, key=score, reverse=True)[:limit]

    prompt = (
        'Ты агент адаптации промптов для Threads Романа. По этим постам/тредам с метриками определи, что реально заходит аудитории. '
        'Верни короткие правила для следующего промпта: какие хуки повторять, какие темы усиливать, какой конфликт аудитории использовать, чего избегать. '
        'Пиши как внутреннюю инструкцию для генератора, без воды. Учитывай, что Роман хочет стиль: человек рассказывает историю, длинно и понятно, триггерно, не учительски.\n\n'
        + json.dumps(top, ensure_ascii=False)[:9000]
    )
    ai = ai_cached('adaptive_threads_rules_' + str(abs(hash(json.dumps(top, ensure_ascii=False))) % 1000000), prompt, max_tokens=1400, ttl=1800)
    if not ai.startswith('AI недоступен') and not ai.startswith('AI ошибка'):
        return ai

    examples = '\n'.join([f"- [{r['source']}] views={r['views']} likes={r['likes']} comments={r['comments']} ER={r['er']}%: {short_caption(r['text'], 220)}" for r in top[:8]])
    return (
        'AI-адаптация временно недоступна, но генератор должен опираться на лучшие по метрикам материалы ниже. '
        'Повторять темы/хуки из верхних строк, сильнее использовать живую боль клиента, не писать сухие инструкции.\n' + examples
    )


def analyze_thread_patterns(threads: List[Dict]) -> str:
    top = sorted([t for t in threads if t.get('er', 0) > 0],
                 key=lambda x: x.get('er', 0), reverse=True)[:8]
    if not top:
        return 'Нет тредов с метриками для анализа.'
    prompt = ('Проанализируй, что общего у топ-тредов по engagement rate. '
              'Выдели 5 паттернов и 5 конкретных рекомендаций.\n\n'
              + json.dumps(top, ensure_ascii=False)[:6000])
    return ai_cached('thread_patterns', prompt, ttl=1800)




# ── Instagram profile watcher / prompt agent ─────────────────────────────────

def normalize_instagram_username(value: str) -> str:
    value = (value or '').strip().lstrip('@')
    m = re.search(r'instagram\.com/([^/?#]+)', value)
    if m:
        value = m.group(1)
    return value.strip('/ ')


def fetch_instagram_profile(username: str) -> Dict[str, Any]:
    username = normalize_instagram_username(username)
    resp = requests.post(SOCIAL_ANALYZER_PROFILE, json={'username': username}, timeout=90)
    resp.raise_for_status()
    data = resp.json()
    data['username'] = username
    return data


def post_score(post: Dict[str, Any]) -> int:
    views = int(post.get('view_count') or post.get('play_count') or 0)
    likes = int(post.get('like_count') or 0)
    comments = int(post.get('comment_count') or 0)
    # comments usually signal stronger trigger than likes; views dominate for reach
    return views + likes * 20 + comments * 80


def short_caption(caption: str, limit: int = 180) -> str:
    text = re.sub(r'\s+', ' ', caption or '').strip()
    text = re.sub(r'#\w+', '', text).strip()
    return text[:limit].rstrip() + ('…' if len(text) > limit else '')


def top_profile_posts(profile: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
    rows = []
    for post in profile.get('posts') or []:
        views = int(post.get('view_count') or post.get('play_count') or 0)
        likes = int(post.get('like_count') or 0)
        comments = int(post.get('comment_count') or 0)
        rows.append({
            'type': post.get('type') or 'post',
            'url': post.get('url') or post.get('permalink') or '',
            'caption': short_caption(post.get('caption') or ''),
            'views': views,
            'likes': likes,
            'comments': comments,
            'published_at': (post.get('published_at') or '')[:10],
            'score': post_score(post),
            'er': engagement_rate(max(views, likes + comments), likes, comments, 0),
        })
    return sorted(rows, key=lambda x: x['score'], reverse=True)[:limit]


def build_prompt_agent(profile: Dict[str, Any], top_posts: List[Dict[str, Any]]) -> str:
    username = profile.get('username') or profile.get('handle') or ''
    bio = profile.get('bio') or ''
    facts = {
        'username': username,
        'followers': profile.get('follower_count'),
        'bio': bio,
        'top_posts': top_posts[:6],
        'roman_channel': ROMAN_CHANNEL,
    }
    prompt = (
        'Ты отдельный агент Романа по улучшению промптов для Threads. На основе фактов профиля и топ-постов '\
        'сформулируй: 1) какие темы уже цепляют, 2) какие боли аудитории повторять, 3) какие хуки тестировать, '\
        '4) какие 5 промптов использовать для новых тредов. Стиль: как человек, длинно и понятно, триггерно, через историю, не как учитель. '\
        f'Каждый CTA ведёт в канал: {ROMAN_CHANNEL}.\n\nФАКТЫ:\n' + json.dumps(facts, ensure_ascii=False)[:7000]
    )
    ai = ai_call(prompt, max_tokens=1800)
    if not ai.startswith('AI недоступен') and not ai.startswith('AI ошибка'):
        return ai
    themes = []
    for p in top_posts[:5]:
        if p.get('caption'):
            themes.append('— ' + p['caption'])
    return (
        f'Prompt-agent для @{username}\n\n'
        f'AI сейчас недоступен, поэтому даю рабочую эвристику по фактам профиля.\n\n'
        f'Что уже цепляет:\n' + ('\n'.join(themes) if themes else '— мало текста в последних постах, нужно добавить ссылки на конкретные ролики/метрики') + '\n\n'
        'Как писать треды дальше:\n'
        '1. Начинать не с обучения, а с истории: “знаю двух экспертов…” или “увидел ролик и понял неприятную вещь…”.\n'
        '2. Показывать контраст: один получает заявки, второй получает лайки и тишину.\n'
        '3. Не говорить “делайте боли”, а писать живую фразу клиента: “человек уже 3 курса купил и ему стыдно признаться, что опять ничего не внедрил”.\n'
        '4. В каждом треде оставлять одну мысль, а не 7 советов.\n'
        f'5. Финал всегда вести в канал: {ROMAN_CHANNEL}\n\n'
        'Промпт для генерации:\n'
        '“Напиши тред в стиле живой истории Романа: знаю двух [нишa], у одного очередь/заявки, у второго красивые посты и тишина. Покажи, что второй говорит правильные общие слова, но не называет настоящую боль клиента. Пиши длинно, понятно, триггерно, без учительского тона. В конце CTA в канал.”'
    )

# ── scraping ─────────────────────────────────────────────────────────────────

def scrape_url(url: str) -> Dict[str, Any]:
    headers = {'User-Agent': 'Mozilla/5.0 RomanDashboard/1.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    text = soup.get_text(' ', strip=True)
    og = soup.find('meta', property='og:title')
    title = (og.get('content') if og else None) or (soup.title.text.strip() if soup.title else '') or text[:200]
    views = extract_metric(text, ['views', 'просмотры', 'просмотров', 'охваты'])
    likes = extract_metric(text, ['likes', 'лайки', 'лайков'])
    comments = extract_metric(text, ['comments', 'комментарии', 'комментов'])
    reposts = extract_metric(text, ['reposts', 'shares', 'репосты'])
    return {
        'url': url, 'text': title[:300],
        'views': views, 'likes': likes, 'comments': comments, 'reposts': reposts,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'er': engagement_rate(views, likes, comments, reposts),
    }


# ── contact status ────────────────────────────────────────────────────────────

STATUS_CLASSES = {
    frozenset(['online', 'active', 'done', 'теплый', 'ответил']):
        'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    frozenset(['stopped', 'errored', 'error', 'blocked', 'нет ответа']):
        'bg-rose-500/20 text-rose-300 border-rose-500/30',
}


def status_class(status: str) -> str:
    s = (status or '').lower()
    for keys, cls in STATUS_CLASSES.items():
        if s in keys:
            return cls
    return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'


# ── routes ───────────────────────────────────────────────────────────────────

@app.get('/')
def home(request: Request):
    return templates.TemplateResponse('home.html', {
        'request': request,
        'pm2': pm2_status(),
        'stats': today_stats(),
        'events': last_events(12),
        'active': 'home',
    })


@app.get('/threads')
def threads_page(request: Request):
    threads = load_threads()
    return templates.TemplateResponse('threads.html', {
        'request': request,
        'threads': threads,
        'analysis': analyze_thread_patterns(threads),
        'active': 'threads',
    })


@app.post('/threads/create')
def create_thread(topic: str = Form(...), tone: str = Form('Roman story-selling')):
    profile_insights = read_json(PROFILE_INSIGHTS, {})
    prompt_agent = profile_insights.get('prompt_agent', '')
    adaptive_rules = adaptive_threads_rules()
    prompt = (
        'Создай Threads-тред на русском. Тема: %s. Тон: %s.\n'
        'Пиши как человек и как Роман: длинно и понятно, триггерно, без дробления каждой мысли на микропредложения, без учительского тона. '
        'Через историю: наблюдение → контраст → живой конфликт клиента → честный вывод → мягкий CTA. '
        'Хорошая механика: “знаю двух X”, у одного заявки/очередь, у второго красивые посты и тишина, потом показываем что второй говорит общие слова, но не называет настоящую боль клиента.\n'
        'ВАЖНО: промпт должен автоматически подстраиваться под то, что уже заходит аудитории по просмотрам, лайкам, комментариям и ER. Используй адаптивные правила ниже как приоритетнее общих советов.\n'
        'Разделяй посты строкой ---. Финал ОБЯЗАТЕЛЬНО ведёт в канал: %s\n\n'
        'АДАПТИВНЫЕ ПРАВИЛА ПО МЕТРИКАМ:\n%s\n\n'
        'Подсказки prompt-agent по профилю Романа, если есть:\n%s'
    ) % (topic, tone, ROMAN_CHANNEL, adaptive_rules[:5000], prompt_agent[:3000])
    content = ai_call(prompt, max_tokens=1800)
    rows = read_json(GENERATED_THREADS, [])
    rows.insert(0, {
        'id': str(uuid.uuid4()),
        'title': topic,
        'tone': tone,
        'text': content,
        'created_at': datetime.now().isoformat(timespec='seconds'),
    })
    write_json(GENERATED_THREADS, rows[:100])
    invalidate_cache('thread_patterns')
    return RedirectResponse('/threads', status_code=303)


@app.post('/threads/save')
def save_thread(thread_id: str = Form(...), text: str = Form(...)):
    rows = read_json(GENERATED_THREADS, [])
    for row in rows:
        if row.get('id') == thread_id:
            row['text'] = text
            row['updated_at'] = datetime.now().isoformat(timespec='seconds')
            break
    write_json(GENERATED_THREADS, rows)
    return RedirectResponse('/threads', status_code=303)


@app.post('/threads/delete')
def delete_thread(thread_id: str = Form(...)):
    rows = read_json(GENERATED_THREADS, [])
    rows = [r for r in rows if r.get('id') != thread_id]
    write_json(GENERATED_THREADS, rows)
    invalidate_cache('thread_patterns')
    return RedirectResponse('/threads', status_code=303)


@app.get('/analytics')
def analytics_page(request: Request):
    posts = read_json(POSTS_DATA, [])
    profile_insights = read_json(PROFILE_INSIGHTS, {})
    conclusions = 'Добавь ссылки на посты, чтобы получить AI-анализ.'
    if posts:
        prompt = ('Проанализируй эти Instagram/Threads посты: что зашло лучше и почему? '
                  'Дай конкретные выводы и 5 рекомендаций.\n'
                  + json.dumps(posts[-30:], ensure_ascii=False)[:6000])
        conclusions = ai_cached('analytics_conclusions', prompt, ttl=900)
    return templates.TemplateResponse('analytics.html', {
        'request': request, 'posts': posts, 'conclusions': conclusions,
        'profile_insights': profile_insights, 'roman_channel': ROMAN_CHANNEL,
        'active': 'analytics',
    })


@app.post('/analytics/parse')
def parse_analytics(url: str = Form(...)):
    posts = read_json(POSTS_DATA, [])
    try:
        item = scrape_url(url)
    except Exception as exc:
        item = {
            'url': url, 'text': 'Ошибка парсинга: %s' % exc,
            'views': 0, 'likes': 0, 'comments': 0, 'reposts': 0,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'), 'er': 0,
        }
    posts.insert(0, item)
    write_json(POSTS_DATA, posts[:500])
    invalidate_cache('analytics_conclusions')
    return RedirectResponse('/analytics', status_code=303)




@app.post('/analytics/profile')
def analyze_profile(username: str = Form(...)):
    profile = fetch_instagram_profile(username)
    top_posts = top_profile_posts(profile, limit=10)
    insights = {
        'username': normalize_instagram_username(username),
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'followers': profile.get('follower_count'),
        'bio': profile.get('bio') or '',
        'top_posts': top_posts,
        'prompt_agent': build_prompt_agent(profile, top_posts),
    }
    write_json(PROFILE_INSIGHTS, insights)
    invalidate_cache('analytics_conclusions')
    return RedirectResponse('/analytics', status_code=303)

@app.get('/funnels')
def funnels_page(request: Request):
    analyses = read_json(FUNNELS_FILE, [])
    return templates.TemplateResponse('funnels.html', {
        'request': request, 'analyses': analyses, 'active': 'funnels',
    })


@app.post('/funnels/analyze')
def analyze_funnel(funnel_text: str = Form(...)):
    prompt = (
        'Проанализируй воронку продаж по 5 этапам: Боль → Решение → Результат → Авторитет → Вход.\n'
        'Для КАЖДОГО этапа:\n'
        '• Оценка: X/10\n'
        '• Что есть в тексте\n'
        '• Что слабо / отсутствует\n'
        '• Конкретное улучшение\n\n'
        'В конце: итоговая оценка воронки и 3 приоритетных действия.\n\n'
        'ВОРОНКА:\n'
    ) + funnel_text
    analysis = ai_call(prompt, max_tokens=1800)
    rows = read_json(FUNNELS_FILE, [])
    rows.insert(0, {
        'id': str(uuid.uuid4()),
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'text': funnel_text,
        'analysis': analysis,
    })
    write_json(FUNNELS_FILE, rows[:200])
    return RedirectResponse('/funnels', status_code=303)


@app.get('/outreach')
def outreach_page(request: Request):
    contacts = read_json(CONTACTS_FILE, [])
    return templates.TemplateResponse('outreach.html', {
        'request': request, 'contacts': contacts,
        'status_class': status_class, 'active': 'outreach',
    })


@app.post('/outreach/add')
def add_contact(
    name: str = Form(...), handle: str = Form(''),
    status: str = Form('new'), notes: str = Form(''),
):
    contacts = read_json(CONTACTS_FILE, [])
    contacts.insert(0, {
        'id': str(uuid.uuid4()),
        'name': name, 'handle': handle, 'status': status, 'notes': notes,
        'created_at': datetime.now().isoformat(timespec='seconds'),
    })
    write_json(CONTACTS_FILE, contacts)
    return RedirectResponse('/outreach', status_code=303)


@app.post('/outreach/status')
def update_contact_status(contact_id: str = Form(...), status: str = Form(...)):
    contacts = read_json(CONTACTS_FILE, [])
    for c in contacts:
        if c.get('id') == contact_id:
            c['status'] = status
            c['updated_at'] = datetime.now().isoformat(timespec='seconds')
            break
    write_json(CONTACTS_FILE, contacts)
    return RedirectResponse('/outreach', status_code=303)


if __name__ == '__main__':
    ensure_files()
    uvicorn.run(app, host='0.0.0.0', port=8888, reload=False, log_level='info')
