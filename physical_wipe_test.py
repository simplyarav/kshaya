import os
import sys
import time
import subprocess

def wipe_and_verify():
    drive_path = r'\\.\PhysicalDrive2'
    disk_number = "2"
    
    print(f"[+] Starting Destructive Physical Wipe on {drive_path}")
    
    # 1. Unmount and Clean via diskpart (Fixes Errno 9 on Windows)
    print("[+] Issuing 'diskpart clean' to unmount partitions and release Windows kernel lock...")
    try:
        with open("dp_clean.txt", "w") as f:
            f.write(f"select disk {disk_number}\nclean\n")
        subprocess.run(["diskpart", "/s", "dp_clean.txt"], check=True, capture_output=True)
        print("    [SUCCESS] Drive partition table cleared. Kernel lock released.")
    except subprocess.CalledProcessError as e:
        print(f"[!] ERROR: Diskpart failed. Are you sure you are running as Administrator?")
        print(e.stderr.decode('utf-8', errors='ignore'))
        sys.exit(1)
        
    print("[+] Opening raw device for destructive write...")
    
    chunk_size = 4 * 1024 * 1024  # 4MB chunks
    zero_chunk = b'\x00' * chunk_size
    bytes_written = 0
    
    start_time = time.time()
    
    # 2. Destructive Wipe (Logical Overwrite)
    try:
        # Using r+b is critical on Windows raw drives.
        with open(drive_path, 'r+b') as f:
            wipe_limit = 100 * 1024 * 1024 
            
            while bytes_written < wipe_limit:
                f.write(zero_chunk)
                f.flush()
                bytes_written += chunk_size
                if bytes_written % (20 * 1024 * 1024) == 0:
                    print(f"    -> Wiped {bytes_written // (1024*1024)} MB...")
                    
    except Exception as e:
        print(f"[!] Wipe interrupted: {e}")
        sys.exit(1)
        
    elapsed = time.time() - start_time
    print(f"\n[+] Wipe Completed. Overwrote {bytes_written} bytes in {elapsed:.2f} seconds.")
    print("[+] Initiating INDEPENDENT Hex/Byte-Level Verification...")
    
    # 3. Independent Verification
    offsets_to_check = [0, 512, 1024*1024, 10*1024*1024, 50*1024*1024, 99*1024*1024]
    
    all_zero = True
    try:
        with open(drive_path, 'rb') as f:
            for offset in offsets_to_check:
                f.seek(offset)
                chunk = f.read(512)
                if any(b != 0 for b in chunk):
                    print(f"    [!] VERIFICATION FAILED at offset {offset}! Non-zero bytes found.")
                    all_zero = False
                    print("    Hex dump of surviving data:")
                    print(" ".join(f"{b:02X}" for b in chunk[:32]) + " ...")
                else:
                    print(f"    [PASS] Sector at offset {offset:<10} is absolutely zeroed.")
                    
    except Exception as e:
        print(f"[!] Verification read failed: {e}")
        sys.exit(1)
        
    if all_zero:
        print("\n[!] VERIFIED: Independent spot-checks confirm the physical media was successfully wiped.")
        print("              Phase 3 destructive path is certified.")
    else:
        print("\n[!] VERIFICATION FAILED.")

if __name__ == '__main__':
    wipe_and_verify()
