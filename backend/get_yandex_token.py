
import webbrowser
import time

print("\n" + "="*60)
print("ПОЛУЧЕНИЕ YANDEX MUSIC TOKEN (СПОСОБ GITHUB - FIXED)")
print("="*60)

# Список актуальных Client ID
ids = [
    ("Desktop App", "eeac4a0590c342939316317498c8ebc5"),
    ("Music Mobile", "2330a92cd86b4f738096f30a9053d100"),
    ("Yandex Radio", "fe1eeed3161c471c89019688b1cc30fa")
]

print("\nИНСТРУКЦИЯ:")
print("1. Мы попробуем открыть 3 разные ссылки.")
print("2. Если первая выдаст 400 - закрой вкладку и попробуй вторую.")
print("3. Как только увидишь страницу с подтверждением - нажми 'Разрешить'.")
print("4. Скопируй из адресной строки часть после 'access_token='.")

for name, cid in ids:
    auth_url = f"https://oauth.yandex.ru/authorize?response_type=token&client_id={cid}"
    print(f"\n---> Пробуем метод: {name}")
    print(f"Ссылка: {auth_url}")
    
    webbrowser.open(auth_url)
    
    ans = input("\nЭто сработало? (y/n): ")
    if ans.lower() == 'y':
        print("\nОтлично! Копируй токен и вставляй в .env")
        break
    else:
        print("Пробуем следующий вариант...")

print("\n" + "="*60)
