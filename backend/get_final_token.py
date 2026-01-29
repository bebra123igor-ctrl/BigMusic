
import requests
import json

# Твой свежий Session_id
session_id = "3:1769518665.5.0.1769518665552:ElSJTQ:ea24.1.2:1|1803199157.-1.2.3:1769518665|3:11657180.196160.ChkvAF4Mt6lwlxjvblo_z6Pq2b4"

def fetch_token():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": f"Session_id={session_id}; sessionid2={session_id}",
        "Host": "passport.yandex.ru"
    }
    
    print("Запрашиваю токен у паспортной службы Яндекса...")
    
    # Этот эндпоинт отдает все активные токены для текущей сессии
    url = "https://passport.yandex.ru/am/json/get_all_auth_cookies"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            # Ищем access_token в конфиге авторизации
            sessions = data.get("sessions", {}).get("list", [])
            for s in sessions:
                for cookie in s.get("cookies", []):
                    if cookie.get("name") == "access_token":
                        token = cookie.get("value")
                        print("\n" + "!"*50)
                        print("ТОКЕН УСПЕШНО ПОЛУЧЕН:")
                        print(token)
                        print("!"*50)
                        return
            
            # Если не нашли в куках, ищем в основном тексте ответа
            import re
            match = re.search(r'"access_token":"([^"]+)"', r.text)
            if match:
                print("\n" + "!"*50)
                print("ТОКЕН НАЙДЕН (REGEX):")
                print(match.group(1))
                print("!"*50)
            else:
                print("Ошибка: Токен не найден в ответе Яндекса.")
                print("Ответ сервера:", r.text[:200]) # Показываем начало ответа для диагностики
        else:
            print(f"Ошибка сервера: {r.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    fetch_token()
