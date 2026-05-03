import asyncio
import os
import re

THREADS_USERNAME = os.getenv("THREADS_USERNAME", "")
THREADS_PASSWORD = os.getenv("THREADS_PASSWORD", "")


async def post_to_threads(text: str, image_paths: list = None) -> dict:
    """
    Publish a post to Threads.
    Returns {"ok": True, "url": "...", "post_id": "..."} or {"ok": False, "error": "..."}
    """
    if not THREADS_USERNAME or not THREADS_PASSWORD:
        return {"ok": False, "error": "Не настроены THREADS_USERNAME / THREADS_PASSWORD в .env"}

    from threads_api.src.threads_api import ThreadsAPI

    api = ThreadsAPI()
    try:
        await api.login(
            THREADS_USERNAME,
            THREADS_PASSWORD,
            cached_token_path="/tmp/.threads_session.json",
        )

        if image_paths and len(image_paths) == 1:
            response = await api.post(caption=text, image_path=image_paths[0])
        elif image_paths and len(image_paths) > 1:
            response = await api.post(caption=text, image_path=image_paths)
        else:
            response = await api.post(caption=text)

        if response and response.status == "ok":
            post_code = ""
            post_id = ""
            if response.media:
                post_code = response.media.code or ""
                post_id = str(response.media.pk or "")

            url = f"https://www.threads.net/@{THREADS_USERNAME}/post/{post_code}" if post_code else ""
            return {"ok": True, "url": url, "post_id": post_id}
        else:
            return {"ok": False, "error": f"Threads вернул неожиданный ответ: {response}"}

    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        await api.close_gracefully()


async def post_thread_series(posts: list) -> dict:
    """
    Publish a thread series (multiple posts as replies to each other).
    posts: list of strings
    Returns {"ok": True, "urls": [...]} or {"ok": False, "error": "..."}
    """
    if not THREADS_USERNAME or not THREADS_PASSWORD:
        return {"ok": False, "error": "Не настроены THREADS_USERNAME / THREADS_PASSWORD в .env"}

    from threads_api.src.threads_api import ThreadsAPI

    api = ThreadsAPI()
    urls = []
    try:
        await api.login(
            THREADS_USERNAME,
            THREADS_PASSWORD,
            cached_token_path="/tmp/.threads_session.json",
        )

        parent_id = None
        for i, text in enumerate(posts):
            if parent_id:
                response = await api.post(caption=text, parent_post_id=parent_id)
            else:
                response = await api.post(caption=text)

            if not response or response.status != "ok":
                return {"ok": False, "error": f"Ошибка на посте {i+1}: {response}"}

            post_code = ""
            if response.media:
                parent_id = str(response.media.pk or "")
                post_code = response.media.code or ""

            url = f"https://www.threads.net/@{THREADS_USERNAME}/post/{post_code}" if post_code else ""
            urls.append(url)

            # Small pause between posts to avoid rate limiting
            if i < len(posts) - 1:
                await asyncio.sleep(2)

        return {"ok": True, "urls": urls}

    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        await api.close_gracefully()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python skill.py 'Post text here'")
        sys.exit(1)
    result = asyncio.run(post_to_threads(sys.argv[1]))
    print(result)
