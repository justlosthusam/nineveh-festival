import os
import sys
import time
import subprocess
import urllib.request
import re
import json

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_SCRIPT = os.path.join(PROJECT_DIR, "server.py")
CLOUDFLARED_EXE = os.path.join(PROJECT_DIR, "cloudflared.exe")
if not os.path.exists(CLOUDFLARED_EXE):
    CLOUDFLARED_EXE = r"C:\Users\newFUTURE\.gemini\antigravity\scratch\nineveh_film_festival\cloudflared.exe"

JSON_TUNNEL_FILE = os.path.join(PROJECT_DIR, "assets", "live_tunnel.json")
LOG_FILE = os.path.join(PROJECT_DIR, "tunnel.log")
ADMIN_KEY_FILE = os.path.join(PROJECT_DIR, "admin_key.txt")
ADMIN_LINK_TXT = os.path.join(PROJECT_DIR, "ADMIN_LINK.txt")
ADMIN_HTML_PORTAL = os.path.join(PROJECT_DIR, "ADMIN_QR.html")

server_process = None
tunnel_process = None

def get_admin_key():
    if os.path.exists(ADMIN_KEY_FILE):
        try:
            return open(ADMIN_KEY_FILE, "r", encoding="utf-8").read().strip()
        except Exception:
            pass
    return "niff_admin_2026"

def check_server_alive():
    try:
        res = urllib.request.urlopen("http://localhost:8080/api/seats", timeout=3)
        return res.status == 200
    except Exception:
        return False

def start_server():
    global server_process
    print("[KEEP-ALIVE] Starting Python Server (server.py)...")
    server_process = subprocess.Popen([sys.executable, SERVER_SCRIPT], cwd=PROJECT_DIR)

def extract_and_save_tunnel_url():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            matches = re.findall(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
            if matches:
                latest_url = matches[-1]
                admin_k = get_admin_key()
                admin_full_url = f"{latest_url}/admin?key={admin_k}"

                data = {
                    "live_url": latest_url,
                    "admin_url": admin_full_url,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                os.makedirs(os.path.dirname(JSON_TUNNEL_FILE), exist_ok=True)
                with open(JSON_TUNNEL_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                # Save text link for quick copy
                with open(ADMIN_LINK_TXT, "w", encoding="utf-8") as f:
                    f.write(f"PUBLIC WEBSITE: {latest_url}\n")
                    f.write(f"ADMIN PANEL:    {admin_full_url}\n")
                    f.write(f"ADMIN KEY:      {admin_k}\n")

                # Generate handy QR Code page to scan from mobile
                qr_img_url = f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&data={urllib.parse.quote(admin_full_url)}"
                portal_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>رابط لوحة الأدمن ومسح الباركود</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ background: #120304; color: #fff; font-family: Tahoma, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 15px; box-sizing: border-box; text-align: center; }}
    .card {{ background: #1e080a; border: 2px solid #c5a059; border-radius: 20px; padding: 25px; max-width: 420px; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }}
    h2 {{ color: #c5a059; margin-top: 0; }}
    .qr-box {{ background: #fff; padding: 12px; border-radius: 14px; display: inline-block; margin: 15px 0; }}
    .btn {{ display: block; background: #c5a059; color: #120304; padding: 14px; font-weight: bold; border-radius: 12px; text-decoration: none; font-size: 16px; margin-top: 15px; }}
    .link-txt {{ word-break: break-all; font-size: 13px; color: #fde047; background: #000; padding: 10px; border-radius: 8px; margin-top: 10px; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>لوحة تحكم الأدمن المباشرة 24/7</h2>
    <p style="font-size: 13px; color: #ddd;">امسح الباركود التالي بكاميرا هاتفك لفتح لوحة الأدمن فوراً:</p>
    <div class="qr-box">
      <img src="{qr_img_url}" alt="Admin QR Code" style="display:block; width:260px; height:260px;">
    </div>
    <div class="link-txt">{admin_full_url}</div>
    <a href="{admin_full_url}" target="_blank" class="btn">فتح لوحة الأدمن الآن</a>
  </div>
</body>
</html>"""
                with open(ADMIN_HTML_PORTAL, "w", encoding="utf-8") as f:
                    f.write(portal_html)

                print(f"\n========================================================")
                print(f"[KEEP-ALIVE] LIVE 24/7 SYSTEM IS ACTIVE!")
                print(f"-> PUBLIC URL: {latest_url}")
                print(f"-> ADMIN URL:  {admin_full_url}")
                print(f"========================================================\n")
                return latest_url
        except Exception as e:
            print(f"[KEEP-ALIVE ERROR] {e}")
    return None

def start_tunnel():
    global tunnel_process
    print("[KEEP-ALIVE] Starting Cloudflare Tunnel (cloudflared)...")
    log_f = open(LOG_FILE, "a", encoding="utf-8")
    tunnel_process = subprocess.Popen([CLOUDFLARED_EXE, "tunnel", "--url", "http://localhost:8080"], cwd=PROJECT_DIR, stdout=log_f, stderr=log_f)
    time.sleep(5)
    extract_and_save_tunnel_url()

print("[KEEP-ALIVE] 24/7 Watchdog System Initialized")

if __name__ == "__main__":
    while True:
        if not check_server_alive():
            print("[KEEP-ALIVE] Server check failed. Restarting server...")
            if server_process and server_process.poll() is None:
                try: server_process.kill()
                except Exception: pass
            start_server()
            time.sleep(3)

        if tunnel_process is None or tunnel_process.poll() is not None:
            print("[KEEP-ALIVE] Cloudflare Tunnel process not running. Starting tunnel...")
            start_tunnel()
        else:
            extract_and_save_tunnel_url()

        time.sleep(10)
