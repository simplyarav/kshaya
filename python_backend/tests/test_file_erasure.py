import pytest
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.encrypted_db import Base
from app.db.models import User, Role, AuditEvent, ReviewQueueItem
from app.services.platform.policy_engine import PolicyEngine
from app.services.platform.audit_ledger import AuditLedger
from app.services.platform.certificate_generator import CertificateService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_audit_redaction_design(db_session):
    """
    Ensures that the hashed payload ONLY contains redacted details, 
    and the unredacted paths sit outside the hash.
    """
    ledger = AuditLedger(db_session)
    cert_svc = CertificateService()
    
    event = ledger.append_event(
        actor_username="op_user",
        action="FILE_ERASED",
        resource_id="job-1",
        details={"path": "[REDACTED]"},
        sensitive_details={"path": "C:\\Users\\Secret\\passwords.txt"}
    )
    
    # Prove the event_hash did NOT include sensitive_details
    payload = {
        "actor": "op_user",
        "action": "FILE_ERASED",
        "resource_id": "job-1",
        "details": {"path": "[REDACTED]"},
        "prev_hash": None
    }
    from app.services.platform.crypto import crypto_service
    expected_hash = crypto_service.sha512(json.dumps(payload, sort_keys=True).encode("utf-8")).hex()
    assert event.event_hash == expected_hash, "Sensitive details were incorrectly hashed!"
    
    # Prove they were still stored
    db_event = db_session.query(AuditEvent).first()
    assert db_event.sensitive_details["path"] == "C:\\Users\\Secret\\passwords.txt"
    assert db_event.details["path"] == "[REDACTED]"

def test_architectural_chokepoint_file_erasure():
    """
    Scans the ENTIRE app/services/file_erasure/ tree.
    1. Only erase_engine.py is allowed to perform OS file remove/unlink operations.
    2. No file in this module is allowed to call run_command with dry_run=False.
    """
    mod_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "services", "file_erasure")
    
    destructive_calls = ["os.remove", "os.unlink", "shutil.rmtree"]
    
    for root, _, files in os.walk(mod_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
                
            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                
                # Condition 1: Check for dry_run=False bypass
                assert "dry_run=false" not in content.lower().replace(" ", ""), f"Found dry_run bypass in {f}"
                
                # Condition 2: Check for destructive OS calls outside erase_engine
                if f != "erase_engine.py":
                    for call in destructive_calls:
                        assert call not in content, f"Found destructive call '{call}' in unauthorized file {f}"
