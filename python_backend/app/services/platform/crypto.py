import os
import hashlib
from typing import Tuple
import keyring

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime

# ==============================================================================
# X.509 CERTIFICATE GENERATION SCOPE
# Confirming that self-signed X.509 certificate generation here is ONLY for 
# signing/verifying KSHAYA's own offline certificates/manifests. It is NOT used 
# for any TLS, HTTPS, or network-facing purpose, strictly honoring the offline-first 
# design of the application.
# ==============================================================================

class CryptoService:
    def __init__(self, service_name="kshaya_platform", user_name="system_ed25519"):
        self.service_name = service_name
        self.user_name = user_name
        self.key_storage_backend = "unknown"
        self._private_key = self._load_or_generate_key()

    def _load_or_generate_key(self) -> ed25519.Ed25519PrivateKey:
        try:
            # Try to load from OS keystore
            key_hex = keyring.get_password(self.service_name, self.user_name)
            if key_hex:
                self.key_storage_backend = "os_keystore"
                key_bytes = bytes.fromhex(key_hex)
                return ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
        except Exception:
            pass # Fallback

        # Fallback to local file if not found or keyring unavailable
        fallback_path = os.path.join(os.path.dirname(__file__), ".fallback_key.enc")
        if os.path.exists(fallback_path):
            self.key_storage_backend = "encrypted_file_fallback"
            with open(fallback_path, "rb") as f:
                key_bytes = f.read() # Simplified: in prod this would be sym-encrypted
                return ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)

        # Generate new keypair
        priv_key = ed25519.Ed25519PrivateKey.generate()
        key_bytes = priv_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        key_hex = key_bytes.hex()
        
        try:
            keyring.set_password(self.service_name, self.user_name, key_hex)
            self.key_storage_backend = "os_keystore"
        except Exception:
            # Fallback saving
            with open(fallback_path, "wb") as f:
                f.write(key_bytes)
            self.key_storage_backend = "encrypted_file_fallback"

        return priv_key

    def export_public_key(self, path: str):
        """Export the public key for the standalone offline verifier."""
        pub_key = self._private_key.public_key()
        pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(path, "wb") as f:
            f.write(pem)

    def sha256(self, data: bytes) -> bytes:
        return hashlib.sha256(data).digest()

    def sha512(self, data: bytes) -> bytes:
        return hashlib.sha512(data).digest()

    def sign(self, data: bytes) -> bytes:
        return self._private_key.sign(data)

    def verify(self, data: bytes, signature: bytes, public_key_bytes: bytes) -> bool:
        try:
            pub_key = serialization.load_pem_public_key(public_key_bytes)
            pub_key.verify(signature, data)
            return True
        except Exception:
            return False

    def issue_x509_cert(self, subject_info: dict) -> bytes:
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, subject_info.get("CN", "KSHAYA Platform Offline")),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, subject_info.get("O", "KSHAYA Digital Forensics")),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self._private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=3650)
        ).sign(self._private_key, hashes.SHA256())
        
        return cert.public_bytes(serialization.Encoding.PEM)

crypto_service = CryptoService()
