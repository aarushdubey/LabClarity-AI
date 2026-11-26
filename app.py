"""
LabClarity AI: Root Application Orchestrator & WSGI/ASGI Compatibility Entry Point.
Runs on Render, Docker, and local development.
"""

import os
import sys
import time
import subprocess
import atexit
import urllib.request
import urllib.error

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "5000"))
AI_PORT = 8000
GATEWAY_PORT = 5000 if "gunicorn" in sys.argv[0] or "app:app" in sys.argv else PORT

os.environ.setdefault("NODE_ENV", "production")
os.environ.setdefault("AI_SERVICE_TOKEN", "labclarity_production_internal_token_32chars_secure")
os.environ.setdefault("AI_SERVICE_URL", f"http://127.0.0.1:{AI_PORT}")
os.environ.setdefault("ALLOW_MEMORY_DB", "1")

_processes = []

def _cleanup():
    for p in _processes:
        try:
            p.terminate()
        except Exception:
            pass

atexit.register(_cleanup)

def _is_listening(url):
    try:
        urllib.request.urlopen(url, timeout=1)
        return True
    except Exception:
        return False

def ensure_services():
    global _processes
    # 1. Start AI service on port 8000 if not listening
    if not _is_listening(f"http://127.0.0.1:{AI_PORT}/health"):
        ai_cmd = [
            sys.executable, "-m", "uvicorn", "app.main:create_app",
            "--factory", "--host", "127.0.0.1", f"--port={AI_PORT}",
            "--app-dir", os.path.join(ROOT_DIR, "backend", "ai-service")
        ]
        p_ai = subprocess.Popen(ai_cmd, cwd=os.path.join(ROOT_DIR, "backend", "ai-service"))
        _processes.append(p_ai)

    # 2. Start Gateway if Gunicorn is taking the outer port
    if GATEWAY_PORT != PORT or not _is_listening(f"http://127.0.0.1:{GATEWAY_PORT}/health/live"):
        gw_dir = os.path.join(ROOT_DIR, "backend", "api-gateway")
        env = os.environ.copy()
        env["PORT"] = str(GATEWAY_PORT)
        script = "src/server.js" if env.get("MONGODB_URI") else "scripts/dev-memory-db.js"
        p_gw = subprocess.Popen(["node", script], cwd=gw_dir, env=env)
        _processes.append(p_gw)

    for _ in range(30):
        if _is_listening(f"http://127.0.0.1:{GATEWAY_PORT}/health/live"):
            break
        time.sleep(0.5)

def app(environ, start_response):
    """WSGI callable that proxies requests to the Node.js API Gateway."""
    ensure_services()
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")
    query = environ.get("QUERY_STRING", "")
    target_url = f"http://127.0.0.1:{GATEWAY_PORT}{path}" + (f"?{query}" if query else "")

    headers = {}
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            header_name = key[5:].replace("_", "-").title()
            headers[header_name] = value
        elif key in ("CONTENT_TYPE", "CONTENT_LENGTH") and value:
            header_name = key.replace("_", "-").title()
            headers[header_name] = value

    data = None
    content_length = int(environ.get("CONTENT_LENGTH") or 0)
    if content_length > 0:
        data = environ["wsgi.input"].read(content_length)

    req = urllib.request.Request(target_url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            status = f"{resp.status} {resp.reason}"
            resp_headers = [(k, v) for k, v in resp.getheaders() if k.lower() != "transfer-encoding"]
            start_response(status, resp_headers)
            return [resp.read()]
    except urllib.error.HTTPError as e:
        status = f"{e.code} {e.reason}"
        resp_headers = [(k, v) for k, v in e.headers.items() if k.lower() != "transfer-encoding"]
        start_response(status, resp_headers)
        return [e.read()]
    except Exception as e:
        start_response("502 Bad Gateway", [("Content-Type", "text/plain")])
        return [f"LabClarity Gateway connecting... ({e})\n".encode()]

if __name__ == "__main__":
    ensure_services()
    try:
        for p in _processes:
            p.wait()
    except KeyboardInterrupt:
        _cleanup()
