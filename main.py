"""
EcoNodeX — entry point for both development and PyInstaller packaging.

Usage:
    python main.py               # run the server (opens browser)
    python main.py --no-browser  # run without opening browser
"""
import argparse
import pathlib
import socket
import sys
import threading
import time
import webbrowser

# When frozen (no console window), redirect stdout/stderr to a log file so
# startup errors are visible. Log goes next to the exe.
if getattr(sys, "frozen", False):
    _log_path = pathlib.Path(sys.executable).parent / "econodex.log"
    _log_file = open(_log_path, "w", encoding="utf-8", buffering=1)
    sys.stdout = _log_file
    sys.stderr = _log_file

import pystray
import uvicorn
from PIL import Image, ImageDraw

from backend.app.main import app as _app  # direct import so PyInstaller collects backend.*


def _make_tray_icon() -> Image.Image:
    # Resolve assets/ both in development (next to main.py) and when frozen by PyInstaller
    base = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).parent))
    icon_path = base / "assets" / "icon.png"
    if icon_path.exists():
        return Image.open(icon_path).convert("RGBA")
    # Fallback: plain green circle
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(34, 197, 94))
    return img


def _start_server(host: str, port: int):
    uvicorn.run(_app, host=host, port=port, log_level="info")


def main():
    parser = argparse.ArgumentParser(description="EcoNodeX local server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Port")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    args = parser.parse_args()

    server_thread = threading.Thread(
        target=_start_server,
        args=(args.host, args.port),
        daemon=True,
    )
    server_thread.start()

    url = f"http://localhost:{args.port}"

    # Wait until the server is actually accepting connections (up to 30 s)
    for _ in range(60):
        time.sleep(0.5)
        try:
            with socket.create_connection(("127.0.0.1", args.port), timeout=1):
                break
        except OSError:
            pass

    if not args.no_browser:
        print(f"Opening {url} ...")
        webbrowser.open(url)

    # System tray — blocks until the user clicks "Cerrar"
    menu = pystray.Menu(
        pystray.MenuItem(
            "Abrir EcoNodeX",
            lambda icon, item: webbrowser.open(url),
            default=True,  # double-click action
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Cerrar", lambda icon, item: icon.stop()),
    )
    icon = pystray.Icon("EcoNodeX", _make_tray_icon(), "EcoNodeX", menu)
    icon.run()  # returns when icon.stop() is called → process exits (daemon thread dies)


if __name__ == "__main__":
    main()
