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
# Base API lists（既存）
# ===============================
VIDEO_APIS = [
    "https://iv.melmac.space",
    "https://pol1.iv.ggtyler.dev",
    "https://cal1.iv.ggtyler.dev",
    "https://invidious.0011.lt",
    "https://yt.omada.cafe",
]

SEARCH_APIS = VIDEO_APIS.copy()

COMMENTS_APIS = [
    "https://invidious.lunivers.trade",
    "https://invidious.ducks.party",
    "https://super8.absturztau.be",
    "https://invidious.nikkosphere.com",
    "https://yt.omada.cafe",
    "https://iv.melmac.space",
    "https://iv.duti.dev",
]

# ===============================
# 追加 Invidious API（指定されたやつ）
# ===============================
INVIDIOUS_EXTRA_APIS = {
    "video": [
        "https://super8.absturztau.be",
        "https://invidious.ducks.party",
        "https://invidious.lunivers.trade",
        "https://invidious.nikkosphere.com",
        "https://iv.melmac.space",
        "https://lekker.gay",
        "https://cal1.iv.ggtyler.dev",
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
    ],
}

# ===============================
# API list merge（重複除去）
# ===============================
def merge(base, extra):
    return list(dict.fromkeys(base + extra))

VIDEO_APIS = merge(VIDEO_APIS, INVIDIOUS_EXTRA_APIS["video"])
SEARCH_APIS = merge(SEARCH_APIS, INVIDIOUS_EXTRA_APIS["search"])
COMMENTS_APIS = merge(COMMENTS_APIS, INVIDIOUS_EXTRA_APIS["comments"])

# ===============================
# Other APIs
# ===============================
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
        f"{u}/api/v1/trending" for u in VIDEO_APIS
    ],
    "stream": [
        "https://yudlp.vercel.app/stream/dQw4w9WgXcQ",
        "https://yudlp.vercel.app/m3u8/dQw4w9WgXcQ",
    ],
    "education": [
        EDU_STREAM_API_BASE_URL
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
    except requests.exceptions.RequestException:
        pass
    return None

# ===============================
# Search
# ===============================
@app.get("/api/search")
def api_search(q: str):
    random.shuffle(SEARCH_APIS)
    for base in SEARCH_APIS:
        data = try_json(f"{base}/api/v1/search", {"q": q, "type": "video"})
        if isinstance(data, list) and data:
            return {
                "results": [
                    {
                        "videoId": v.get("videoId"),
                        "title": v.get("title"),
                        "author": v.get("author"),
                        "authorId": v.get("authorId"),
                    }
                    for v in data if v.get("videoId")
                ],
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
                    {"author": c.get("author"), "content": c.get("content")}
                    for c in data.get("comments", [])
                ],
                "source": base
            }
    return {"comments": [], "source": None}

# ===============================
# Stream helpers（iPad対応）
# ===============================
def get_m3u8_from_yudlp(video_id: str):
    try:
        r = requests.get(f"https://yudlp.vercel.app/m3u8/{video_id}", headers=HEADERS, timeout=TIMEOUT)
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
        r = requests.get(f"{STREAM_YTDL_API_BASE_URL}{video_id}", headers=HEADERS, timeout=TIMEOUT)
        for f in r.json().get("formats", []):
            if str(f.get("itag")) == "18" and f.get("url"):
                return f["url"]
    except:
        pass
    return None

# ===============================
# Stream URL
# ===============================
@app.get("/api/streamurl")
def api_streamurl(video_id: str):
    m3u8 = get_m3u8_from_yudlp(video_id)
    if m3u8:
        return RedirectResponse(m3u8)

    mp4 = get_itag18_mp4(video_id)
    if mp4:
        return RedirectResponse(mp4)

    for base in VIDEO_APIS:
        data = try_json(f"{base}/api/v1/videos/{video_id}")
        if data:
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
