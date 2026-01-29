import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
# Cross-platform data path: prefer env DATA_PATH, else project Data/
DATA_DIR = Path(os.getenv("DATA_PATH", str(BASE_DIR / "Data")))
INDEX_DIR = BASE_DIR / "vectorstore"

def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

def get_openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "")
