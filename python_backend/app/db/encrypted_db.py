import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

from ..core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# We fall back to standard sqlite3 if pysqlcipher3 isn't available for scaffolding
try:
    import pysqlcipher3
    DB_URL = f"sqlite+pysqlcipher://:{settings.DB_PASSPHRASE}@/{settings.DB_PATH}?cipher=sqlcipher"
except ImportError:
    logger.warning("pysqlcipher3 not found, falling back to standard sqlite3 (UNENCRYPTED!)")
    DB_URL = f"sqlite:///{settings.DB_PATH}"

engine = create_engine(DB_URL, echo=False)

if DB_URL.startswith("sqlite://"):
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        # We simulate the key pragmas even for standard sqlite if it was compiled with it
        cursor = dbapi_connection.cursor()
        cursor.execute(f"PRAGMA key = '{settings.DB_PASSPHRASE}'")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create tables and apply defense-in-depth DB triggers."""
    Base.metadata.create_all(bind=engine)
    
    # Apply SQLite trigger for append-only audit_events table.
    # Note: This BEFORE UPDATE/DELETE trigger is defense-in-depth at the application DB layer,
    # not a hard security boundary (a raw file-level SQLite client could bypass triggers).
    # The actual tamper-evidence guarantee is the hash-linked, signed chain in AuditLedger,
    # where verify_chain() proves/disproves tampering.
    with engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text(
            "CREATE TRIGGER IF NOT EXISTS trg_audit_events_no_update "
            "BEFORE UPDATE ON audit_events "
            "BEGIN SELECT RAISE(ABORT, 'Updates are strictly prohibited on the audit ledger'); END;"
        ))
        conn.execute(text(
            "CREATE TRIGGER IF NOT EXISTS trg_audit_events_no_delete "
            "BEFORE DELETE ON audit_events "
            "BEGIN SELECT RAISE(ABORT, 'Deletions are strictly prohibited on the audit ledger'); END;"
        ))
