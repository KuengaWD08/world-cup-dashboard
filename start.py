"""
start.py — One-click launch script for the World Cup Betting Dashboard.

Usage:
    python start.py

Options:
    Set FOOTBALL_DATA_API_KEY environment variable for auto score sync.
    Get a free key at https://www.football-data.org/ (free registration).

What it does:
    1. Starts the Django web server on port 8000.
    2. Starts APScheduler to sync live scores every 5 minutes (if API key set).
    3. Starts an ngrok tunnel and prints a public URL for your family.
"""
import os
import sys
import threading
import subprocess
import time

# Must be set before importing Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def start_django():
    """Start Django dev server."""
    subprocess.run([sys.executable, 'manage.py', 'runserver', '8000'])


def start_scheduler():
    """Start background score sync every 5 minutes (requires API key)."""
    # Try to get from environment, fallback to hardcoded for Windows compatibility
    api_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
    
    # Hardcoded fallback (Windows environment variable workaround)
    if not api_key:
        api_key = 'ba326db5fbee4e63aeb5044ddfc80836'
    
    if not api_key or api_key == 'your_key_here':
        print("\n[SYNC] No FOOTBALL_DATA_API_KEY set — scores won't auto-sync.")
        print("[SYNC] To enable: set FOOTBALL_DATA_API_KEY=yourkey then restart.\n")
        return

    # Set it back into environment for Django to use
    os.environ['FOOTBALL_DATA_API_KEY'] = api_key

    from apscheduler.schedulers.background import BackgroundScheduler
    import django
    django.setup()

    from django.core.management import call_command

    def sync_job():
        try:
            call_command('sync_scores')
        except Exception as e:
            print(f"[SYNC] Error during sync: {e}")

    # Run once immediately on startup
    sync_job()

    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_job, 'interval', minutes=5, id='sync_scores')
    scheduler.start()
    print("[SYNC] Auto-sync started — scores will update every 5 minutes.")


def download_ngrok_manually():
    """Download ngrok.exe directly into .ngrok/ folder, bypassing pyngrok's broken temp-path downloader."""
    import zipfile
    import io

    ngrok_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.ngrok')
    os.makedirs(ngrok_dir, exist_ok=True)
    ngrok_exe = os.path.join(ngrok_dir, 'ngrok.exe')

    if os.path.exists(ngrok_exe):
        return ngrok_exe  # Already downloaded

    print("[NGROK] Downloading ngrok.exe ...", flush=True)
    try:
        import urllib.request
        zip_url = 'https://bin.ngrok.com/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip'
        with urllib.request.urlopen(zip_url, timeout=60) as response:
            zip_data = response.read()

        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            for name in z.namelist():
                if name.endswith('.exe'):
                    with z.open(name) as src, open(ngrok_exe, 'wb') as dst:
                        dst.write(src.read())
                    print(f"[NGROK] Installed to {ngrok_exe}", flush=True)
                    return ngrok_exe

        print("[NGROK] Could not find .exe in zip archive.")
        return None
    except Exception as e:
        print(f"[NGROK] Manual download failed: {e}")
        return None


def start_ngrok():
    """Start ngrok tunnel and print public URL."""
    time.sleep(3)  # Wait for Django to be up
    try:
        from pyngrok import ngrok, conf

        # Use manually-downloaded ngrok binary to avoid Windows temp path bug
        ngrok_exe = download_ngrok_manually()
        if ngrok_exe:
            conf.get_default().ngrok_path = ngrok_exe

        # Set authtoken
        authtoken = os.getenv('NGROK_AUTHTOKEN', '3F4Nu5DntSRSehm7xvP3CRSxe9D_4pobNGfrEfC39ByrDZW4Y')
        if authtoken:
            ngrok.set_auth_token(authtoken)

        public_url = ngrok.connect(8000)
        print("\n" + "=" * 60)
        print("🏆  WORLD CUP BETTING DASHBOARD IS LIVE!")
        print("=" * 60)
        print(f"\n📱  Share this link with your family:")
        print(f"\n    {public_url}\n")
        print("=" * 60)
        print("(This link works on any device — phone, tablet, laptop)")
        print("(It stays active as long as this window is open)\n")
    except Exception as e:
        print(f"[NGROK] Could not start public tunnel: {e}")
        print("[NGROK] Dashboard is still available locally at http://localhost:8000/")


if __name__ == '__main__':
    print("Starting World Cup Betting Dashboard...")

    # Thread 1: score sync scheduler (non-blocking)
    sync_thread = threading.Thread(target=start_scheduler, daemon=True)
    sync_thread.start()

    # Thread 2: ngrok tunnel
    ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)
    ngrok_thread.start()

    # Main thread: Django server (blocks until Ctrl+C)
    start_django()