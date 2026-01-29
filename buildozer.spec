name = BigMusic
package.name = bigmusic
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,html,js,css,txt,m4a,json
version = 0.1
requirements = python3,fastapi,uvicorn,jinja2,aiohttp,pydantic,python-dotenv,yt-dlp,webview,pywebview

orientation = portrait
fullscreen = 1
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (Дополнительные настройки для вшивания бэкенда)
python_folders = backend,frontend
android.entrypoint = desktop_launcher.py
