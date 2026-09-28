import struct
import zlib
import os

image_path = "C:\\Users\\Ravi\\OneDrive\\Desktop\\mock_image.001"

if not os.path.exists(image_path):
    # Create a 50MB blank file if it doesn't exist
    with open(image_path, "wb") as f:
        f.write(b'\x00' * (50 * 1024 * 1024))

with open(image_path, "r+b") as f:
    # 1. Inject a valid JPEG at 1MB offset
    f.seek(1024 * 1024)
    jpeg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00\x43\x00' + (b'\x11' * 64) + b'\xFF\xD9'
    f.write(jpeg_data)
    
    # 2. Inject a corrupted PNG at 2MB offset
    f.seek(2 * 1024 * 1024)
    # Valid PNG header + IHDR chunk
    png_sig = b'\x89PNG\r\n\x1A\n'
    ihdr_data = b'\x00\x00\x00\x0A\x00\x00\x00\x0A\x08\x02\x00\x00\x00'
    ihdr_chunk = b'IHDR' + ihdr_data
    ihdr_crc = struct.pack('>I', zlib.crc32(ihdr_chunk) & 0xffffffff)
    
    # Corrupt IDAT chunk (bad CRC)
    idat_data = b'Some compressed data'
    idat_chunk = b'IDAT' + idat_data
    bad_idat_crc = struct.pack('>I', 0xDEADBEEF) # Deliberately wrong
    
    iend_chunk = b'IEND'
    iend_crc = struct.pack('>I', zlib.crc32(iend_chunk) & 0xffffffff)
    
    png_data = (png_sig + 
                struct.pack('>I', len(ihdr_data)) + ihdr_chunk + ihdr_crc +
                struct.pack('>I', len(idat_data)) + idat_chunk + bad_idat_crc +
                struct.pack('>I', 0) + iend_chunk + iend_crc)
    f.write(png_data)

print("Injected valid JPEG and corrupted PNG into unallocated blocks of mock_image.001")
