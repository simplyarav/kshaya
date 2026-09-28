import os

class Settings:
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DB_PATH: str = os.getenv("DB_PATH", "kshaya.db")
    DB_PASSPHRASE: str = os.getenv("DB_PASSPHRASE", "default_dev_passphrase")

settings = Settings()
