"""
Простой способ получить Spotify Refresh Token
"""

import requests
import base64
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CLIENT_ID = "95bf0a87f2994f94a810799888671cf0"
CLIENT_SECRET = "06f338ad3f9e4f96905ee161cfa79cbc"

print("\n" + "="*60)
print("Получение Spotify Refresh Token (ручной способ)")
print("="*60)

print("""
ИНСТРУКЦИЯ:

1. Открой эту ссылку в браузере:

https://accounts.spotify.com/authorize?client_id=95bf0a87f2994f94a810799888671cf0&response_type=code&redirect_uri=https://example.com/callback&scope=user-library-read%20user-read-currently-playing%20user-read-playback-state

2. Разреши доступ приложению

3. Тебя перенаправит на example.com с ошибкой - ЭТО НОРМАЛЬНО!

4. Скопируй КОД из адресной строки браузера. 
   URL будет выглядеть так:
   https://example.com/callback?code=AQD...очень_длинный_код...

5. Скопируй только часть после "code=" (без &state если есть)

""")

code = "AQCamKk3QNueTbAFAYn4Xoyw7jsKUHiA_vvE3aZlaoa8oJgMS65nCEIm5gr7fRWiP9gDivEvLzoG5deuLJEmedrpZki3yW7jHTL142111cZyMC16Om9CDIe5j87FxonIh2ZSZS2JILnA0HY0AQ4GiE-90zVW5gLyp_ZYIYmxPTVJrOjamnr8Rn3gEgLFcKSVTexPzQuZs_5L5LCa1mRLstEVh79uU555d_k8F5_NWzQXZRJYBgqJsCCT_jchgTeSCwENFLWKnyXcNA"
if not code:
    print("Код не введён!")
    sys.exit(1)

print("\nОбмениваю код на токены...")

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
        "redirect_uri": "https://example.com/callback"
    }
)

data = response.json()

if 'error' in data:
    print(f"\nОшибка: {data['error']}")
    print(f"Описание: {data.get('error_description', 'нет')}")
    sys.exit(1)

print("\n" + "="*60)
print("УСПЕХ!")
print("="*60)
print()
print("Твой REFRESH TOKEN:")
print()
print(data.get('refresh_token', 'НЕ ПОЛУЧЕН'))
print()
print("="*60)
print("Скопируй его и вставь в main.py в строку SPOTIFY_REFRESH_TOKEN")
print("="*60)
