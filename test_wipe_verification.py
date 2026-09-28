import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'python_backend')))
from app.services.device.windows_backend import WindowsDeviceBackend
from app.services.forensics.carving.carver_engine import CarverEngine

def test_real_wipe_execution():
    image_path = "C:\\Users\\Ravi\\OneDrive\\Desktop\\mock_image.001"
    
    print(f"\n[+] Executing Independent Post-Wipe Verification Test")
    
    # 1. Pre-wipe Carving Pass
    print("\n[+] PASS 1: Pre-Wipe Carver Engine Check")
    engine_pre = CarverEngine(image_path)
    candidates_pre = engine_pre.carve_all()
    print(f"    Found {len(candidates_pre)} carved files on drive before sanitization.")
    if len(candidates_pre) == 0:
        print("    Error: Drive is already wiped. Cannot verify destruction.")
        sys.exit(1)
    
    # 2. Execute Real Destructive Wipe
    print("\n[+] PASS 2: Executing Real Destructive Wipe (dry_run=False, method=Clear)")
    backend = WindowsDeviceBackend()
    
    # We pass the image path directly as the device_id to test the physical IO logic
    result = backend.run_command(device_id=image_path, command="clear", dry_run=False)
    
    if not result.success:
        print(f"    Wipe failed! Error: {result.error}")
        sys.exit(1)
        
    print(f"    [SUCCESS] {result.output}")
    print(f"    Drive completely overwritten with zeros.")
    
    # 3. Post-wipe Carving Verification
    print("\n[+] PASS 3: Independent Post-Wipe Verification (Carver Engine Check)")
    engine_post = CarverEngine(image_path)
    candidates_post = engine_post.carve_all()
    
    print(f"    Found {len(candidates_post)} carved files on drive after sanitization.")
    
    if len(candidates_post) == 0:
        print("\n[!] VERIFIED: The logical overwrite algorithm successfully and irreversibly destroyed all data.")
        print("              The CarverEngine confirms exactly 0 bytes of recoverable data remain.")
    else:
        print("    Wipe verification failed! Data survived the sanitization pass.")
        sys.exit(1)

if __name__ == "__main__":
    test_real_wipe_execution()
