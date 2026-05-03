import asyncio
import os
import re
import json
import requests as _requests
from datetime import datetime

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

THREADS_USERNAME = os.getenv("THREADS_USERNAME", "")
THREADS_PASSWORD = os.getenv("THREADS_PASSWORD", "")


def _gemini(prompt: str) -> str:
    for attempt in range(3):
        try:
            resp = _requests.post(
                _GEMINI_URL,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=90,
            )
            if resp.status_code == 429:
                import time; time.sleep(30)
                continue
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            if attempt == 2:
                raise
            import time; time.sleep(10)


def _parse_input(text: str) -> tuple:
    """Returns (mode, value): mode = 'post' | 'user', value = url or username"""
    text = text.strip()
    # Threads post URL: threads.net/@user/post/CODE
    if re.search(r'threads\.net/@[\w.]+/post/', text):
        return 'post', text
    # Profile URL: threads.net/@user
    if re.search(r'threads\.net/@([\w.]+)', text):
        m = re.search(r'threads\.net/@([\w.]+)', text)
        return 'user', m.group(1)
    # @username or plain username
    username = text.lstrip('@')
    return 'user', username


def _extract_post_data(post) -> dict:
    """Extract useful fields from a Post object"""
    caption_text = ""
    if post.caption:
        caption_text = post.caption.text or ""

    username = ""
    followers = 0
    if post.user:
        username = post.user.username or ""
        followers = post.user.follower_count or 0

    like_count = post.like_count or 0
    reply_count = 0
    repost_count = 0
    if post.text_post_app_info:
        reply_count = post.text_post_app_info.direct_reply_count or 0
        if post.text_post_app_info.share_info:
            pass  # repost data not directly available in count

    post_id = post.pk
    post_code = post.code or ""

    return {
        "id": str(post_id) if post_id else "",
        "code": post_code,
        "url": f"https://www.threads.net/@{username}/post/{post_code}" if post_code else "",
        "text": caption_text,
        "likes": like_count,
        "replies": reply_count,
        "author": username,
        "followers": followers,
    }


async def _get_top_posts(api, username: str, count: int = 15) -> list:
    """Get user's recent posts, sorted by likes"""
    user_id = await api.get_user_id_from_username(username)
    threads_data = await api.get_user_threads(user_id, count=count)

    posts = []
    for thread in (threads_data.threads or []):
        for item in (thread.thread_items or []):
            if item.post and not (item.post.text_post_app_info and item.post.text_post_app_info.is_reply):
                posts.append(_extract_post_data(item.post))

    posts.sort(key=lambda x: x["likes"], reverse=True)
    return posts[:5]


async def _get_single_post(api, url: str) -> dict:
    """Get a specific post by URL"""
    post_id = await api.get_post_id_from_url(url)
    replies_data = await api.get_post(str(post_id))

    if replies_data.containing_thread:
        thread = replies_data.containing_thread
        if thread.thread_items:
            return _extract_post_data(thread.thread_items[0].post)
    return {}


def _build_analysis_prompt(posts: list, mode: str) -> str:
    if mode == 'post':
        post = posts[0]
        context = f"""Пост от @{post['author']} (подписчики: {post['followers']:,}):
Текст: {post['text']}
Лайки: {post['likes']} | Ответы: {post['replies']}"""
    else:
        lines = []
        for i, p in enumerate(posts, 1):
            lines.append(f"{i}. Лайки: {p['likes']} | Ответы: {p['replies']}\n   Текст: {p['text'][:300]}")
        context = f"Топ постов @{posts[0]['author']} (подписчики: {posts[0]['followers']:,}):\n\n" + "\n\n".join(lines)

    return f"""Ты эксперт по контент-маркетингу и психологии вирального контента.

{context}

Проанализируй {'этот пост' if mode == 'post' else 'эти посты'} и ответь СТРОГО в этом формате без markdown, звёздочек, решёток:

КРЮЧОК: [тип крючка — ПАРАДОКС/ЦИФРЫ/БОЛЬ/ИСТОРИЯ/ПРОВОКАЦИЯ + 1 предложение почему работает]

ПСИХОЛОГИЯ: [какой триггер задействован — любопытство/страх/зависть/вдохновение/юмор + объяснение]

СТРУКТУРА: [из чего состоит пост — начало/середина/конец]

ПОЧЕМУ ЗАЛЕТЕЛ: [3 конкретные причины через —]

АДАПТАЦИЯ ДЛЯ НАШЕЙ НИШИ:
[Готовый тред 5-7 постов в том же стиле, но про маркетинг в соцсетях и рост аккаунтов.
Посты разделяй через ---
Первый пост должен содержать мощный крючок. Последний — CTA с упоминанием t.me/+H1I_MHFuv603ZTdi]

Только текст, никаких символов форматирования."""


async def analyze_threads(input_text: str) -> str:
    """Main function — analyze Threads post or account"""
    if not THREADS_USERNAME or not THREADS_PASSWORD:
        return "❌ Не настроены THREADS_USERNAME / THREADS_PASSWORD в .env"

    from threads_api.src.threads_api import ThreadsAPI

    api = ThreadsAPI()
    try:
        await api.login(THREADS_USERNAME, THREADS_PASSWORD, cached_token_path="/tmp/.threads_session.json")

        mode, value = _parse_input(input_text)

        if mode == 'post':
            post = await _get_single_post(api, value)
            if not post:
                return "❌ Не удалось получить данные поста"
            posts = [post]
            subject = f"пост {value}"
        else:
            posts = await _get_top_posts(api, value)
            if not posts:
                return f"❌ Не найдены посты у @{value}"
            subject = f"топ постов @{value}"

        prompt = _build_analysis_prompt(posts, mode)
        analysis = _gemini(prompt)

        header = f"🧵 Анализ: {subject}\n{'─' * 30}\n\n"
        return header + analysis

    finally:
        await api.close_gracefully()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python skill.py <threads_url_or_@username>")
        sys.exit(1)
    result = asyncio.run(analyze_threads(sys.argv[1]))
    print(result)
