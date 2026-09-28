class JPEGCarver:
    def search(self, data: bytes, base_offset: int):
        candidates = []
        idx = 0
        while True:
            idx = data.find(b'\xFF\xD8', idx)
            if idx == -1: break
            
            # Found header. Walk JFIF.
            end_idx = data.find(b'\xFF\xD9', idx)
            structure_valid = False
            
            # Check for fragmentation gap (blocks of nulls)
            gap_idx = data.find(b'\x00' * 512, idx)
            
            if end_idx != -1 and (gap_idx == -1 or gap_idx > end_idx):
                structure_valid = True
            else:
                end_idx = -1 # Truncate before the gap
                
            raw = data[idx:end_idx+2] if end_idx != -1 else data[idx:idx+4096]
            from .carver_engine import CarvedCandidate
            candidates.append(CarvedCandidate(base_offset + idx, "JPEG", raw, signature_valid=True, structure_valid=structure_valid))
            idx += 2
        return candidates
