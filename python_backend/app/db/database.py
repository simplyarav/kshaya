import sqlite3
import os
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

def get_db_connection():
    # Note: In a real environment, you must have pysqlcipher3 or sqlcipher3 installed
    # or the standard sqlite3 compiled with SQLCipher support to use encryption.
    # We will use standard sqlite3 API here which is compatible with sqlcipher3.
    try:
        from pysqlcipher3 import dbapi2 as sqlite3_cipher
    except ImportError:
        # Fallback to standard sqlite3 for scaffolding, 
        # but warn that encryption is missing.
        logger.warning("pysqlcipher3 not found, falling back to standard sqlite3 (UNENCRYPTED!)")
        sqlite3_cipher = sqlite3

    conn = sqlite3_cipher.connect(settings.DB_PATH)
    conn.row_factory = sqlite3_cipher.Row
    # Apply SQLCipher encryption key
    conn.execute(f"PRAGMA key = '{settings.DB_PASSPHRASE}'")
    return conn

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    conn = get_db_connection()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
