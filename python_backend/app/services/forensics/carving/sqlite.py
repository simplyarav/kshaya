import struct

class SQLiteCarver:
    def search(self, data: bytes, base_offset: int):
        candidates = []
        idx = 0
        sig = b'SQLite format 3\x00'
        while True:
            idx = data.find(sig, idx)
            if idx == -1: break
            
            structure_valid = False
            if idx + 100 <= len(data):
                page_size = struct.unpack('>H', data[idx+16:idx+18])[0]
                if page_size == 1: page_size = 65536
                
                # Check B-tree page 1 type (at offset 100)
                if idx + 100 < len(data):
                    ptype = data[idx+100]
                    if ptype in [2, 5, 10, 13]:
                        structure_valid = True
            
            from .carver_engine import CarvedCandidate
            candidates.append(CarvedCandidate(base_offset + idx, "SQLite", data[idx:idx+4096], signature_valid=True, structure_valid=structure_valid))
            idx += 16
        return candidates
