"""
LabClarity AI: Local Development Server Runner
"""

import os
from dotenv import load_dotenv

load_dotenv()

from app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    print("=" * 60)
    print(" LabClarity AI: Research Microscopy Image Enhancer")
    print(f" Local Development Server running at: http://{host}:{port}")
    print(" Press CTRL+C to terminate server.")
    print("=" * 60)
    app.run(host=host, port=port, debug=debug)
