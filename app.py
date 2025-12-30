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

@app.get("/")
def root():
    if os.path.isfile("statics/index.html"):
        return FileResponse("statics/index.html")
    return {"status": "index.html not found"}

# ===============================
# External APIs
# ===============================
EDU_STREAM_API_BASE_URL = "https://siawaseok.duckdns.org/api/stream/"
EDU_VIDEO_API_BASE_URL  = "https://siawaseok.duckdns.org/api/video2/"
STREAM_YTDL_API_BASE_URL = "https://yudlp.vercel.app/stream/"
SHORT_STREAM_API_BASE_URL = "https://yt-dl-kappa.vercel.app/short/"

# ===============================
# Invidious API lists（完全統合）
# ===============================
INVIDIOUS_APIS = {
    "video": list(set([
        "https://invidious.exma.de/",
        "https://invidious.f5.si/",
        "https://siawaseok-wakame-server2.glitch.me/",
        "https://lekker.gay/",
        "https://id.420129.xyz/",
        "https://invid-api.poketube.fun/",
        "https://eu-proxy.poketube.fun/",
        "https://cal1.iv.ggtyler.dev/",
        "https://pol1.iv.ggtyler.dev/",
        "https://invidious.lunivers.trade/",
        "https://invidious.ducks.party/",
        "https://super8.absturztau.be/",
        "https://invidious.nikkosphere.com/",
        "https://yt.omada.cafe/",
        "https://iv.melmac.space/",
        "https://iv.duti.dev/",
    ])),
    "search": list(set([
        "https://pol1.iv.ggtyler.dev/",
        "https://youtube.mosesmang.com/",
        "https://iteroni.com/",
        "https://invidious.0011.lt/",
        "https://iv.melmac.space/",
        "https://rust.oskamp.nl/",
        "https://api-five-zeta-55.vercel.app/",
    ])),
    "channel": list(set([
        "https://siawaseok-wakame-server2.glitch.me/",
        "https://id.420129.xyz/",
        "https://invidious.0011.lt/",
        "https://invidious.nietzospannend.nl/",
        "https://invid-api.poketube.fun/",
        "https://invidious.lunivers.trade/",
        "https://invidious.ducks.party/",
        "https://super8.absturztau.be/",
        "https://invidious.nikkosphere.com/",
        "https://yt.omada.cafe/",
        "https://iv.melmac.space/",
        "https://iv.duti.dev/",
    ])),
    "playlist": list(set([
        "https://siawaseok-wakame-server2.glitch.me/",
        "https://invidious.0011.lt/",
        "https://invidious.nietzospannend.nl/",
        "https://youtube.mosesmang.com/",
        "https://iv.melmac.space/",
        "https://lekker.gay/",
    ])),
    "comments": list(set([
        "https://siawaseok-wakame-server2.glitch.me/",
        "https://invidious.0011.lt/",
        "https://invidious.nietzospannend.nl/",
        "https://invidious.lunivers.trade/",
        "https://invidious.ducks.party/",
        "https://super8.absturztau.be/",
        "https://invidious.nikkosphere.com/",
        "https://yt.omada.cafe/",
        "https://iv.melmac.space/",
        "https://iv.duti.dev/",
    ])),
}

TIMEOUT = 6
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ===============================
# Utils
# ===============================
def try_json(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# ===============================
# Search
# ===============================
@app.get("/api/search")
def api_search(q: str):
    apis = INVIDIOUS_APIS["search"].copy()
    random.shuffle(apis)

    for base in apis:
        data = try_json(f"{base}/api/v1/search", {"q": q, "type": "video"})
        if isinstance(data, list) and data:
            return {"source": base, "results": data}

    raise HTTPException(status_code=503, detail="Search unavailable")

# ===============================
# Video Info
# ===============================
@app.get("/api/video")
def api_video(video_id: str):
    apis = INVIDIOUS_APIS["video"].copy()
    random.shuffle(apis)

    for base in apis:
        data = try_json(f"{base}/api/v1/videos/{video_id}")
        if data:
            return data

    raise HTTPException(status_code=503, detail="Video unavailable")

# ===============================
# Channel
# ===============================
@app.get("/api/channel")
def api_channel(channel_id: str):
    apis = INVIDIOUS_APIS["channel"].copy()
    random.shuffle(apis)

    for base in apis:
        data = try_json(f"{base}/api/v1/channels/{channel_id}")
        if data:
            return data

    raise HTTPException(status_code=503, detail="Channel unavailable")

# ===============================
# Comments
# ===============================
@app.get("/api/comments")
def api_comments(video_id: str):
    apis = INVIDIOUS_APIS["comments"].copy()
    random.shuffle(apis)

    for base in apis:
        data = try_json(f"{base}/api/v1/comments/{video_id}")
        if data:
            return data

    return {"comments": []}

# ===============================
# Stream URL（最重要）
# ===============================
@app.get("/api/streamurl")
def api_streamurl(video_id: str):

    # ① EDU m3u8
    try:
        r = requests.get(f"{EDU_STREAM_API_BASE_URL}{video_id}", timeout=TIMEOUT)
        if r.status_code == 200 and "url" in r.json():
            return RedirectResponse(r.json()["url"])
    except:
        pass

    # ② yudlp itag18
    try:
        r = requests.get(f"{STREAM_YTDL_API_BASE_URL}{video_id}", timeout=TIMEOUT)
        for f in r.json().get("formats", []):
            if str(f.get("itag")) == "18":
                return RedirectResponse(f["url"])
    except:
        pass

    # ③ SHORT
    try:
        r = requests.get(f"{SHORT_STREAM_API_BASE_URL}{video_id}", timeout=TIMEOUT)
        if r.status_code == 200 and "url" in r.json():
            return RedirectResponse(r.json()["url"])
    except:
        pass

    # ④ Invidious fallback
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
# Status
# ===============================
@app.get("/api/status")
def api_status():
    results = []

    for category, urls in INVIDIOUS_APIS.items():
        for base in urls:
            start = time.time()
            ok = False
            try:
                r = requests.get(f"{base}/api/v1/trending", timeout=5)
                ok = r.status_code == 200
            except:
                pass

            results.append({
                "category": category,
                "base": base,
                "ok": ok,
                "latency_ms": int((time.time() - start) * 1000)
            })

    return results
