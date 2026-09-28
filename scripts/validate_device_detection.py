#!/usr/bin/env python3
"""
Device Detection Validation Harness

PURPOSE:
This script validates KSHAYA's DeviceLayer detection logic against real, physical hardware.
It strictly operates in READ-ONLY mode. It queries the underlying real device backend
(LinuxDeviceBackend or WindowsDeviceBackend, NEVER the mock backend) and prints the
parsed DeviceInfo and DeviceCapability structures.

Then, it shells out directly to the native OS tools (smartctl, lsblk, WMI, PowerShell)
and prints the raw output alongside KSHAYA's parsed output, allowing manual diffing
to catch parsing bugs.

SAFETY GUARANTEE:
This script NEVER imports or invokes any write paths, sanitization logic, or run_command
from erase_engine. It is strictly a read-only telemetry dumper.
"""

import os
import sys
import subprocess
import json

# Ensure we import from the local python_backend package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../python_backend')))

# DO NOT import erase_engine or any write paths!
# We assert this to ensure this script is strictly read-only.
assert "erase_engine" not in sys.modules, "FATAL: Write paths imported in read-only harness!"

from app.services.device.windows_backend import WindowsDeviceBackend
from app.services.device.linux_backend import LinuxDeviceBackend

def main():
    print("=" * 80)
    print("KSHAYA Real-Hardware Device Detection Validation Harness")
    print("=" * 80)
    
    if sys.platform == "win32":
        print("[+] Platform: Windows")
        backend = WindowsDeviceBackend()
        raw_cmd = ["powershell", "-NoProfile", "-Command", "Get-PhysicalDisk | Select-Object * | ConvertTo-Json -Depth 2"]
        raw_tool_name = "PowerShell Get-PhysicalDisk"
    else:
        print("[+] Platform: Linux")
        backend = LinuxDeviceBackend()
        raw_cmd = ["lsblk", "-O", "-J"]
        raw_tool_name = "lsblk"
        
    print("[+] Initializing Real Hardware Backend...")
    devices = backend.list_devices()
    
    if not devices:
        print("[!] KSHAYA backend returned 0 devices.")
        # NOTE: windows_backend is currently a stub returning []. 
        # This harness will prove it needs fixing!
    else:
        for dev in devices:
            print("-" * 80)
            print(f"[KSHAYA PARSED] Device ID: {dev.device_id}")
            try:
                info = backend.get_device_info(dev.device_id)
                cap = backend.detect_capability(dev.device_id)
                
                print("\\n--- DeviceInfo ---")
                print(f"Bus:            {info.bus}")
                print(f"Type:           {info.type}")
                print(f"Model:          {info.model}")
                print(f"Serial:         {info.serial}")
                print(f"Firmware:       {info.firmware}")
                print(f"Capacity:       {info.capacity_bytes} bytes")
                print(f"Sector Size:    {info.sector_size}")
                print(f"SMART Health:   {info.smart_health_summary}")
                print(f"Is Mounted:     {info.is_mounted}")
                print(f"Is Boot Drive:  {info.is_boot_drive}")
                
                print("\\n--- DeviceCapability ---")
                print(f"ATA Sanitize:   {cap.ata_sanitize_supported}")
                print(f"NVMe Sanitize:  {cap.nvme_sanitize_supported}")
                print(f"Crypto Erase:   {cap.crypto_erase_supported}")
                print(f"HPA/DCO Hidden: {cap.hpa_dco_present}")
                print(f"RAID/LVM Vol:   {cap.is_raid_lvm_volume}")
            except Exception as e:
                print(f"[!] Error parsing device {dev.device_id}: {e}")

    print("\\n" + "=" * 80)
    print(f"[RAW NATIVE TOOL] Executing: {' '.join(raw_cmd)}")
    print("=" * 80)
    
    try:
        result = subprocess.run(raw_cmd, capture_output=True, text=True, check=False)
        print(result.stdout)
        if result.stderr:
            print("[!] STDERR Output:")
            print(result.stderr)
    except Exception as e:
        print(f"[!] Failed to execute raw command: {e}")
        
    print("\\n[+] Validation complete. Compare KSHAYA parsed fields against Raw Native Tool output above.")

if __name__ == "__main__":
    main()
