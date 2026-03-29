"""Application configuration."""
import os
import socket
from pathlib import Path

APP_NAME = "EcoNodeX"
APP_VERSION = "1.0.0"

# Data directory — writable location next to exe when packaged, or ~/EcoNodeX otherwise
def _resolve_data_dir() -> Path:
    # PyInstaller sets sys.frozen; store data next to the executable
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "data"
    return Path.home() / "EcoNodeX"


DATA_DIR: Path = _resolve_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH: Path = DATA_DIR / "econodex.db"
DATABASE_URL: str = f"sqlite:///{DATABASE_PATH}"

HOST: str = "0.0.0.0"
PORT: int = 8765
FRONTEND_DIST: Path = Path(__file__).parent.parent.parent / "frontend" / "dist"


def get_local_ip() -> str:
    """Return the machine's LAN IP (best-effort)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()
