from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
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

# Монтируем статику (фронтенд)
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Прокси для app.js и styles.css чтобы они были в корне
@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    file_full_path = os.path.join(FRONTEND_DIR, file_path)
    if os.path.exists(file_full_path) and os.path.isfile(file_full_path):
        return FileResponse(file_full_path)
    # Если файл не найден, но это API - FastAPI сам обработает, 
    # а если нет - вернем 404 или индекс
    return JSONResponse(status_code=404, content={"detail": "Not found"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            
    # Генерируем чистое имя файла
    safe_name = "".join([c for c in search_q if c.isalnum() or c in (' ', '-', '_')]).strip()
    filepath = os.path.join(DOWNLOAD_DIR, f"{safe_name}.m4a")

    if not os.path.exists(filepath):
        print(f"📥 Скачивание (Original Only): {search_q}")
        # Чтобы треки были ОРИГИНАЛЬНЫМИ, добавляем "official audio" и фильтры
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': filepath,
            'quiet': True,
            'no_warnings': True,
            # Добавляем эммуляцию мобилок для обхода 403
            'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        }
        
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Ищем официальное аудио
                ydl.download([f"ytsearch1:{search_q} official audio"])
        
        try:
            await asyncio.to_thread(run_dl)
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None, None

    return filepath, f"{search_q}.m4a"

# ==================== API ENDPOINTS ====================

@app.get("/api/tracks")
async def api_tracks(q: Optional[str] = None, seed_track: Optional[str] = None):
    token = await get_token()
    if not token: return {"tracks": [], "artist": None}
    
    async with aiohttp.ClientSession() as s:
        # Если передан seed_track, получаем рекомендации
        if seed_track:
            real_id = seed_track.replace("spotify_", "")
            url = f"https://api.spotify.com/v1/recommendations?seed_tracks={real_id}&limit=20"
            async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as r:
                if r.status == 200:
                    data = await r.json()
                    tracks_data = data.get("tracks", [])
                    tracks = []
                    for i in tracks_data:
                        tracks.append(Track(
                            id=f"spotify_{i['id']}",
                            title=i['name'],
                            artist=", ".join([a['name'] for a in i['artists']]),
                            cover_url=i['album']['images'][0]['url'] if i['album']['images'] else None
                        ))
                    return {"tracks": [t.model_dump() for t in tracks], "artist": None}

        # Обычный поиск
        is_search = bool(q and q.strip())
        query = q if is_search else "top hits 2025"
        
        # Запрашиваем и треки, и артистов
        url = f"https://api.spotify.com/v1/search?q={query}&type=track,artist&limit=50"
        async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as r:
            if r.status != 200: return {"tracks": [], "artist": None}
            data = await r.json()
            
            # Парсим треки
            items = data.get("tracks", {}).get("items", [])
            tracks = []
            for i in items:
                if not i: continue
                tracks.append(Track(
                    id=f"spotify_{i['id']}",
                    title=i['name'],
                    artist=", ".join([a['name'] for a in i['artists']]),
                    cover_url=i['album']['images'][0]['url'] if i['album']['images'] else None
                ))
            
            # Парсим артиста (только если это был поиск, берем первого лучшего)
            artist_data = None
            if is_search:
                artists = data.get("artists", {}).get("items", [])
                if artists:
                    best_match = artists[0]
                    artist_data = {
                        "name": best_match["name"],
                        "followers": best_match["followers"]["total"],
                        "image_url": best_match["images"][0]["url"] if best_match["images"] else None
                    }
            
            return {"tracks": [t.model_dump() for t in tracks], "artist": artist_data}

@app.get("/api/check/{track_id}")
async def api_check(track_id: str):
    """Проверяет, скачан ли трек"""
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
    print(f"⚡ Запрос на воспроизведение: {track_id}")
    filepath, _ = await get_track_file(track_id)
    if filepath and os.path.exists(filepath):
        # Отдаем файл как есть. Браузер его подхватит.
        return FileResponse(filepath, media_type="audio/mp4")
    raise HTTPException(status_code=404, detail="Track not found")

@app.get("/api/download/{track_id}")
async def api_download(track_id: str):
    print(f"📥 Запрос на скачивание: {track_id}")
    filepath, filename = await get_track_file(track_id)
    if filepath and os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="Track download failed")

if __name__ == "__main__":
    import uvicorn
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    uvicorn.run(app, host="0.0.0.0", port=8000)
