import os
import shutil
import hashlib
import time

class EraseEngine:
    @staticmethod
    def is_cloud_sync_path(path: str) -> bool:
        path_lower = path.lower()
        if "onedrive" in path_lower or "dropbox" in path_lower:
            return True
        return False
        
    @staticmethod
    def hash_file(filepath: str) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError:
            return "hash-failed"

    @staticmethod
    def overwrite_and_delete(filepath: str) -> dict:
        """
        Securely overwrites the file using native Python IO.
        Explicitly calls flush() and os.fsync() to bypass OS buffer cache.
        """
        try:
            size = os.path.getsize(filepath)
            
            # 1 pass random overwrite
            with open(filepath, 'r+b') as f:
                f.seek(0)
                bytes_written = 0
                while bytes_written < size:
                    chunk_size = min(4096, size - bytes_written)
                    f.write(os.urandom(chunk_size))
                    bytes_written += chunk_size
                    
                # Explicit flush and fsync as requested
                f.flush()
                os.fsync(f.fileno())

            # Rename to random string before delete to obfuscate filename
            dir_name = os.path.dirname(filepath)
            rand_name = os.urandom(8).hex()
            new_path = os.path.join(dir_name, rand_name)
            os.rename(filepath, new_path)
            
            # Delete
            os.remove(new_path)
            
            return {"status": "success"}
        except PermissionError:
            return {"status": "locked", "error": "File is locked by another process."}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @staticmethod
    def quarantine_file(filepath: str, vault_dir: str = "C:\\KSHAYA_Vault") -> str:
        if not os.path.exists(vault_dir):
            os.makedirs(vault_dir)
            
        base = os.path.basename(filepath)
        dest = os.path.join(vault_dir, f"{base}.quarantine")
        shutil.move(filepath, dest)
        return dest
