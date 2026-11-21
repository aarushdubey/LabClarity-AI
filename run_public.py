"""
LabClarity AI: Public Deployment via Ngrok
Exposes the local Flask microscopy enhancement server over a secure, publicly accessible HTTPS tunnel.
Directly corresponds to Milestone 5 of the Project Specification.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from pyngrok import ngrok, conf
from app import app

PORT = int(os.getenv("PORT", 5001))
AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "").strip()


def start_tunnel():
    """Configures Ngrok authtoken and establishes public HTTPS tunnel."""
    if AUTHTOKEN and not AUTHTOKEN.startswith("your_"):
        print("[LabClarity AI] Applying configured Ngrok authtoken...")
        ngrok.set_auth_token(AUTHTOKEN)
    else:
        print("[LabClarity AI] Warning: No NGROK_AUTHTOKEN provided in .env.")
        print("[LabClarity AI] Proceeding with anonymous tunnel (may have session limits).")

    try:
        # Open HTTP tunnel to Flask port
        public_url = ngrok.connect(PORT, "http")
        print("\n" + "=" * 62)
        print(" LABCLARITY AI IS NOW LIVE GLOBALLY!")
        print(f" Public HTTPS URL: {public_url}")
        print(f" Local Webhook:    http://127.0.0.1:{PORT}")
        print(" Share this URL for live evaluation & team testing.")
        print("=" * 62 + "\n")
        return public_url
    except Exception as e:
        print(f"[LabClarity AI] Ngrok tunnel error: {e}")
        print("[LabClarity AI] Falling back to standard local execution.")
        return None


if __name__ == "__main__":
    tunnel = start_tunnel()
    # debug=False is required to prevent reloader from duplicating Ngrok tunnel
    app.run(host="127.0.0.1", port=PORT, debug=False)
