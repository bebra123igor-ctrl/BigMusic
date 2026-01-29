# BigMusic 🎵

Красивое веб-приложение для прослушивания и скачивания музыки из Yandex Music и Spotify.

## Возможности

- 🎧 Прослушивание треков из Yandex Music и Spotify
- 📥 Скачивание в MP3 формате
- 🎨 Красивый современный интерфейс с анимациями
- 🔍 Поиск по названию и исполнителю
- 🌈 Glassmorphism дизайн

## Структура проекта

```
BigMusic/
├── backend/           # FastAPI сервер
│   ├── main.py       # Основной API
│   ├── requirements.txt
│   └── .env.example
├── frontend/          # Веб-интерфейс
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── README.md
```

## Установка

### Backend

1. Создайте виртуальное окружение:
```bash
cd backend
python -m venv venv
```

2. Активируйте его:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example` и добавьте свои токены.

5. Запустите сервер:
```bash
python main.py
```

API будет доступен на `http://localhost:8000`

### Frontend

Просто откройте `frontend/index.html` в браузере или запустите локальный сервер:

```bash
cd frontend
python -m http.server 3000
```

Затем откройте `http://localhost:3000`

## Получение токенов

### Yandex Music

1. Перейдите в [инструкцию](https://github.com/MarshalX/yandex-music-api#получение-токена)
2. Получите OAuth токен
3. Вставьте в настройки приложения

### Spotify

1. Перейдите в [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Создайте новое приложение
3. Получите Client ID и Client Secret
4. Для Refresh Token используйте OAuth flow или инструменты вроде [spotifyauth](https://github.com/plamber/spotifyauth)

## API Endpoints

- `GET /api/tracks` - Получить все треки
- `GET /api/tracks?source=yandex` - Только Yandex Music
- `GET /api/tracks?source=spotify` - Только Spotify
- `GET /api/stream/{track_id}` - Стриминг трека
- `GET /api/download/{track_id}` - Скачать MP3
- `POST /api/tokens` - Обновить токены
- `GET /api/status` - Статус подключений

## Технологии

### Backend
- FastAPI
- yandex-music (API)
- spotipy (Spotify API)
- yt-dlp (для скачивания)

### Frontend
- Vanilla HTML/CSS/JS
- CSS Variables
- CSS Animations
- Glassmorphism design
