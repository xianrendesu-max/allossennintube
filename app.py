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
# Render で statics が無くても即死しない
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
# API BASE LIST
# ===============================
VIDEO_APIS = [
    "https://iv.melmac.space",
    "https://pol1.iv.ggtyler.dev",
    "https://cal1.iv.ggtyler.dev",
    "https://invidious.0011.lt",
    "https://yt.omada.cafe",
]

SEARCH_APIS = VIDEO_APIS

COMMENTS_APIS = [
    "https://invidious.lunivers.trade",
    "https://invidious.ducks.party",
    "https://super8.absturztau.be",
    "https://invidious.nikkosphere.com",
    "https://yt.omada.cafe",
    "https://iv.melmac.space",
    "https://iv.duti.dev",
]

EDU_STREAM_API_BASE_URL = "https://raw.githubusercontent.com/toka-kun/Education/refs/heads/main/keys/key1.json"
STREAM_YTDL_API_BASE_URL = "https://yudlp.vercel.app/stream/"
SHORT_STREAM_API_BASE_URL = "https://yt-dl-kappa.vercel.app/short/"

TIMEOUT = 6

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ===============================
# Status Targets
# ===============================
STATUS_TARGETS = {
    "invidious": [
        "https://iv.melmac.space/api/v1/trending",
        "https://pol1.iv.ggtyler.dev/api/v1/trending",
        "https://invidious.0011.lt/api/v1/trending",
        "https://yt.omada.cafe/api/v1/trending",
    ],
    "stream": [
        "https://yudlp.vercel.app/stream/dQw4w9WgXcQ",
        "https://yudlp.vercel.app/m3u8/dQw4w9WgXcQ",
    ],
    "education": [
        "https://raw.githubusercontent.com/toka-kun/Education/refs/heads/main/keys/key1.json"
    ]
}

# ===============================
# Utils
# ===============================
def try_json(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("request error:", e)
    return None

# ===============================
# Search
# ===============================
@app.get("/api/search")
def api_search(q: str):
    results = []
    random.shuffle(SEARCH_APIS)

    for base in SEARCH_APIS:
        data = try_json(f"{base}/api/v1/search", {"q": q, "type": "video"})
        if not isinstance(data, list):
            continue

        for v in data:
            if not v.get("videoId"):
                continue

            results.append({
                "videoId": v.get("videoId"),
                "title": v.get("title"),
                "author": v.get("author"),
                "authorId": v.get("authorId"),
            })

        if results:
            return {
                "count": len(results),
                "results": results,
                "source": base
            }

    raise HTTPException(status_code=503, detail="Search unavailable")

# ===============================
# Video Info
# ===============================
@app.get("/api/video")
def api_video(video_id: str):
    random.shuffle(VIDEO_APIS)

    for base in VIDEO_APIS:
        data = try_json(f"{base}/api/v1/videos/{video_id}")
        if data:
            return {
                "title": data.get("title"),
                "author": data.get("author"),
                "description": data.get("description"),
                "viewCount": data.get("viewCount"),
                "lengthSeconds": data.get("lengthSeconds"),
                "source": base
            }

    raise HTTPException(status_code=503, detail="Video info unavailable")

# ===============================
# Comments
# ===============================
@app.get("/api/comments")
def api_comments(video_id: str):
    for base in COMMENTS_APIS:
        data = try_json(f"{base}/api/v1/comments/{video_id}")
        if data:
            return {
                "comments": [
                    {
                        "author": c.get("author"),
                        "content": c.get("content")
                    }
                    for c in data.get("comments", [])
                ],
                "source": base
            }
    return {"comments": [], "source": None}

# ===============================
# Channel
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
                published_iso = published_raw.replace("Z", "+00:00")

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

        return {
            "author": ch.get("author"),
            "authorId": c,
            "authorThumbnails": ch.get("authorThumbnails"),
            "description": ch.get("description") or "",
            "subCount": ch.get("subCount") or 0,
            "latestVideos": latest_videos,
            "source": base
        }

    raise HTTPException(status_code=503, detail="Channel unavailable")

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
        if not formats:
            return None

        def height(f):
            try:
                return int((f.get("resolution") or "0x0").split("x")[-1])
            except:
                return 0

        formats.sort(key=height, reverse=True)
        return formats[0].get("url")
    except:
        return None

def get_itag18_mp4(video_id: str):
    try:
        r = requests.get(
            f"{STREAM_YTDL_API_BASE_URL}{video_id}",
            headers=HEADERS,
            timeout=TIMEOUT
        )
        data = r.json()

        for f in data.get("formats", []):
            if str(f.get("itag")) == "18" and f.get("url"):
                return f["url"]
    except:
        pass
    return None

# ===============================
# Stream URL ONLY（iPad完全対応）
# ===============================
@app.get("/api/streamurl")
def api_streamurl(video_id: str):
    # ① HLS（iPad最優先）
    m3u8 = get_m3u8_from_yudlp(video_id)
    if m3u8:
        return RedirectResponse(m3u8)

    # ② MP4（itag18）
    mp4 = get_itag18_mp4(video_id)
    if mp4:
        return RedirectResponse(mp4)

    # ③ Invidious muxed
    for base in VIDEO_APIS:
        data = try_json(f"{base}/api/v1/videos/{video_id}")
        if not data:
            continue

        for f in data.get("formatStreams", []):
            if f.get("url"):
                return RedirectResponse(f["url"])

    raise HTTPException(status_code=503, detail="Stream unavailable")

# ===============================
# Status Monitor
# ===============================
@app.get("/api/status")
def api_status():
    results = []

    for category, urls in STATUS_TARGETS.items():
        for url in urls:
            start = time.time()
            ok = False
            status = None

            try:
                r = requests.get(url, headers=HEADERS, timeout=5)
                status = r.status_code
                if r.status_code == 200:
                    ok = True
            except Exception as e:
                print("status check error:", url, e)

            elapsed = round((time.time() - start) * 1000)

            results.append({
                "category": category,
                "url": url,
                "ok": ok,
                "status": status,
                "latency_ms": elapsed,
                "checked_at": datetime.utcnow().isoformat() + "Z"
            })

    return {
        "count": len(results),
        "results": results
                         }
