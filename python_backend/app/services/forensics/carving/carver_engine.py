import os
from typing import List, Any
from ..filesystem_parser import FilesystemParser
from .jpeg import JPEGCarver
from .png import PNGCarver
from .pdf import PDFCarver
from .zip_docx import ZipCarver
from .sqlite import SQLiteCarver
from .executable_risk import ExecutableRiskChecker
from ..reconstruction import ReconstructionEngine

class CarvedCandidate:
    def __init__(self, offset, file_type, raw_bytes, signature_valid=False, structure_valid=False, crc_valid=None):
        self.offset = offset
        self.file_type = file_type
        self.raw_bytes = raw_bytes
        self.signature_valid = signature_valid
        self.structure_valid = structure_valid
        self.crc_valid = crc_valid
        self.reconstruction_attempted = False
        self.fragment_recovered = False
        self.completeness = structure_valid  # Usually true if structure is fully valid (e.g., found EOF)
        self.decoder_valid = structure_valid # basic simulation for MVP
        self.source_type = "unallocated"

class CarverEngine:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.parser = FilesystemParser(image_path)
        self.risk_checker = ExecutableRiskChecker()
        self.reconstruction = ReconstructionEngine(self.parser.block_size)
        
        self.carvers = [
            JPEGCarver(),
            PNGCarver(),
            PDFCarver(),
            ZipCarver(),
            SQLiteCarver()
        ]

    def _scan_regions(self, regions, source_name):
        candidates = []
        with open(self.image_path, 'rb') as f:
            for offset, length in regions:
                f.seek(offset)
                bytes_left = length
                curr_offset = offset
                while bytes_left > 0:
                    chunk_size = min(bytes_left, 1024 * 1024 * 2) # 2MB chunks
                    data = f.read(chunk_size)
                    if not data: break
                    
                    if self.risk_checker.is_risky(data):
                        print(f"    [!] ExecutableRiskChecker: Flagged malicious/executable payload at offset {curr_offset} in {source_name}. Excluding from preview.")
                        # Move to next block to avoid parsing malware
                        bytes_left -= chunk_size
                        curr_offset += chunk_size
                        continue

                    for carver in self.carvers:
                        found = carver.search(data, curr_offset)
                        for cand in found:
                            cand.source_type = source_name
                        candidates.extend(found)
                        
                    bytes_left -= chunk_size
                    curr_offset += chunk_size
        return candidates

    def carve_all(self) -> List[CarvedCandidate]:
        unallocated = self.parser.get_unallocated_blocks()
        slack = self.parser.get_slack_space()
        
        candidates = self._scan_regions(unallocated, "unallocated")
        candidates.extend(self._scan_regions(slack, "slack"))
        
        # Pass incomplete candidates to reconstruction engine
        self.reconstruction.attempt_reconstruction(candidates, unallocated, self.image_path)
        
        return candidates

    def export_candidate(self, cand, case_id: str, output_base: str = "/tmp/kshaya_exports"):
        import os
        case_dir = os.path.join(output_base, str(case_id))
        os.makedirs(case_dir, exist_ok=True)
        ext = cand.file_type.lower()
        if ext == "zip_docx": ext = "zip"
        safe_filename = f"carved_{cand.offset}.{ext}"
        out_path = os.path.join(case_dir, safe_filename)
        with open(out_path, "wb") as f:
            f.write(cand.raw_bytes)
        return out_path
