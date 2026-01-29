"""
Скрипт для получения Spotify Refresh Token
Запусти: python get_spotify_token.py
"""

import webbrowser
import http.server
import socketserver
import urllib.parse
import requests
import base64
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Твои данные
CLIENT_ID = "95bf0a87f2994f94a810799888671cf0"
CLIENT_SECRET = "06f338ad3f9e4f96905ee161cfa79cbc"
REDIRECT_URI = "http://localhost:8889/callback"
SCOPE = "user-library-read user-read-currently-playing user-read-playback-state"

auth_code = None

class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write("""
            <html>
            <head><title>Успех!</title></head>
            <body style="font-family: system-ui; background: #1a1a2e; color: white; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;">
                <div style="text-align: center;">
                    <h1 style="color: #1ed760;">✅ Авторизация успешна!</h1>
                    <p>Можешь закрыть это окно и вернуться в терминал.</p>
                </div>
            </body>
            </html>
            """.encode('utf-8'))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Error")
    
    def log_message(self, format, *args):
        pass  # Не выводим логи сервера

def get_tokens(code):
    """Обменять код на токены"""
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
    )
    
    return response.json()

def main():
    print("\n" + "="*60)
    print("🎵 Получение Spotify Refresh Token")
    print("="*60 + "\n")
    
    # Формируем URL для авторизации
    auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"scope={urllib.parse.quote(SCOPE)}"
    )
    
    print("📌 Сейчас откроется браузер для авторизации в Spotify...")
    print("📌 Разреши доступ приложению.\n")
    
    # Открываем браузер
    webbrowser.open(auth_url)
    
    # Запускаем сервер для получения callback
    print("⏳ Ожидаю авторизацию...")
    
    with socketserver.TCPServer(("", 8889), CallbackHandler) as httpd:
        while auth_code is None:
            httpd.handle_request()
    
    print("\n✅ Код получен! Обмениваю на токены...\n")
    
    # Получаем токены
    tokens = get_tokens(auth_code)
    
    if 'error' in tokens:
        print(f"❌ Ошибка: {tokens['error']}")
        print(f"   {tokens.get('error_description', '')}")
        return
    
    print("="*60)
    print("🎉 УСПЕХ! Вот твои токены:")
    print("="*60)
    print()
    print(f"Access Token (временный):")
    print(f"   {tokens.get('access_token', 'N/A')[:50]}...")
    print()
    print(f"🔑 REFRESH TOKEN (вставь в настройки BigMusic):")
    print()
    print(f"   {tokens.get('refresh_token', 'N/A')}")
    print()
    print("="*60)
    print()
    print("📋 Скопируй Refresh Token выше и вставь в настройки BigMusic!")
    print()

if __name__ == "__main__":
    main()
