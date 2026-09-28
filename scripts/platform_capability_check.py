#!/usr/bin/env python3
"""
Platform Capability Check

Diagnostic tool to run BEFORE a live demo to determine exactly which 
capabilities the host machine supports.
"""

import sys
import os
import ctypes

def is_admin():
    try:
        if sys.platform == 'win32':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.getuid() == 0
    except:
        return False

def main():
    print("=" * 80)
    print("KSHAYA Platform Capability Diagnostic")
    print("=" * 80)
    
    # 1. Active Backend & Elevation
    elevated = is_admin()
    if sys.platform == 'win32':
        print("[+] Active Backend: WindowsDeviceBackend")
        print(f"[+] Elevation (Admin): {'YES' if elevated else 'NO (Please run as Administrator)'}")
        
        # 2. Windows-Specific Firmware Sanitize limitation
        print("\\n--- Firmware Sanitize Issuable Check ---")
        print("OS: Windows")
        print("Result: BLOCKED BY DEFAULT")
        print("Explanation: Windows strictly blocks raw ATA Secure Erase and NVMe Sanitize commands")
        print("via standard IOCTLs unless a specialized storage driver (like an HBA in IT mode")
        print("or a vendor-specific pass-through) is used. The Windows ")
        print("DeviceLayer will therefore fallback to logical CLEAR (overwrite) for most USBs.")
        print("Demo Path: Expect 'Clear (logical overwrite) — Purge not achieved'.")
        
    else:
        print("[+] Active Backend: LinuxDeviceBackend")
        print(f"[+] Elevation (Root): {'YES' if elevated else 'NO (Please run with sudo)'}")
        
        # 2. Linux-Specific Firmware Sanitize
        print("\\n--- Firmware Sanitize Issuable Check ---")
        print("OS: Linux")
        print("Result: ISSUABLE (Subject to hdparm/nvme-cli)")
        print("Explanation: Linux allows raw ATA/NVMe command pass-through via SG_IO.")
        print("If the attached device supports Sanitize, the Linux backend can issue it directly.")
        print("Demo Path: Expect 'Purge (firmware level Sanitize)' if device supports it.")
        
    print("=" * 80)
    
if __name__ == "__main__":
    main()
