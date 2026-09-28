import json
import argparse
import sys
from cryptography.hazmat.primitives import serialization

def verify_manifest(manifest_path: str, pubkey_path: str) -> bool:
    try:
        with open(pubkey_path, "rb") as f:
            pub_key_bytes = f.read()
    except Exception as e:
        print(f"Error reading public key: {e}", file=sys.stderr)
        return False
        
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"Error reading manifest: {e}", file=sys.stderr)
        return False
        
    signature_hex = manifest.get("signature")
    if not signature_hex:
        print("Manifest missing signature.", file=sys.stderr)
        return False
        
    # We DO NOT read the trusted public key from the manifest.
    # We only check if the signer_key_id matches what the user expects (optional).
    claimed_key_id = manifest.get("signer_key_id")
    print(f"Manifest claims to be signed by key ID: {claimed_key_id}")

    # Re-derive data payload
    manifest_no_sig = {k: v for k, v in manifest.items() if k != "signature"}
    payload_bytes = json.dumps(manifest_no_sig, sort_keys=True).encode("utf-8")
    signature_bytes = bytes.fromhex(signature_hex)
    
    # Verify using the externally provided pubkey
    try:
        pub_key = serialization.load_pem_public_key(pub_key_bytes)
        pub_key.verify(signature_bytes, payload_bytes)
        print("Signature is VALID.")
        return True
    except Exception as e:
        print(f"Signature is INVALID: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="KSHAYA Offline Verifier")
    parser.add_argument("--manifest", required=True, help="Path to JSON manifest")
    parser.add_argument("--pubkey", required=True, help="Path to trusted public key PEM file")
    
    args = parser.parse_args()
    
    is_valid = verify_manifest(args.manifest, args.pubkey)
    
    if is_valid:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
