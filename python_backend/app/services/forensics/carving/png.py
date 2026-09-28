import zlib
import struct

class PNGCarver:
    def search(self, data: bytes, base_offset: int):
        candidates = []
        idx = 0
        sig = b'\x89PNG\r\n\x1A\n'
        while True:
            idx = data.find(sig, idx)
            if idx == -1: break
            
            structure_valid = True
            crc_valid = True
            ptr = idx + 8
            
            while ptr < len(data):
                if ptr + 8 > len(data):
                    structure_valid = False; break
                
                length = struct.unpack('>I', data[ptr:ptr+4])[0]
                chunk_type = data[ptr+4:ptr+8]
                
                if ptr + 8 + length + 4 > len(data):
                    structure_valid = False; break
                
                chunk_data = data[ptr+4:ptr+8+length]
                expected_crc = struct.unpack('>I', data[ptr+8+length:ptr+12+length])[0]
                actual_crc = zlib.crc32(chunk_data) & 0xffffffff
                
                if actual_crc != expected_crc:
                    crc_valid = False
                    
                ptr += 12 + length
                if chunk_type == b'IEND':
                    break
            
            from .carver_engine import CarvedCandidate
            candidates.append(CarvedCandidate(base_offset + idx, "PNG", data[idx:ptr], signature_valid=True, structure_valid=structure_valid, crc_valid=crc_valid))
            idx += 8
        return candidates
