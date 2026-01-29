
import requests
import re

# Твои куки
cookies_str = "_yasc=Ca1CedrGGozcS60kLw5Q11u/Jx6Ql3jCzMByOhQQJuII+oO0YVs4FeKNu3U0dRLrg3sY+g==; i=oKMhGCjKf6uk+kZP7BN2AIVWAzAML5bBhhIlk9fXzFDKnJWWnHuA7m2O5xmDAat0UpQrgMdFYvwFfs4u2Qh4Cbyzf1Q=; yandexuid=973070211769518564; yashr=4279785291769518564; bh=YNGy6ssGahfcyuH/CJLYobEDn8/14Qyx3POOA7rQAQ==; is_gdpr=0; is_gdpr_b=CMWBTRDf8AI=; yuidss=973070211769518564; ymex=2084878568.yrts.1769518568; gdpr=0; _ym_uid=1769518566923983525; _ym_d=1769518566; Session_id=3:1769518665.5.0.1769518665552:ElSJTQ:ea24.1.2:1|1803199157.-1.2.3:1769518665|3:11657180.196160.ChkvAF4Mt6lwlxjvblo_z6Pq2b4; sessar=1.1615350.CiA9HPkepaUSEYOaaA6EWy7DZfObgCBg58j1lDLO9YUb2g.z1-hwaUSH_sHKEmpJrNmUuP1eeepyUowU1WbzWytbQE; sessionid2=3:1769518665.5.0.1769518665552:ElSJTQ:ea24.1.2:1|1803199157.-1.2.3:1769518665|3:11657180.196160.fakesign0000000000000000000; yp=2084878665.udn.cDpJZ29yIE1pa2hlbHNvbg%3D%3D; L=VjVSfGRoeGJ+VEtAAnx7U1VLXmBUYF1FHgc8AiIdDgMjFhkJOw==.1769518665.1651333.39077.8d4abf75c85e1ee500234eb231668dd9; yandex_login=ihormikhelson; _ym_isad=2; _ym_visorc=b"

def get_token():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": cookies_str,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    print("Захожу на главную страницу Музыки...")
    r = requests.get("https://music.yandex.ru/home", headers=headers)
    
    # Ищем токен в скриптах страницы
    token_match = re.search(r'"access_token":"([^"]+)"', r.text)
    
    if token_match:
        token = token_match.group(1)
        print("\n" + "="*50)
        print("ПОБЕДА! ТОКЕН ИЗВЛЕЧЕН:")
        print("="*50)
        print(token)
        print("="*50)
        print("\nВставь его в .env в поле YANDEX_TOKEN")
    else:
        print("Ошибка: Токен не найден в коде страницы.")
        print("Пробую альтернативный поиск...")
        
        # Еще один вариант поиска
        alt_match = re.search(r'OAuth\s+([a-zA-Z0-9_\-]+)', r.text)
        if alt_match:
            print(f"Найден альтернативный токен: {alt_match.group(1)}")
        else:
            print("Ничего не вышло. Проверь, не разлогинился ли ты в браузере?")

if __name__ == "__main__":
    get_token()
