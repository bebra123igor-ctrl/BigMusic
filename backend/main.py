from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import asyncio
import yt_dlp
import aiohttp
import time
import base64
import sys

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="BigMusic")

# Папка для кэша и загрузок
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# CORS для локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Токены Spotify (вшиты как запасные, но .env в приоритете)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "95bf0a87f2994f94a810799888671cf0")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "06f338ad3f9e4f96905ee161cfa79cbc")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN", "AQAYs4svYDNfPb7bihUmNrkQofVxzc1IUVvsVKsezm9N_bjhk84fkSmlA8T0a4lfofNLwPEgz9hggbHRSrJosZg1c1C7a8KVYE7Mhoi8rBj-ffCKkmIaeAzeJXU8uLiiBps")

class Track(BaseModel):
    id: str
    title: str
    artist: str
    album: Optional[str] = None
    cover_url: Optional[str] = None
    source: str = "spotify"

# ==================== SPOTIFY AUTH ====================
spotify_token = {"access": None, "expires": 0}

async def get_token():
    if spotify_token["access"] and time.time() < spotify_token["expires"]:
        return spotify_token["access"]
    
    auth = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    async with aiohttp.ClientSession() as s:
        async with s.post("https://accounts.spotify.com/api/token", 
                         headers={"Authorization": f"Basic {auth}"},
                         data={"grant_type": "refresh_token", "refresh_token": SPOTIFY_REFRESH_TOKEN}) as r:
            if r.status == 200:
                d = await r.json()
                spotify_token["access"] = d["access_token"]
                spotify_token["expires"] = time.time() + d["expires_in"] - 60
                return d["access_token"]
    return None

# ==================== CORE FUNCTIONS ====================

async def get_track_file(track_id: str):
    """Находит или скачивает трек в папку downloads"""
    token = await get_token()
    real_id = track_id.replace("spotify_", "")
    
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://api.spotify.com/v1/tracks/{real_id}", headers={"Authorization": f"Bearer {token}"}) as r:
            if r.status != 200: return None, None
            tr = await r.json()
            search_q = f"{tr['artists'][0]['name']} - {tr['name']}"
            
    safe_name = "".join([c for c in search_q if c.isalnum() or c in (' ', '-', '_')]).strip()
    filepath = os.path.join(DOWNLOAD_DIR, f"{safe_name}.m4a")

    if not os.path.exists(filepath):
        print(f"📥 Downloading: {search_q}")
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': filepath,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            # Добавляем заголовки для обхода простых блокировок
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        # Пробуем найти сначала на SoundCloud (там меньше блокировок), потом на YT
        queries = [
            f"scsearch1:{search_q}", 
            f"ytsearch1:{search_q} official audio"
        ]
        
        success = False
        for query in queries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = await asyncio.to_thread(ydl.extract_info, query, download=True)
                    if info and 'entries' in info and len(info['entries']) > 0:
                        success = True
                        break
            except Exception as e:
                print(f"⚠️ Source failed ({query}): {e}")
                continue
        
        if not success:
            print(f"❌ All sources failed for {search_q}")
            return None, None

    return filepath, f"{search_q}.m4a"

# ==================== API ENDPOINTS ====================

@app.get("/api/tracks")
async def api_tracks(q: Optional[str] = None, seed_track: Optional[str] = None):
    token = await get_token()
    if not token: return {"tracks": [], "artist": None}
    
    async with aiohttp.ClientSession() as s:
        if seed_track:
            real_id = seed_track.replace("spotify_", "")
            url = f"https://api.spotify.com/v1/recommendations?seed_tracks={real_id}&limit=20"
        else:
            is_search = bool(q and q.strip())
            query = q if is_search else "top hits 2025"
            url = f"https://api.spotify.com/v1/search?q={query}&type=track,artist&limit=50"

        async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as r:
            if r.status != 200: return {"tracks": [], "artist": None}
            data = await r.json()
            
            items = data.get("tracks", {}).get("items", []) if not seed_track else data.get("tracks", [])
            tracks = []
            for i in items:
                if not i: continue
                tracks.append(Track(
                    id=f"spotify_{i['id']}",
                    title=i['name'],
                    artist=", ".join([a['name'] for a in i['artists']]),
                    cover_url=i['album']['images'][0]['url'] if i['album']['images'] else None
                ))
            
            artist_data = None
            if q and not seed_track:
                artists = data.get("artists", {}).get("items", [])
                if artists:
                    best = artists[0]
                    artist_data = {
                        "name": best["name"],
                        "followers": best["followers"]["total"],
                        "image_url": best["images"][0]["url"] if best["images"] else None
                    }
            
            return {"tracks": [t.model_dump() for t in tracks], "artist": artist_data}

@app.get("/api/check/{track_id}")
async def api_check(track_id: str):
    token = await get_token()
    real_id = track_id.replace("spotify_", "")
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://api.spotify.com/v1/tracks/{real_id}", headers={"Authorization": f"Bearer {token}"}) as r:
            if r.status != 200: return {"ready": False}
            tr = await r.json()
            search_q = f"{tr['artists'][0]['name']} - {tr['name']}"
            safe_name = "".join([c for c in search_q if c.isalnum() or c in (' ', '-', '_')]).strip()
            filepath = os.path.join(DOWNLOAD_DIR, f"{safe_name}.m4a")
            return {"ready": os.path.exists(filepath)}

@app.get("/api/stream/{track_id}")
async def api_stream(track_id: str):
    filepath, _ = await get_track_file(track_id)
    if filepath and os.path.exists(filepath):
        # Используем StreamingResponse для лучшей совместимости с Range запросами
        def iterfile():
            with open(filepath, mode="rb") as file_like:
                yield from file_like
        return StreamingResponse(iterfile(), media_type="audio/mp4", headers={
            "Content-Disposition": f"inline; filename=track.m4a",
            "Accept-Ranges": "bytes"
        })
    raise HTTPException(status_code=404, detail="Track not found")

@app.get("/api/download/{track_id}")
async def api_download(track_id: str):
    filepath, filename = await get_track_file(track_id)
    if filepath and os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="Track error")

# ==================== STATIC FILES ====================
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    # Если запрашивают API, пролетаем мимо статики
    if file_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    
    file_full_path = os.path.join(FRONTEND_DIR, file_path)
    if os.path.exists(file_full_path) and os.path.isfile(file_full_path):
        return FileResponse(file_full_path)
    
    # SPA fallback: если это не файл, отдаем индекс
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    uvicorn.run(app, host="0.0.0.0", port=8000)
