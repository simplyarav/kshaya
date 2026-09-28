import struct
import zlib
import os

image_path = "C:\\Users\\Ravi\\OneDrive\\Desktop\\mock_image.001"
with open(image_path, "wb") as f:
    f.write(b'\x00' * (50 * 1024 * 1024))

with open(image_path, "r+b") as f:
    # 0. Healthy JPEG at 1MB
    f.seek(1 * 1024 * 1024)
    f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00\x43\x00' + (b'\x11' * 64) + b'\xFF\xD9')

    # 1. Inject healthy ZIP
    f.seek(3 * 1024 * 1024)
    zip_data = b'PK\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00PK\x05\x06' + (b'\x00' * 20)
    f.write(zip_data)
    
    # 2. Inject healthy SQLite
    f.seek(4 * 1024 * 1024)
    sqlite_data = b'SQLite format 3\x00' + struct.pack('>H', 4096) + (b'\x00' * 82) + b'\x0d' + (b'\x00' * 100)
    f.write(sqlite_data)
    
    # 3. Inject Executable Risk (MZ)
    f.seek(5 * 1024 * 1024)
    mz_data = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00' + (b'\x00' * 100)
    f.write(mz_data)
    
    # 4. Inject Fragmented JPEG (Part 1 at 6MB, Part 2 at 6MB + 20KB with FF D9)
    f.seek(6 * 1024 * 1024)
    jpeg_part1 = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00\x43\x00' + (b'\x55' * 2000)
    f.write(jpeg_part1)
    
    f.seek(6 * 1024 * 1024 + 20000) # Gap of ~18KB
    jpeg_part2 = (b'\x55' * 200) + b'\xFF\xD9'
    f.write(jpeg_part2)
    
    # 5. Inject Slack Space PDF exactly at 20MB
    f.seek(20 * 1024 * 1024)
    pdf_data = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<< /Size 1 /Root 1 0 R >>\nstartxref\n50\n%%EOF'
    f.write(pdf_data[:2048])
    
print("Test gaps injected successfully!")
