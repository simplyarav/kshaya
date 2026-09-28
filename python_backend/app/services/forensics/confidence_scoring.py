class ConfidenceScorer:
    @staticmethod
    def calculate_overall(candidate, reconstruction_res: dict) -> dict:
        score = 0.0
        explanations = []
        
        # 1. Signature
        if candidate.signature_confidence > 0.8:
            score += 20
            explanations.append("Signature matched expected magic bytes.")
            
        # 2. Structure
        if candidate.structure_pass:
            score += 40
            explanations.append(candidate.structure_details)
        else:
            explanations.append(f"Structure Invalid: {candidate.structure_details}")
            
        # 3. Fragments / Recon
        recon_conf = reconstruction_res.get("reconstruction_confidence", 0.0)
        score += recon_conf * 40
        explanations.append(f"Reconstruction: {reconstruction_res.get('explanation')}")
        
        return {
            "score": score, # out of 100
            "grade": "High" if score > 80 else ("Medium" if score > 50 else "Low"),
            "explanations": explanations
        }
