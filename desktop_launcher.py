import os
import sys
import multiprocessing
import webview
import uvicorn
from backend.main import app
import threading
import socket

def get_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def run_server(port):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

if __name__ == '__main__':
    # Для Windows PyInstaller
    multiprocessing.freeze_support()
    
    port = get_free_port()
    
    # Запускаем бэкенд в отдельном потоке
    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()
    
    # Открываем окно приложения
    webview.create_window(
        'BigMusic Premium', 
        f'http://127.0.0.1:{port}',
        width=1200,
        height=800,
        background_color='#050505'
    )
    webview.start()
