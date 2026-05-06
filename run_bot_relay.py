#!/usr/bin/env python3
"""
Simple runner for bot_relay_client.py
Prompts for credentials and runs the relay client
"""

import logging
import sys
import os

# Add current directory to path so we can import bot_relay_client
sys.path.insert(0, os.path.dirname(__file__))

from bot_relay_client import create_relay_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("🤖 DababyBot Relay Client Runner")
    print("=" * 40)

    # Get credentials from user
    cloud_url = input("Enter cloud relay URL (e.g., https://your-app.onrender.com): ").strip()
    user_id = input("Enter your user ID: ").strip()
    mt5_account = input("Enter MT5 account number: ").strip()
    mt5_server = input("Enter MT5 server: ").strip()
    auth_token = input("Enter JWT auth token: ").strip()

    if not all([cloud_url, user_id, mt5_account, mt5_server, auth_token]):
        print("❌ All fields are required!")
        return

    print(f"\n🔗 Connecting to: {cloud_url}")
    print(f"👤 User ID: {user_id}")
    print(f"📊 MT5 Account: {mt5_account} on {mt5_server}")
    print("\n⏳ Connecting...")

    # Create and start the relay client
    client = create_relay_client(
        cloud_url=cloud_url,
        user_id=user_id,
        mt5_account=mt5_account,
        mt5_server=mt5_server,
        auth_token=auth_token
    )

    if client:
        print("✅ Connected successfully!")
        print("📡 Relay client is running. Press Ctrl+C to stop.")

        try:
            # Keep the main thread alive
            while client.is_connected:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Shutting down...")
            client.disconnect()
            print("✅ Disconnected.")
    else:
        print("❌ Failed to connect. Check your credentials and try again.")

if __name__ == "__main__":
    main()