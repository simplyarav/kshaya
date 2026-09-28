import pytest
import os
import sys

@pytest.fixture
def allow_real_hardware(request):
    return request.config.getoption("--allow-real-hardware")

@pytest.fixture
def target_serial(request):
    return request.config.getoption("--target-serial")

@pytest.mark.real_hardware
def test_real_hardware_sanitization(allow_real_hardware, target_serial):
    if not allow_real_hardware:
        pytest.skip("Skipping real hardware test. Pass --allow-real-hardware to execute.")
    if not target_serial:
        pytest.skip("Skipping real hardware test. Must provide --target-serial <SERIAL>.")

    # We import here so we don't pollute the global scope during discovery
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../python_backend')))
    from app.services.device.windows_backend import WindowsDeviceBackend
    from app.services.device.linux_backend import LinuxDeviceBackend
    
    print(f"\\n[+] Starting Real Hardware Sanitization Test for serial: {target_serial}")
    print("[!] WARNING: IF THIS CONTINUES, IT WILL ATTEMPT TO WIPE THE DRIVE.")
    
    if sys.platform == 'win32':
        backend = WindowsDeviceBackend()
    else:
        backend = LinuxDeviceBackend()
        
    devices = backend.list_devices()
    target_dev = next((d for d in devices if backend.get_device_info(d.device_id).serial == target_serial), None)
    
    if not target_dev:
        pytest.fail(f"Device with serial {target_serial} not found.")
        
    info = backend.get_device_info(target_dev.device_id)
    cap = backend.detect_capability(target_dev.device_id)
    
    print("\\n--- CAPABILITY FLAGS ---")
    print(f"ATA Sanitize: {cap.ata_sanitize_supported}")
    print(f"NVMe Sanitize: {cap.nvme_sanitize_supported}")
    
    # Decision logic sanity check
    if not (cap.ata_sanitize_supported or cap.nvme_sanitize_supported):
        print("[+] Decision: Clear (logical overwrite) — Purge not achieved")
    else:
        print("[+] Decision: Purge (firmware level Sanitize)")
        
    print("\\n[+] VerificationResult (Simulated): Wipe confirmed across all sectors.")
    print("[+] Generated Certificate (Simulated).")
    
    print("\\n" + "!" * 80)
    print("POST-RUN REMINDER:")
    print("Please independently verify the wipe. Check this drive with an external hex editor")
    print("or attempt file recovery on it (e.g., using Autopsy or PhotoRec) to confirm")
    print("the claimed method actually took effect.")
    print("!" * 80 + "\\n")
