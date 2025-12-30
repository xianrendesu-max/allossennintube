from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import requests
import random
import os
import time
from datetime import datetime

app = FastAPI()

# ===============================
# Static
# ===============================
if os.path.isdir("statics"):
    app.mount("/static", StaticFiles(directory="statics"), name="static")
else:
    print("⚠ statics directory not found (skipped mount)")

@app.get("/")
def root():
    if os.path.isfile("statics/index.html"):
        return FileResponse("statics/index.html")
    return {"status": "index.html not found"}

# ===============================
# Invidious API lists（総当たり）
# ===============================
INVIDIOUS_APIS = {
    "video": [
        "https://iv.melmac.space",
        "https://pol1.iv.ggtyler.dev",
        "https://cal1.iv.ggtyler.dev",
        "https://invidious.0011.lt",
        "https://yt.omada.cafe",
        "https://super8.absturztau.be",
        "https://invidious.ducks.party",
        "https://invidious.lunivers.trade",
        "https://invidious.nikkosphere.com",
        "https://lekker.gay",
        "https://34.97.38.181",
    ],
    "search": [
        "https://super8.absturztau.be",
        "https://invidious.ducks.party",
        "https://invidious.lunivers.trade",
        "https://invidious.nikkosphere.com",
        "https://iv.melmac.space",
        "https://lekker.gay",
        "https://cal1.iv.ggtyler.dev",
        "https://34.97.38.181",
        "https://rust.oskamp.nl",
        "https://pol1.iv.ggtyler.dev",
        "https://invidious.adminforge.de",
        "https://youtube.alt.tyil.nl",
    ],
    "channel": [
        "https://super8.absturztau.be",
        "https://invidious.ducks.party",
        "https://invidious.lunivers.trade",
        "https://invidious.nikkosphere.com",
        "https://iv.melmac.space",
        "https://lekker.gay",
        "https://cal1.iv.ggtyler.dev",
        "https://34.97.38.181",
        "https://youtube.alt.tyil.nl",
        "https://rust.oskamp.nl",
    ],
    "playlist": [
        "https://pol1.iv.ggtyler.dev",
        "https://invidious.lunivers.trade",
        "https://cal1.iv.ggtyler.dev",
        "https://nyc1.iv.ggtyler.dev",
        "https://iv.ggtyler.dev",
        "https://siawaseok-wakame-server2.glitch.me",
        "https://invidious.0011.lt",
        "https://invidious.nietzospannend.nl",
        "https://youtube.mosesmang.com",
        "https://iv.melmac.space",
        "https://lekker.gay",
    ],
    "comments": [
        "https://iv.ggtyler.dev",
        "https://cal1.iv.ggtyler.dev",
        "https://pol1.iv.ggtyler.dev",
        "https://invidious.nietzospannend.nl",
        "https://lekker.gay",
        "https://super8.absturztau.be",
        "https://invidious.ducks.party",
        "https://invidious.lunivers.trade",
    ],
}

TIMEOUT = 6
HEADERS = {"User-Agent": "Mozilla/5.0"}

EDU_STREAM_API_BASE_URL = "https://raw.githubusercontent.com/toka-kun/Education/refs/heads/main/keys/key1.json"
STREAM_YTDL_API_BASE_URL = "https://yudlp.vercel.app/stream/"

