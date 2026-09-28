import struct
import zlib
import os

image_path = "C:\\Users\\Ravi\\OneDrive\\Desktop\\mock_image.001"
with open(image_path, "r+b") as f:
    # Move MZ far away to 10MB to avoid 2MB chunk collateral damage on SQLite
    f.seek(5 * 1024 * 1024)
    f.write(b'\x00' * 100) # Erase old MZ
    f.seek(10 * 1024 * 1024)
    f.write(b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00' + (b'\x00' * 100))
