import os
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.core.config import AppConfig

CHINOOK_URL = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"

def download_chinook():
    print("Downloading Chinook Database (Real-world Schema)...")
    
    response = requests.get(CHINOOK_URL)
    response.raise_for_status()
    
    target_path = AppConfig.DATA_DIR / "chinook.db"
    
    with open(target_path, "wb") as f:
        f.write(response.content)
        
    print(f"Download complete: {target_path}")
    print(f"   Size: {os.path.getsize(target_path) / 1024:.2f} KB")

if __name__ == "__main__":
    download_chinook()