import subprocess
import sys
import os
import threading
import time


def start_api():
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
    ])


def start_ui():
    subprocess.run([
        sys.executable, "-m", "streamlit",
        "run", "app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
    ])


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "ui"

    if mode == "api":
        start_api()
    elif mode == "both":
        api_thread = threading.Thread(target=start_api, daemon=True)
        api_thread.start()
        time.sleep(2)
        start_ui()
    else:
        start_ui()


if __name__ == "__main__":
    main()