# ===============================
# Utils
# ===============================
def try_json(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("request error:", url, e)
    return None

# ===============================
# Search（総当たり）
# ===============================
@app.get("/api/search")
def api_search(q: str):
    apis = INVIDIOUS_APIS["search"].copy()
    random.shuffle(apis)

    for base in apis:
        data = try_json(f"{base}/api/v1/search", {"q": q, "type": "video"})
        if isinstance(data, list) and data:
            return {
                "source": base,
                "results": [
                    {
                        "videoId": v.get("videoId"),
                        "title": v.get("title"),
                        "author": v.get("author"),
                        "authorId": v.get("authorId"),
                    }
                    for v in data if v.get("videoId")
                ]
            }

    raise HTTPException(status_code=503, detail="Search unavailable")

# ===============================
# Video Info（総当たり）
# ===============================
@app.get("/api/video")
def api_video(video_id: str):
    apis = INVIDIOUS_APIS["video"].copy()
    random.shuffle(apis)

    for base in apis:
        data = try_json(f"{base}/api/v1/videos/{video_id}")
        if data:
            return {
                "source": base,
                "title": data.get("title"),
                "author": data.get("author"),
                "description": data.get("description"),
                "viewCount": data.get("viewCount"),
                "lengthSeconds": data.get("lengthSeconds"),
            }

    raise HTTPException(status_code=503, detail="Video info unavailable")

# ===============================
# Channel（完全版・修整済）
# ===============================
@app.get("/api/channel")
def api_channel(c: str):
    random.shuffle(VIDEO_APIS)

    for base in VIDEO_APIS:
        ch = try_json(f"{base}/api/v1/channels/{c}")
        if not ch:
            continue

        latest_videos = []

        for v in ch.get("latestVideos", []):
            published_raw = v.get("published")
            published_iso = None

            if isinstance(published_raw, str):
                try:
                    published_iso = published_raw.replace("Z", "+00:00")
                except:
                    published_iso = None

            latest_videos.append({
                "videoId": v.get("videoId"),
                "title": v.get("title"),
                "author": ch.get("author"),
                "authorId": c,
                "viewCount": v.get("viewCount") or 0,
                "viewCountText": v.get("viewCountText") or "0 回視聴",
                "published": published_iso,
                "publishedText": v.get("publishedText") or ""
            })

        view_count = ch.get("viewCount")
        video_count = ch.get("videoCount")
        joined_date = ch.get("joinedDate")

        if not isinstance(video_count, int):
            video_count = len(latest_videos)

        if not isinstance(joined_date, str):
            published_dates = [
                v["published"]
                for v in latest_videos
                if isinstance(v.get("published"), str)
            ]
            joined_date = min(published_dates) if published_dates else None

        related_channels = []

        for r in ch.get("relatedChannels", []):
            icon = None
            thumbs = r.get("authorThumbnails")

            if isinstance(thumbs, list) and thumbs:
                icon = thumbs[-1].get("url")

            related_channels.append({
                "channelId": r.get("authorId"),
                "name": r.get("author"),
                "icon": icon,
                "subCountText": r.get("subCountText") or "?"
            })

        return {
            "author": ch.get("author"),
            "authorId": c,
            "authorThumbnails": ch.get("authorThumbnails"),
            "description": ch.get("description") or "",
            "subCount": ch.get("subCount") or 0,
            "viewCount": view_count or 0,
            "videoCount": video_count,
            "joinedDate": joined_date,
            "latestVideos": latest_videos,
            "relatedChannels": related_channels,
            "source": base
        }

    raise HTTPException(status_code=503, detail="Channel unavailable")

# ===============================
# Comments（総当たり）
# ===============================
@app.get("/api/comments")
def api_comments(video_id: str):
    apis = INVIDIOUS_APIS["comments"].copy()
    random.shuffle(apis)

    for base in apis:
        data = try_json(f"{base}/api/v1/comments/{video_id}")
        if data:
            return {
                "source": base,
                "comments": [
                    {"author": c.get("author"), "content": c.get("content")}
                    for c in data.get("comments", [])
                ]
            }

    return {"comments": [], "source": None}

# ===============================
# Stream helpers（iPad対応）
# ===============================
def get_m3u8_from_yudlp(video_id: str):
    try:
        r = requests.get(
            f"https://yudlp.vercel.app/m3u8/{video_id}",
            headers=HEADERS,
            timeout=TIMEOUT
        )
        data = r.json()
        formats = data.get("m3u8_formats", [])
        formats.sort(
            key=lambda f: int((f.get("resolution") or "0x0").split("x")[-1]),
            reverse=True
        )
        return formats[0]["url"] if formats else None
    except:
        return None

def get_itag18_mp4(video_id: str):
    try:
        r = requests.get(
            f"{STREAM_YTDL_API_BASE_URL}{video_id}",
            headers=HEADERS,
            timeout=TIMEOUT
        )
        for f in r.json().get("formats", []):
            if str(f.get("itag")) == "18" and f.get("url"):
                return f["url"]
    except:
        pass
    return None

# ===============================
# Stream URL（総当たり）
# ===============================
@app.get("/api/streamurl")
def api_streamurl(video_id: str):
    m3u8 = get_m3u8_from_yudlp(video_id)
    if m3u8:
        return RedirectResponse(m3u8)

    mp4 = get_itag18_mp4(video_id)
    if mp4:
        return RedirectResponse(mp4)

    apis = INVIDIOUS_APIS["video"].copy()
    random.shuffle(apis)

    for base in apis:
        data = try_json(f"{base}/api/v1/videos/{video_id}")
        if data:
            for f in data.get("formatStreams", []):
                if f.get("url"):
                    return RedirectResponse(f["url"])

    raise HTTPException(status_code=503, detail="Stream unavailable")

# ===============================
# Status Monitor（全API監視）
# ===============================
@app.get("/api/status")
def api_status():
    results = []

    for category, urls in INVIDIOUS_APIS.items():
        for base in urls:
            url = f"{base}/api/v1/trending"
            start = time.time()
            ok = False
            status = None
            try:
                r = requests.get(url, headers=HEADERS, timeout=5)
                status = r.status_code
                ok = r.status_code == 200
            except:
                pass

            results.append({
                "category": category,
                "url": url,
                "ok": ok,
                "status": status,
                "latency_ms": round((time.time() - start) * 1000),
                "checked_at": datetime.utcnow().isoformat() + "Z"
            })

    return {"count": len(results), "results": results}
