# KSHAYA Real-Hardware Validation

## 1. Device Detection Validation
To validate that KSHAYA accurately parses physical hardware metadata (Serial, SMART, Sanitize capabilities) without accidentally triggering any write commands, use the validation harness.

### Running on Windows
Ensure you are running an Administrator PowerShell, as raw disk access requires elevation:
\\\powershell
cd \"C:\Users\Ravi\OneDrive\Desktop\KSHAYA 1.0\"
python scripts\validate_device_detection.py
\\\

### Running on Linux
Ensure you run with sudo privileges to allow \lsblk\ and backend probes to access block devices:
\\\ash
cd /path/to/kshaya
sudo python3 scripts/validate_device_detection.py
\\\

### What to Check For
- Does the \Serial\ reported by KSHAYA perfectly match the serial number physically printed on the USB test drive?
- Does KSHAYA's parsed output match the JSON dump from the native tool (PowerShell/lsblk) printed at the bottom?
- Note: If KSHAYA returns 0 devices on Windows, the \windows_backend.py\ stub needs to be fully implemented based on the raw PowerShell output provided by this script.
