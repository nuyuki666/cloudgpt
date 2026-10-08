# start_public_host.py
# Automatic Cloudflare Tunnel launcher for global 24/7 HTTPS hosting
import os
import sys
import subprocess
import urllib.request
import re
import time

PORT = 8000
CLOUDFLARED_PATH = os.path.abspath(os.path.join("apk_tools", "cloudflared.exe"))
CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

def ensure_cloudflared():
    os.makedirs("apk_tools", exist_ok=True)
    if not os.path.exists(CLOUDFLARED_PATH) or os.path.getsize(CLOUDFLARED_PATH) < 1000000:
        print("[HOST] Загрузка официального Cloudflare Tunnel...")
        try:
            urllib.request.urlretrieve(CLOUDFLARED_URL, CLOUDFLARED_PATH)
            print(f"[HOST] Cloudflare Tunnel успешно установлен ({os.path.getsize(CLOUDFLARED_PATH)} байт)")
        except Exception as e:
            print(f"[ERROR] Не удалось скачать cloudflared: {e}")
            return False
    return True

def run_tunnel():
    if not ensure_cloudflared():
        return
    
    print("\n" + "=" * 65)
    print("  🌐 ЗАПУСК ПУБЛИЧНОГО ХОСТИНГА ДЛЯ CLOUDGPT (HTTPS С СЕРТИФИКАТОМ) 🌐")
    print("=" * 65)
    print(f"  Локальный порт: http://localhost:{PORT}")
    print("  Создание защищенного глобального туннеля...")
    
    cmd = [CLOUDFLARED_PATH, "tunnel", "--url", f"http://localhost:{PORT}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    tunnel_url = None
    for line in proc.stdout:
        print(line, end="")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            tunnel_url = match.group(0)
            print("\n" + "🎉" * 25)
            print("  🚀 ВАШ ИИ-АГЕНТ CLOUDGPT ДОСТУПЕН ПО ВСЕМУ МИРУ!")
            print(f"  👉 ПУБЛИЧНЫЙ АДРЕС: {tunnel_url}")
            print("🎉" * 25 + "\n")
            print("  Отправьте эту ссылку на телефон или друзьям — она работает везде!\n")
            break
            
    proc.wait()

if __name__ == "__main__":
    run_tunnel()
