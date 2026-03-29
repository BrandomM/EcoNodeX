"""
EcoNodeX — entry point for both development and PyInstaller packaging.

Usage:
    python main.py               # run the server (opens browser)
    python main.py --no-browser  # run without opening browser
"""
import argparse
import sys
import threading
import time
import webbrowser

import uvicorn


def _start_server(host: str, port: int):
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        log_level="info",
    )


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

    if not args.no_browser:
        # Give the server a moment to start before opening browser
        time.sleep(1.5)
        url = f"http://localhost:{args.port}"
        print(f"Opening {url} ...")
        webbrowser.open(url)

    print("EcoNodeX is running. Presiona Ctrl+C para salir.")
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\nEcoNodeX detenido.")
        sys.exit(0)


if __name__ == "__main__":
    main()
