#!/usr/bin/env python3
"""
Real Test Image Preparation Guide

This script guides the user through manually preparing a REAL USB drive
to be used as the ground-truth testing artifact for the forensic pipeline.
"""

import sys
import os

def main():
    print("=" * 80)
    print("KSHAYA Real-Hardware Forensic Image Preparation Guide")
    print("=" * 80)
    print("\\nThis guide will walk you through creating a real-world test artifact (.dd) ")
    print("to validate the KSHAYA carving and reconstruction pipeline.\\n")
    
    input("Press Enter to begin Step 1...")
    print("\\nSTEP 1: FORMATTING")
    print("- Insert your dedicated USB test drive.")
    print("- Format it using your OS (Windows Disk Management or Linux mkfs).")
    print("- Recommended format: FAT32 or NTFS.")
    print("- WARNING: Make sure you are formatting the correct drive!")
    
    input("\\nPress Enter to proceed to Step 2...")
    print("\\nSTEP 2: POPULATING SAMPLE FILES")
    print("- Copy a diverse set of real files onto the root of the USB drive.")
    print("- Ensure you include at least one of each MVP format: ")
    print("  * JPEG (.jpg) \\n  * PNG (.png) \\n  * PDF (.pdf) \\n  * ZIP or DOCX (.zip/.docx) \\n  * SQLite (.db/.sqlite)")
    
    input("\\nPress Enter to proceed to Step 3...")
    print("\\nSTEP 3: DELETING AND FRAGMENTING")
    print("- Normally delete (Shift+Delete on Windows, or rm on Linux) some of the files.")
    print("- DO NOT use a secure eraser — the files must remain forensically present.")
    print("- Optional: To test fragmentation, copy a large file, delete it, and then write")
    print("  several smaller files to partially overwrite its blocks.")
    
    input("\\nPress Enter to proceed to Step 4...")
    print("\\nSTEP 4: CREATING THE RAW IMAGE (.dd)")
    print("Now, create a raw bit-for-bit image of the USB drive.")
    if sys.platform == 'win32':
        print("- Since you are on Windows, you can use FTK Imager or rawcopy to create the .dd file.")
        print("- Example FTK Imager CLI: ftkimager \\\\.\\PhysicalDriveX C:\\path\\to\\real_test_image.dd --e01")
        print("  (Replace PhysicalDriveX with the correct drive number, and you can use .dd format).")
    else:
        print("- Since you are on Linux, use dd:")
        print("- sudo dd if=/dev/sdX of=real_test_image.dd bs=4M status=progress")
    
    print("\\nOnce you have 'real_test_image.dd', you will run:")
    print("pytest tests/test_real_recovery_pipeline.py --allow-real-hardware --image-path path/to/real_test_image.dd")
    print("\\nDone. Follow these steps carefully.")

if __name__ == "__main__":
    main()
