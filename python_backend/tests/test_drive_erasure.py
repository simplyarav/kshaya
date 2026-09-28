import pytest
import os
import ast
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.encrypted_db import Base
from app.db.models import User, Role, Case, Evidence, Certificate
from app.services.platform.policy_engine import PolicyEngine
from app.services.platform.audit_ledger import AuditLedger
from app.services.platform.certificate_generator import CertificateService
from app.services.device.interface import DeviceLayer, SafetyViolation
from app.services.drive_erasure.job_orchestrator import JobOrchestrator
from app.services.device.models import DeviceInfo, DeviceCapability, CommandResult

class MockDeviceBackend:
    def get_device_info(self, device_id: str):
        return DeviceInfo(
            device_id=device_id,
            bus="NVMe",
            type="NVMe SSD",
            model="Test NVMe",
            serial="TEST-SERIAL-001",
            firmware="2.0",
            capacity_bytes=1000,
            sector_size=4096,
            smart_health_summary="OK"
        )
    
    def detect_capability(self, device_id: str):
        return DeviceCapability(
            device_type="NVMe SSD",
            ata_sanitize_supported=False,
            nvme_sanitize_supported=True,
            nvme_format_supported=True,
            hpa_dco_present=False,
            raid_lvm_member=False,
            encryption_indicators=False,
            mounted=False,
            boot_volume=False,
            firmware_sanitize_available=True
        )

    def run_command(self, device_id, command, dry_run):
        return CommandResult(success=True, output="Mocked", dry_run=dry_run)
        
    def list_devices(self):
        return []

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_dry_run_prerequisite_and_serial_check(db_session):
    ledger = AuditLedger(db_session)
    policy = PolicyEngine(db_session, ledger)
    cert = CertificateService("key-123")
    dev_layer = DeviceLayer(backend=MockDeviceBackend())
    
    # Setup RBAC
    r_op = Role(name="Operator", permissions=["execute_erasure"])
    db_session.add(r_op)
    db_session.commit()
    u_op = User(username="op", role_id=r_op.id)
    db_session.add(u_op)
    db_session.commit()

    orch = JobOrchestrator(db_session, dev_layer, policy, ledger, cert)
    
    # 1. Try real run without prior dry_run
    with pytest.raises(SafetyViolation, match="Mandatory dry-run simulation has not been performed"):
        orch.execute_job(u_op.username, u_op.id, "test_dev", "NVMe Crypto Erase (Purge)", "TEST-SERIAL-001")
        
    # 2. Perform dry-run
    res = orch.execute_dry_run(u_op.username, u_op.id, "test_dev")
    assert res["status"] == "simulation_complete"
    
    # 3. Try real run with WRONG typed serial
    with pytest.raises(SafetyViolation, match="Typed serial confirmation does not match"):
        orch.execute_job(u_op.username, u_op.id, "test_dev", "NVMe Crypto Erase (Purge)", "WRONG-SERIAL")

    # 4. Try real run with correct typed serial
    cert_obj = orch.execute_job(u_op.username, u_op.id, "test_dev", "NVMe Crypto Erase (Purge)", "TEST-SERIAL-001")
    assert cert_obj is not None
    assert cert_obj.pdf_bytes is not None

def test_deterministic_pdf_generation(db_session):
    cert = CertificateService("key-123")
    manifest = cert.generate_manifest(
        job_details={"target": "disk1", "method": "crypto"},
        operator_identity="op_user",
        template_key="cryptographic_erase",
        exceptions=[]
    )
    
    pdf_bytes_1 = cert.generate_pdf(manifest)
    pdf_bytes_2 = cert.generate_pdf(manifest)
    
    # Must be provably byte-identical
    assert pdf_bytes_1 == pdf_bytes_2, "PDF generation is not deterministic!"

def test_architectural_chokepoint_dry_run():
    """
    Scans the ENTIRE app/ source tree and asserts the literal syntax 
    'dry_run=False' appears in exactly one file total: job_orchestrator.py.
    """
    app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app")
    
    files_with_dry_run_false = []
    
    for root, _, files in os.walk(app_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
                
            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                # Remove spaces to catch dry_run=False, dry_run = False, etc.
                if "dry_run=false" in content.lower().replace(" ", ""):
                    files_with_dry_run_false.append(f)

    # Allow exactly one hit: job_orchestrator.py
    # But wait, verification.py ALSO had dry_run=False because I originally drafted it calling it.
    # The prompt explicitly requires "job_orchestrator.py must be the only thing in this module allowed to call DeviceLayer.run_command() with dry_run=False."
    # I need to ensure verification.py does NOT have dry_run=False. I'll update it before running this.
    assert "job_orchestrator.py" in files_with_dry_run_false
    assert len(files_with_dry_run_false) == 1, f"Found dry_run=False in multiple files: {files_with_dry_run_false}"
