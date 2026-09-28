import pytest
import os
import sys

@pytest.fixture
def allow_real_hardware(request):
    return request.config.getoption("--allow-real-hardware")

@pytest.fixture
def image_path(request):
    return request.config.getoption("--image-path")

@pytest.mark.real_hardware
def test_real_recovery_pipeline(allow_real_hardware, image_path):
    if not allow_real_hardware:
        pytest.skip("Skipping real hardware test. Pass --allow-real-hardware.")
    if not image_path or not os.path.exists(image_path):
        pytest.skip("Skipping real recovery test. Must provide a valid --image-path.")

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../python_backend')))
    
    from app.services.forensics.image_import import ImageImporter
    from app.services.forensics.carving.carver_engine import CarverEngine
    from app.services.forensics.carving.confidence_scoring import ConfidenceScorer
    
    # ---------------------------------------------------------
    # PART A: INTEGRATION TEST FOR HASH MISMATCH (GAP 5)
    # ---------------------------------------------------------
    print(f"\n[+] Gap 5: Hash Mismatch Integration Test (Production Mode)")
    
    class MockEvidence:
        def __init__(self):
            self.id = 1
            self.evidence_tag = "EVID-001"
            self.original_hash = None
            
    class MockDB:
        def __init__(self):
            self.evidence = MockEvidence()
        def query(self, *args):
            return self
        def filter(self, *args):
            return self
        def first(self):
            return self.evidence
        def commit(self):
            pass
            
    class MockPolicy:
        def check_authorization(self, user_id, action): return True
        
    class MockAudit:
        def __init__(self):
            self.events = []
        def append_event(self, actor_username, action, resource_id, details, sensitive_details):
            self.events.append(action)

    db = MockDB()
    policy = MockPolicy()
    audit = MockAudit()
    
    prod_importer = ImageImporter.for_api(db=db, policy=policy, audit=audit)
    
    # 1st Import (Baseline)
    meta = prod_importer.import_image(image_path, user_id=1, username="analyst1", evidence_id=1)
    print(f"    Baseline established: {meta['hash']}")
    
    # Flip a byte deliberately
    corrupt_path = image_path + ".corrupt"
    with open(image_path, "rb") as f_in, open(corrupt_path, "wb") as f_out:
        data = bytearray(f_in.read())
        data[0] = data[0] ^ 0xFF # Flip first byte
        f_out.write(data)
        
    # 2nd Import (Mismatch)
    try:
        prod_importer.import_image(corrupt_path, user_id=1, username="analyst1", evidence_id=1)
        pytest.fail("Failed to hard-block on hash mismatch!")
    except Exception as e:
        print(f"    Correctly hard-blocked on drift! Exception: {e}")
        assert "IMAGE_HASH_MISMATCH" in audit.events
        print("    Audit event IMAGE_HASH_MISMATCH successfully logged.")
        
    os.remove(corrupt_path)
    print("    [PASS] Gap 5 Hash Mismatch logic is sound.")

    # ---------------------------------------------------------
    # PART B: THE CARVING PIPELINE (GAPS 1-4)
    # ---------------------------------------------------------
    print(f"\n[+] Starting Real Recovery/Carving Pipeline Test on: {image_path}")
    
    # 1. Image Import & Hash Validation (STANDALONE MODE)
    print("\n[+] Step 1: Image Import & Hash Validation (Standalone)")
    importer = ImageImporter.for_script()
    image_meta = importer.import_image(image_path)
    print(f"    Image size: {image_meta.get('size')} bytes")
    
    # 2. Filesystem Parsing & Carving
    print("\n[+] Step 2: Carving All Formats & Scanning Regions")
    engine = CarverEngine(image_path)
    candidates = engine.carve_all()
    print(f"    Carved {len(candidates)} raw candidates.")
    
    # 3. Confidence Scoring
    print("\n[+] Step 3: Confidence Scoring (6-Dimension Explainable Score)")
    scorer = ConfidenceScorer()
    scored_candidates = []
    for cand in candidates:
        score_result = scorer.score_candidate(cand)
        scored_candidates.append(score_result)
        
    print("\n--- CARVING RESULTS SUMMARY ---")
    for res in scored_candidates:
        print(f"File: {res.filename}")
        print(f"  Final Score: {res.confidence_score}/100")
        print(f"  Explanation: {res.explanation_string}")
        print("  -" * 60)
        
    print("\n[!] Pipeline completed successfully. Review output for specific Gap requirements.")
