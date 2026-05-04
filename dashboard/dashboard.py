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
MODEL = 'claude-sonnet-4-6'

app = FastAPI(title='Roman Ops Dashboard')
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.filters['tojson'] = lambda v: Markup(json.dumps(v, ensure_ascii=False))


# ── helpers ──────────────────────────────────────────────────────────────────

def ensure_files() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    for path in [POSTS_DATA, CONTACTS_FILE, FUNNELS_FILE, GENERATED_THREADS, AI_CACHE]:
        if not path.exists():
            path.write_text('{}' if path == AI_CACHE else '[]', encoding='utf-8')


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


def analyze_thread_patterns(threads: List[Dict]) -> str:
    top = sorted([t for t in threads if t.get('er', 0) > 0],
                 key=lambda x: x.get('er', 0), reverse=True)[:8]
    if not top:
        return 'Нет тредов с метриками для анализа.'
    prompt = ('Проанализируй, что общего у топ-тредов по engagement rate. '
              'Выдели 5 паттернов и 5 конкретных рекомендаций.\n\n'
              + json.dumps(top, ensure_ascii=False)[:6000])
    return ai_cached('thread_patterns', prompt, ttl=1800)


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
def create_thread(topic: str = Form(...), tone: str = Form('экспертный')):
    prompt = (
        'Создай Threads-тред на русском. Тема: %s. Тон: %s.\n'
        'Структура: сильный хук (первое сообщение должно цеплять с первых слов), '
        '6-9 коротких постов раскрывающих тему, финальный CTA.\n'
        'Разделяй посты строкой ---\nБез воды. Только конкретика.'
    ) % (topic, tone)
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
    conclusions = 'Добавь ссылки на посты, чтобы получить AI-анализ.'
    if posts:
        prompt = ('Проанализируй эти Instagram/Threads посты: что зашло лучше и почему? '
                  'Дай конкретные выводы и 5 рекомендаций.\n'
                  + json.dumps(posts[-30:], ensure_ascii=False)[:6000])
        conclusions = ai_cached('analytics_conclusions', prompt, ttl=900)
    return templates.TemplateResponse('analytics.html', {
        'request': request, 'posts': posts, 'conclusions': conclusions, 'active': 'analytics',
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
    uvicorn.run(app, host='0.0.0.0', port=8080, reload=False, log_level='info')
