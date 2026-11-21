"""
LabClarity AI: Local Development Server Runner
"""

import os
import socket
from dotenv import load_dotenv

load_dotenv()

from app import app


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a local port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def get_preferred_port(default_port: int = 5001, host: str = "127.0.0.1") -> int:
    """
    Returns an available port. On macOS, port 5000 is claimed by ControlCenter (AirPlay Receiver),
    causing HTTP 403 Forbidden. Defaults to 5001 and auto-increments if occupied.
    """
    env_port = os.getenv("PORT")
    candidate = int(env_port) if env_port else default_port

    if is_port_in_use(candidate, host):
        print(f"[LabClarity AI] Port {candidate} is occupied (macOS AirPlay Receiver / ControlCenter).")
        candidate = 5001
        while is_port_in_use(candidate, host):
            candidate += 1
        print(f"[LabClarity AI] Automatically routed to available port: {candidate}")

    return candidate


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = get_preferred_port(default_port=5001, host=host)
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    print("=" * 64)
    print(" 🔬 LabClarity AI: Research Microscopy Image Enhancer")
    print(f" Server running at: http://{host}:{port}")
    print(f" Access in browser: http://127.0.0.1:{port} (or http://localhost:{port})")
    print(" Press CTRL+C to stop server.")
    print("=" * 64)
    app.run(host=host, port=port, debug=debug)
