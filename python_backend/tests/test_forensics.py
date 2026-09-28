import pytest
import os
import tempfile
import struct
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.encrypted_db import Base
from app.db.models import User, Role, Case, Evidence, AuditEvent
from app.services.platform.policy_engine import PolicyEngine
from app.services.platform.audit_ledger import AuditLedger
from app.services.platform.certificate_generator import CertificateService

from app.services.forensics.case_management import CaseManagementService
from app.services.forensics.image_import import ImageImportService
from app.services.forensics.carving.jpeg import JPEGCarver
from app.services.forensics.carving.executable_risk import check_executable_risk
from app.services.forensics.reconstruction import ReconstructionEngine
from app.services.forensics.confidence_scoring import ConfidenceScorer
from app.services.forensics.reporting import ForensicReportingService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def create_synthetic_image(temp_dir, filename, content_bytes):
    filepath = os.path.join(temp_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content_bytes)
    return filepath

def test_forensics_e2e_happy_path(db_session):
    ledger = AuditLedger(db_session)
    policy = PolicyEngine(db_session, ledger)
    
    # RBAC setup
    r_analyst = Role(name="Analyst", permissions=["analyze_evidence"])
    r_approver = Role(name="Approver", permissions=["approve_reports"])
    db_session.add_all([r_analyst, r_approver])
    db_session.commit()
    
    u_analyst = User(username="analyst", role_id=r_analyst.id)
    u_approver = User(username="approver", role_id=r_approver.id)
    db_session.add_all([u_analyst, u_approver])
    db_session.commit()

    case_mgr = CaseManagementService(db_session, policy, ledger)
    import_svc = ImageImportService(db_session, policy, ledger)
    
    # 1. Create Case & Evidence
    case = case_mgr.create_case(u_analyst.id, u_analyst.username, "CASE-001")
    ev = case_mgr.register_evidence(u_analyst.id, u_analyst.username, case.id, "EV-001")
    
    # 2. Import Image & Hash Baseline
    synthetic_jpeg = b"\x00\x00\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xD9\x00\x00"
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = create_synthetic_image(tmpdir, "img1.bin", synthetic_jpeg)
        
        # Baseline import
        import_svc.import_image(u_analyst.id, u_analyst.username, ev.id, img_path)
        assert ev.original_hash is not None
        
        # 3. Carve
        carver = JPEGCarver()
        candidate = carver.carve(synthetic_jpeg, 0)
        assert candidate is not None
        assert candidate.structure_pass is True
        
        # 4. Reconstruction Score
        recon = ReconstructionEngine()
        recon_res = recon.score_fragment(synthetic_jpeg, aligned=True)
        
        # 5. Confidence Score
        score_res = ConfidenceScorer.calculate_overall(candidate, recon_res)
        assert score_res["grade"] in ["Medium", "High"]
        
        # 6. Report
        cert_svc = CertificateService()
        rep_svc = ForensicReportingService(db_session, cert_svc, policy, ledger)
        
        pdf_bytes = rep_svc.generate_report(u_approver.id, u_approver.username, {"recovered": 1}, is_redacted=True)
        assert pdf_bytes.startswith(b"%PDF")
        
        # We can also verify the manifest structure from DB
        from app.db.models import Certificate
        cert = db_session.query(Certificate).order_by(Certificate.id.desc()).first()
        assert "Redacted forensic analysis report" in cert.manifest_json["verification_scope"]
        
        # Verify Audit Ledger captured these steps
        events = [e.action for e in db_session.query(AuditEvent).all()]
        assert "CASE_CREATED" in events
        assert "EVIDENCE_REGISTERED" in events
        assert "IMAGE_HASH_BASELINE_ESTABLISHED" in events

def test_forensics_negative_path(db_session):
    ledger = AuditLedger(db_session)
    policy = PolicyEngine(db_session, ledger)
    
    # Missing footer JPEG
    synthetic_truncated = b"\x00\x00\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
    
    carver = JPEGCarver()
    candidate = carver.carve(synthetic_truncated, 0)
    
    assert candidate.structure_pass is False
    assert "Missing FFD9 footer" in candidate.structure_details
    
    recon = ReconstructionEngine()
    recon_res = recon.score_fragment(synthetic_truncated, aligned=False)
    
    score_res = ConfidenceScorer.calculate_overall(candidate, recon_res)
    # Score should be Low because structure failed and recon is low
    assert score_res["grade"] == "Low"

def test_architectural_read_only_enforcement():
    """
    Asserts absolutely NO writes occur to evidence files inside forensics module.
    """
    mod_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "services", "forensics")
    
    write_modes = ['"w"', "'w'", '"w+"', "'w+'", '"wb"', "'wb'", '"r+"', "'r+'", '"r+b"', "'r+b'", '"a"', "'a'", '"ab"', "'ab'"]
    destructive_calls = ["os.remove", "os.unlink", "shutil.rmtree"]
    
    for root, _, files in os.walk(mod_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
                
            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                content_lower = content.lower()
                
                # Check for run_command with dry_run=False bypass
                assert "dry_run=false" not in content_lower.replace(" ", ""), f"Found dry_run bypass in {f}"
                
                # Check for write mode open calls
                for mode in write_modes:
                    assert mode not in content, f"Found explicit write-mode open({mode}) in {f}. This violates read-only rules!"
                    
                # Check for OS deletes
                for call in destructive_calls:
                    assert call not in content, f"Found destructive call '{call}' in unauthorized file {f}"
                    
                # Check for pytsk3 write flags if any exist (img_info usually defaults to read-only but ensure no weird flags)
                assert "TSK_IMG_TYPE_EXTERNAL" not in content # etc, just ensure basic read-only
