class CleanupTargets:
    TARGETS = {
        "temp_files": ["C:\\Windows\\Temp", "C:\\Users\\*\\AppData\\Local\\Temp"],
        "recycle_bin": ["C:\\$Recycle.Bin"],
        "browser_cache": ["C:\\Users\\*\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache"]
    }
    
    @staticmethod
    def get_target_paths(target_id: str) -> list:
        # Real implementation would use glob to resolve wildcards
        return CleanupTargets.TARGETS.get(target_id, [])

    @staticmethod
    def is_unsafe_target(path: str) -> bool:
        # Pagefiles and hibernation files
        path_lower = path.lower()
        if "pagefile.sys" in path_lower or "hiberfil.sys" in path_lower:
            return True
        return False
