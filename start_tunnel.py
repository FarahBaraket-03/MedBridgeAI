"""Start ngrok tunnel to expose local backend for Databricks evaluation."""
import time
from pyngrok import ngrok

tunnel = ngrok.connect(8000, "http")
print(f"\n{'='*60}")
print(f"  NGROK TUNNEL ACTIVE")
print(f"  Public URL: {tunnel.public_url}")
print(f"  Forwarding to: http://localhost:8000")
print(f"{'='*60}")
print(f"\nUse this URL in Databricks notebook:")
print(f'  MEDBRIDGE_API_URL = "{tunnel.public_url}"')
print(f"\nKeep this window open. Press Ctrl+C to stop.\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down tunnel...")
    ngrok.kill()
