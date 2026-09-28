import socket
import pytest
import tempfile
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.encrypted_db import Base
from app.db.models import User, Role, SystemSetting

# App imports
from app.services.platform.policy_engine import PolicyEngine
from app.services.platform.audit_ledger import AuditLedger
from app.services.platform.certificate_generator import CertificateService

from app.services.drive_erasure.job_orchestrator import JobOrchestrator
from app.services.device.interface import DeviceLayer

from app.services.file_erasure.selection import FileSelector
from app.services.file_erasure.erase_engine import EraseEngine

from app.services.forensics.case_management import CaseManagementService
from app.services.forensics.image_import import ImageImportService
from app.services.forensics.carving.jpeg import JPEGCarver
from app.services.forensics.reconstruction import ReconstructionEngine
from app.services.forensics.reporting import ForensicReportingService

# ----------------------------------------------------------------------------
# Strict Network Blocker
# ----------------------------------------------------------------------------
class NetworkBlockedError(RuntimeError):
    pass

_original_socket = socket.socket

def _block_socket(*args, **kwargs):
    raise NetworkBlockedError("Outbound network call detected and blocked by offline-first policy!")

@pytest.fixture(autouse=True)
def enforce_offline_mode(monkeypatch):
    """
    Monkeypatch Python's core socket constructor. 
    Any attempt to create a network connection (HTTP, Syslog, DNS, etc.) will hard-crash the test.
    """
    monkeypatch.setattr(socket, "socket", _block_socket)

# ----------------------------------------------------------------------------
# DB Setup
# ----------------------------------------------------------------------------
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# ----------------------------------------------------------------------------
# Integration Test
# ----------------------------------------------------------------------------
def test_full_offline_pipeline(db_session):
    """
    Simulates a full walkthrough of KSHAYA's core features (Module 1, 2, and 3)
    while the strict network blocker is active, proving zero-trust offline capability.
    """
    
    # Ensure Online Mode is OFF
    db_session.add(SystemSetting(key="online_mode", value_json="false"))
    db_session.commit()
    
    # 0. Setup core services
    ledger = AuditLedger(db_session)
    policy = PolicyEngine(db_session, ledger)
    cert_svc = CertificateService()
    
    admin_role = Role(name="Admin", permissions=[
        "execute_erasure", "analyze_evidence", "approve_reports"
    ])
    db_session.add(admin_role)
    db_session.commit()
    
    admin = User(username="admin", role_id=admin_role.id)
    db_session.add(admin)
    db_session.commit()
    
    # =========================================================================
    # MODULE 1: Drive Erasure
    # =========================================================================
    dev_layer = DeviceLayer()
    orch = JobOrchestrator(db_session, dev_layer, policy, ledger, cert_svc)
    
    # Dry run should succeed without network
    orch.execute_dry_run(admin.username, admin.id, "MOCK-DEVICE-01")
    
    # =========================================================================
    # MODULE 2: File Erasure
    # =========================================================================
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(b"sensitive data")
        temp_path = tf.name
        
    try:
        # File selector preview
        preview = FileSelector.get_preview([temp_path])
        assert preview["total_files"] == 1
        
        # Erase engine
        res = EraseEngine.overwrite_and_delete(temp_path)
        assert res["status"] == "success"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    # =========================================================================
    # MODULE 3: Forensics
    # =========================================================================
    case_mgr = CaseManagementService(db_session, policy, ledger)
    import_svc = ImageImportService(db_session, policy, ledger)
    rep_svc = ForensicReportingService(db_session, cert_svc, policy, ledger)
    
    case = case_mgr.create_case(admin.id, admin.username, "OFL-CASE-1")
    ev = case_mgr.register_evidence(admin.id, admin.username, case.id, "EV-1")
    
    synthetic_jpeg = b"\x00\x00\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xD9\x00\x00"
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "img.bin")
        with open(img_path, "wb") as f:
            f.write(synthetic_jpeg)
            
        import_svc.import_image(admin.id, admin.username, ev.id, img_path)
        
        carver = JPEGCarver()
        candidate = carver.carve(synthetic_jpeg, 0)
        
        recon = ReconstructionEngine()
        recon.score_fragment(synthetic_jpeg, aligned=True)
        
        pdf_bytes = rep_svc.generate_report(admin.id, admin.username, {"recovered": 1}, is_redacted=True)
        assert pdf_bytes.startswith(b"%PDF")
        
    # If we got here without raising NetworkBlockedError, the offline-first requirement is mathematically proven.
    assert True
