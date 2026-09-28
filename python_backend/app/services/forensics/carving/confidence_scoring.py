class ScoreResult:
    def __init__(self, filename, offset, score, explanation):
        self.filename = filename
        self.offset = offset
        self.confidence_score = score
        self.explanation_string = explanation

class ConfidenceScorer:
    def __init__(self):
        # 6-Dimension Score
        self.weights = {
            "signature": 20,
            "structure": 20,
            "completeness": 15,
            "fragment": 15,
            "decoder": 15,
            "crc": 15
        }

    def score_candidate(self, cand) -> ScoreResult:
        score = 0
        explanations = []
        
        # 1. Signature
        if getattr(cand, "signature_valid", False):
            score += self.weights["signature"]
            explanations.append(f"Sig(+{self.weights['signature']})")
        else: explanations.append("Sig(+0)")
            
        # 2. Structure
        if getattr(cand, "structure_valid", False):
            score += self.weights["structure"]
            explanations.append(f"Struct(+{self.weights['structure']})")
        else: explanations.append("Struct(+0)")
        
        # 3. Completeness (Found EOF/Trailer)
        if getattr(cand, "completeness", False):
            score += self.weights["completeness"]
            explanations.append(f"Complete(+{self.weights['completeness']})")
        else: explanations.append("Truncated(+0)")
        
        # 4. Fragment (Contiguous is best, reconstructed is partial penalty)
        if getattr(cand, "fragment_recovered", False):
            score += 10 # Partial score for reconstructed
            explanations.append("Reconstructed(+10)")
        else:
            score += self.weights["fragment"]
            explanations.append(f"Contiguous(+{self.weights['fragment']})")
            
        # 5. Decoder (Does a basic header/stream decode pass?)
        if getattr(cand, "decoder_valid", False):
            score += self.weights["decoder"]
            explanations.append(f"Decoded(+{self.weights['decoder']})")
        else: explanations.append("DecodeFail(+0)")
            
        # 6. CRC
        if getattr(cand, "crc_valid", None) is not None:
            if cand.crc_valid:
                score += self.weights["crc"]
                explanations.append(f"CRC(+{self.weights['crc']})")
            else:
                explanations.append("BadCRC(+0)")
        else:
            # Scale if CRC not applicable (Max is 85 without CRC, scale to 100)
            score = int((score / 85) * 100)
            explanations.append("NoCRC")
            
        explanation_str = ", ".join(explanations)
        
        ext = getattr(cand, "file_type", "unknown").lower()
        if ext == "zip_docx": ext = "zip"
        source = getattr(cand, "source_type", "unallocated")
        filename = f"carved_{cand.offset}_{source}.{ext}"
        
        return ScoreResult(filename, cand.offset, score, explanation_str)
