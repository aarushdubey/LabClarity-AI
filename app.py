"""
LabClarity AI: Root Application Orchestrator & WSGI Compatibility Entry Point.
Runs on Render, Docker, and local development.
"""

import os
import sys
import time
import fcntl
import subprocess
import atexit
import urllib.request
import urllib.error

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "5000"))
AI_PORT = 8000
GATEWAY_PORT = int(os.environ.get("GATEWAY_PORT", "5000")) if ("gunicorn" in sys.argv[0] or "app:app" in sys.argv) else PORT

os.environ.setdefault("NODE_ENV", "production")
os.environ.setdefault("AI_SERVICE_TOKEN", "labclarity_production_internal_token_32chars_secure")
os.environ.setdefault("AI_SERVICE_URL", f"http://127.0.0.1:{AI_PORT}")
os.environ.setdefault("ALLOW_MEMORY_DB", "1")

_processes = []
_boot_done = False

def _cleanup():
    for p in _processes:
        try:
            p.terminate()
        except Exception:
            pass

atexit.register(_cleanup)

def _is_listening(url):
    try:
        with urllib.request.urlopen(url, timeout=0.5) as resp:
            return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False

def ensure_services():
    global _boot_done
    if _boot_done or _is_listening(f"http://127.0.0.1:{GATEWAY_PORT}/api/v1/health/live"):
        _boot_done = True
        return

    lock = open("/tmp/labclarity_boot.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if _is_listening(f"http://127.0.0.1:{GATEWAY_PORT}/api/v1/health/live"):
            _boot_done = True
            return

        if not _is_listening(f"http://127.0.0.1:{AI_PORT}/health"):
            ai_dir = os.path.join(ROOT_DIR, "backend", "ai-service")
            ai_cmd = [
                sys.executable, "-m", "uvicorn", "app.main:create_app",
                "--factory", "--host", "127.0.0.1", f"--port={AI_PORT}",
                "--app-dir", ai_dir
            ]
            _processes.append(subprocess.Popen(ai_cmd, cwd=ai_dir))

        gw_dir = os.path.join(ROOT_DIR, "backend", "api-gateway")
        if not os.path.exists(os.path.join(gw_dir, "node_modules")):
            subprocess.run(["npm", "install"], cwd=gw_dir, check=True)

        if not _is_listening(f"http://127.0.0.1:{GATEWAY_PORT}/api/v1/health/live"):
            env = os.environ.copy()
            env["PORT"] = str(GATEWAY_PORT)
            script = "src/server.js" if env.get("MONGODB_URI") else "scripts/dev-memory-db.js"
            _processes.append(subprocess.Popen(["node", script], cwd=gw_dir, env=env))

        for _ in range(60):
            if _is_listening(f"http://127.0.0.1:{GATEWAY_PORT}/api/v1/health/live"):
                _boot_done = True
                break
            time.sleep(0.5)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()

if "gunicorn" in sys.argv[0] or "app:app" in sys.argv:
    ensure_services()

def app(environ, start_response):
    """WSGI callable that proxies requests to the Node.js API Gateway."""
    ensure_services()
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")
    query = environ.get("QUERY_STRING", "")
    target_url = f"http://127.0.0.1:{GATEWAY_PORT}{path}" + (f"?{query}" if query else "")

    headers = {}
    for key, val in environ.items():
        if key.startswith("HTTP_"):
            headers[key[5:].replace("_", "-").title()] = val
        elif key in ("CONTENT_TYPE", "CONTENT_LENGTH") and val:
            headers[key.replace("_", "-").title()] = val

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
            return [] if method == "HEAD" else [resp.read()]
    except urllib.error.HTTPError as e:
        status = f"{e.code} {e.reason}"
        resp_headers = [(k, v) for k, v in e.headers.items() if k.lower() != "transfer-encoding"]
        start_response(status, resp_headers)
        return [] if method == "HEAD" else [e.read()]
    except Exception as e:
        start_response("502 Bad Gateway", [("Content-Type", "text/plain")])
        return [] if method == "HEAD" else [f"LabClarity Gateway connecting... ({e})\n".encode()]

if __name__ == "__main__":
    ensure_services()
    try:
        for p in _processes:
            p.wait()
    except KeyboardInterrupt:
        _cleanup()
