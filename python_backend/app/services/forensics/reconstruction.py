import math
from collections import Counter
import os

class ReconstructionEngine:
    def __init__(self, cluster_size: int = 4096):
        self.cluster_size = cluster_size

    def calculate_entropy(self, data: bytes) -> float:
        if not data: return 0.0
        counts = Counter(data)
        entropy = 0.0
        for count in counts.values():
            p = count / len(data)
            entropy -= p * math.log2(p)
        return entropy

    def attempt_reconstruction(self, candidates, all_unallocated_blocks, image_path):
        for cand in candidates:
            if cand.structure_valid and cand.completeness: continue
                
            if cand.file_type == "JPEG" and cand.signature_valid and not cand.structure_valid:
                target_entropy = self.calculate_entropy(cand.raw_bytes[-self.cluster_size:])
                
                with open(image_path, 'rb') as f:
                    f.seek(cand.offset + len(cand.raw_bytes))
                    
                    # Beam search up to 10MB ahead
                    for _ in range(2500): 
                        chunk = f.read(self.cluster_size)
                        if not chunk: break
                        
                        chunk_entropy = self.calculate_entropy(chunk)
                        
                        # Match entropy or common filler
                        if abs(chunk_entropy - target_entropy) < 1.0 or chunk_entropy < 0.5:
                            if b'\xFF\xD9' in chunk:
                                idx = chunk.find(b'\xFF\xD9')
                                cand.fragment_recovered = True
                                cand.completeness = True
                                cand.structure_valid = True
                                cand.decoder_valid = True
                                cand.raw_bytes += chunk[:idx+2]
                                break
            
            cand.reconstruction_attempted = True
