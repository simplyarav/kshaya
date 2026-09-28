import struct

class ZipCarver:
    def search(self, data: bytes, base_offset: int):
        candidates = []
        idx = 0
        while True:
            idx = data.find(b'PK\x03\x04', idx)
            if idx == -1: break
            
            structure_valid = False
            # Look for End of Central Directory
            eocd_idx = data.find(b'PK\x05\x06', idx)
            if eocd_idx != -1:
                structure_valid = True
                
            raw = data[idx:eocd_idx+22] if eocd_idx != -1 else data[idx:idx+4096]
            from .carver_engine import CarvedCandidate
            candidates.append(CarvedCandidate(base_offset + idx, "ZIP_DOCX", raw, signature_valid=True, structure_valid=structure_valid))
            idx += 4
        return candidates
