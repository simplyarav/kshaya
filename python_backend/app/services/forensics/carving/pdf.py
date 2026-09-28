class PDFCarver:
    def search(self, data: bytes, base_offset: int):
        candidates = []
        idx = 0
        while True:
            idx = data.find(b'%PDF-', idx)
            if idx == -1: break
            
            structure_valid = False
            # Look for %%EOF within reasonable bound
            end_idx = data.find(b'%%EOF', idx)
            if end_idx != -1:
                # Look for xref
                xref_idx = data.find(b'xref', idx, end_idx)
                if xref_idx != -1:
                    structure_valid = True
            
            raw = data[idx:end_idx+5] if end_idx != -1 else data[idx:idx+4096]
            from .carver_engine import CarvedCandidate
            candidates.append(CarvedCandidate(base_offset + idx, "PDF", raw, signature_valid=True, structure_valid=structure_valid))
            idx += 5
        return candidates
