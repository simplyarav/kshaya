import pytest
import os
import tempfile
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.encrypted_db import Base, init_db
from app.db.models import User, Role, Case, Evidence, AuditEvent
from app.services.platform.crypto import crypto_service
from app.services.platform.audit_ledger import AuditLedger
from app.services.platform.certificate_generator import CertificateService
from app.services.platform.policy_engine import PolicyEngine
from app.services.platform.offline_verifier import verify_manifest

@pytest.fixture
def db_session():
    # Use standard in-memory sqlite for fast tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_audit_chain_validity(db_session):
    ledger = AuditLedger(db_session)
    
    e1 = ledger.append_event("admin", "LOGIN", "sys", {})
    e2 = ledger.append_event("admin", "ERASE_START", "disk1", {"method": "crypto"})
    e3 = ledger.append_event("admin", "ERASE_DONE", "disk1", {"status": "success"})
    
    assert ledger.verify_chain() is None

def test_audit_chain_tamper_detection(db_session):
    ledger = AuditLedger(db_session)
    
    ledger.append_event("user1", "ACTION_1", "res1", {})
    e2 = ledger.append_event("user1", "ACTION_2", "res2", {})
    ledger.append_event("user1", "ACTION_3", "res3", {})
    
    # Deliberately corrupt an entry to simulate a direct DB file modification
    e2.details = {"hacked": True}
    db_session.commit()
    
    # verify_chain should return the ID of the broken event
    broken_id = ledger.verify_chain()
    assert broken_id == e2.id

def test_certificate_signature_round_trip():
    cert_svc = CertificateService(key_id="test-key-id")
    
    manifest = cert_svc.generate_manifest(
        job_details={"target": "disk1", "method": "crypto"},
        operator_identity="op_user",
        template_key="cryptographic_erase",
        exceptions=[]
    )
    
    assert "signature" in manifest
    assert "Verification Scope: Cryptographic key destruction" in manifest["verification_scope"]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Export pubkey
        pubkey_path = os.path.join(tmpdir, "pub.pem")
        crypto_service.export_public_key(pubkey_path)
        
        # Save manifest
        manifest_path = os.path.join(tmpdir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
            
        # Verify
        is_valid = verify_manifest(manifest_path, pubkey_path)
        assert is_valid is True

        # Tamper manifest
        manifest["operator"] = "hacker"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
            
        is_valid = verify_manifest(manifest_path, pubkey_path)
        assert is_valid is False

def test_policy_engine_rbac_allow_deny(db_session):
    ledger = AuditLedger(db_session)
    engine = PolicyEngine(db_session, ledger)
    
    r_op = Role(name="Operator", permissions=["start_job"])
    r_app = Role(name="Approver", permissions=["approve_exceptions"])
    db_session.add_all([r_op, r_app])
    db_session.commit()
    
    u_op = User(username="op", role_id=r_op.id)
    u_app = User(username="app", role_id=r_app.id)
    db_session.add_all([u_op, u_app])
    db_session.commit()
    
    # Allow path
    assert engine.check_authorization(u_op.id, "start_job") is True
    # Deny path
    assert engine.check_authorization(u_op.id, "approve_exceptions") is False
    assert engine.check_authorization(u_app.id, "start_job") is False
    assert engine.check_authorization(u_app.id, "approve_exceptions") is True

def test_policy_engine_exception_workflow(db_session):
    ledger = AuditLedger(db_session)
    engine = PolicyEngine(db_session, ledger)
    
    r_app = Role(name="Approver", permissions=["approve_exceptions"])
    db_session.add(r_app)
    db_session.commit()
    
    u_app = User(username="approver1", role_id=r_app.id)
    db_session.add(u_app)
    db_session.commit()
    
    req_id = engine.request_exception("operator1", "wipe_mounted", "need to test")
    
    # Unauthorized approval should fail and log DENIED
    success = engine.approve_exception("unauth_user", 999, req_id)
    assert success is False
    
    # Authorized approval
    success = engine.approve_exception(u_app.username, u_app.id, req_id)
    assert success is True
    
    # Verify both reached ledger
    events = db_session.query(AuditEvent).all()
    actions = [e.action for e in events]
    assert "EXCEPTION_REQUESTED" in actions
    assert "EXCEPTION_APPROVAL_DENIED" in actions
    assert "EXCEPTION_APPROVED" in actions
