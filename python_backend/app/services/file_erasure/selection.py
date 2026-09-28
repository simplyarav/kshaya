import os
from typing import List, Dict, Any

class FileSelector:
    @staticmethod
    def get_preview(paths: List[str]) -> Dict[str, Any]:
        """
        Recursively maps out the provided paths, counting files and total sizes.
        Does not perform any destructive operations.
        """
        total_files = 0
        total_size = 0
        detailed_paths = []
        
        for p in paths:
            if not os.path.exists(p):
                continue
                
            if os.path.isfile(p):
                size = os.path.getsize(p)
                total_files += 1
                total_size += size
                detailed_paths.append({"path": p, "size": size, "type": "file"})
            elif os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for file in files:
                        fp = os.path.join(root, file)
                        # Avoid symlink loops by not following them or tracking them specially
                        if not os.path.islink(fp):
                            try:
                                size = os.path.getsize(fp)
                                total_files += 1
                                total_size += size
                                detailed_paths.append({"path": fp, "size": size, "type": "file"})
                            except OSError:
                                pass
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "items": detailed_paths
        }
