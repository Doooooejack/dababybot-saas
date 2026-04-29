import MetaTrader5 as mt5
import requests
import time

MT5_LOGIN = 12345678  # <-- Your MT5 login
MT5_PASSWORD = "your_mt5_password"  # <-- Your MT5 password
MT5_SERVER = "YourBroker-Server"  # <-- Your MT5 server
SYNC_URL = "https://your-render-backend/api/mt5/sync"  # <-- Your backend sync endpoint
SYNC_TOKEN = "your_secure_sync_token"  # <-- Use a strong secret token


def fetch_account_info():
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print("MT5 init failed")
        return None
    info = mt5.account_info()
    mt5.shutdown()
    return info._asdict() if info else None

def sync_to_backend(account_info):
    headers = {"Authorization": f"Bearer {SYNC_TOKEN}"}
    resp = requests.post(SYNC_URL, json=account_info, headers=headers)
    print("Sync response:", resp.status_code, resp.text)

if __name__ == "__main__":
    while True:
        info = fetch_account_info()
        if info:
            sync_to_backend(info)
        time.sleep(60)  # Sync every 60 seconds
