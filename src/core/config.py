import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class AppConfig:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.warning(f".env file not found at {env_path}")

    DATA_DIR = BASE_DIR / "data"
    OUTPUT_DIR = DATA_DIR / "output"
    LOGS_DIR = DATA_DIR / "logs"

    DEFAULT_DB_CONNECTION = f"sqlite:///{DATA_DIR}/demo.db"
    
    _raw_key = os.getenv("GOOGLE_API_KEY")
    if _raw_key is not None:
        _raw_key = _raw_key.strip().strip('"').strip("'")
    GEMINI_API_KEY = _raw_key
    GEMINI_MODEL = "gemini-2.5-flash-lite"
    
    MAX_RETRIES = 3

    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError(f"CRITICAL: GOOGLE_API_KEY is missing. Checked path: {cls.env_path}")
        try:
            preview = f"{cls.GEMINI_API_KEY[:6]}...{cls.GEMINI_API_KEY[-4:]}"
            logger.info(f"GOOGLE_API_KEY present. Preview={preview} (len={len(cls.GEMINI_API_KEY)})")
        except Exception:
            logger.info("GOOGLE_API_KEY present. (unable to preview)")
        
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)