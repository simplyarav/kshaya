import json
import datetime
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from .crypto import crypto_service

class CertificateService:
    SCOPE_TEMPLATES = {        "logical_readback": "Verification Scope: Logical host read-back only. SSD spare/over-provisioned areas not independently verifiable.",
        "sampling_verification": "Verification Scope: Independent sampling verification performed. Hex-level read-back confirmed logical zeroes strictly at offsets: {offsets}. Full-drive bit-by-bit readback was not performed.",
        "cryptographic_erase": "Verification Scope: Cryptographic key destruction only. Underlying media was not physically wiped.",
        "forensic_image": "Verification Scope: Forensically sound bit-for-bit logical image acquisition.",
        "logical_file_overwrite": "Verification Scope: logical file overwrite performed; SSD wear-leveling, filesystem journaling (e.g. NTFS journal), and copy-on-write snapshots (e.g. Btrfs/ZFS/APFS) may retain remnants of the original data outside this operation's control.",
        "forensic_report": "Verification Scope: Forensic analysis report. All findings mathematically linked to cryptographic baseline hash.",
        "forensic_report_redacted": "Verification Scope: Redacted forensic analysis report. PII and full file paths have been stripped for authorized dissemination."
    }

    def __init__(self, key_id: str = "default-key"):
        self.key_id = key_id

    def generate_manifest(self, job_details: dict, operator_identity: str, template_key: str, exceptions: list = None) -> dict:
        if template_key not in self.SCOPE_TEMPLATES:
            raise ValueError("Template key must be a pre-approved phrasing template.")
            
        manifest = {
            "version": "1.0",
            "job_details": job_details,
            "operator": operator_identity,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "verification_scope": self.SCOPE_TEMPLATES[template_key],
            "exceptions": exceptions or [],
            "signer_key_id": self.key_id
        }
        
        manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
        signature = crypto_service.sign(manifest_bytes).hex()
        
        manifest["signature"] = signature
        return manifest

    def generate_pdf(self, manifest: dict) -> bytes:
        pdf_buffer = BytesIO()
        # Set deterministic id to avoid reportlab generating unique UUIDs per run
        c = canvas.Canvas(pdf_buffer, pagesize=letter, enforceColorSpace='RGB')
        c.setCreator("KSHAYA Platform")
        c.setProducer("KSHAYA")
        c._doc.info.creationDate = "D:20230101000000Z"
        c._doc.info.modDate = "D:20230101000000Z"
        
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "KSHAYA Platform - Process Certificate")
        
        # Details
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 90, f"Operator: {manifest['operator']}")
        c.drawString(50, height - 110, f"Timestamp: {manifest['timestamp']}")
        
        # Verification Scope (Strictly Enforced)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, height - 140, "Verification Scope & Limitations:")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 155, manifest["verification_scope"])
        
        # Job Details
        y = height - 185
        c.drawString(50, y, "Job Details:")
        y -= 15
        # Ensure consistent order for deterministic output
        for k in sorted(manifest["job_details"].keys()):
            v = manifest["job_details"][k]
            c.drawString(60, y, f"{k}: {v}")
            y -= 15
            
        # Exceptions
        if manifest["exceptions"]:
            y -= 15
            c.drawString(50, y, "Exceptions:")
            y -= 15
            for exc in sorted(manifest["exceptions"]):
                c.drawString(60, y, f"- {exc}")
                y -= 15

        # Generate QR Code encoding manifest hash
        qr = qrcode.QRCode(box_size=4, border=2)
        
        # Re-derive hash of manifest (without signature) for QR
        manifest_no_sig = {k:v for k,v in manifest.items() if k != "signature"}
        manifest_bytes = json.dumps(manifest_no_sig, sort_keys=True).encode("utf-8")
        manifest_hash = crypto_service.sha256(manifest_bytes).hex()
        
        qr_data = f"kshaya://verify/{manifest['signer_key_id']}/{manifest_hash}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR to memory and draw on canvas
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        qr_image = ImageReader(img_buffer)
        
        c.drawImage(qr_image, 50, y - 100, width=80, height=80)
        
        c.setFont("Helvetica", 8)
        c.drawString(50, y - 115, f"Hash: {manifest_hash}")
        c.drawString(50, y - 130, f"Signature: {manifest['signature'][:32]}...")
        c.save()
        pdf_data = pdf_buffer.getvalue()
        
        # ReportLab embeds a non-deterministic /ID in the trailer. Strip it for provable determinism.
        import re
        pdf_data = re.sub(b'/ID \\s*\\[\\<[0-9a-fA-F]+\\>\\<[0-9a-fA-F]+\\>\\]', b'/ID \\n[<00000000000000000000000000000000><00000000000000000000000000000000>]', pdf_data)
        
        return pdf_data

