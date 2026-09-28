import struct
import zlib
import os

image_path = "C:\\Users\\Ravi\\OneDrive\\Desktop\\mock_image.001"
with open(image_path, "r+b") as f:
    f.seek(15 * 1024 * 1024)
    png_sig = b'\x89PNG\r\n\x1A\n'
    ihdr_data = b'\x00\x00\x00\x0A\x00\x00\x00\x0A\x08\x02\x00\x00\x00'
    ihdr_chunk = b'IHDR' + ihdr_data
    ihdr_crc = struct.pack('>I', zlib.crc32(ihdr_chunk) & 0xffffffff)
    
    idat_data = b'Some compressed data'
    idat_chunk = b'IDAT' + idat_data
    idat_crc = struct.pack('>I', zlib.crc32(idat_chunk) & 0xffffffff) # GOOD CRC
    
    iend_chunk = b'IEND'
    iend_crc = struct.pack('>I', zlib.crc32(iend_chunk) & 0xffffffff)
    
    png_data = (png_sig + 
                struct.pack('>I', len(ihdr_data)) + ihdr_chunk + ihdr_crc +
                struct.pack('>I', len(idat_data)) + idat_chunk + idat_crc +
                struct.pack('>I', 0) + iend_chunk + iend_crc)
    f.write(png_data)
