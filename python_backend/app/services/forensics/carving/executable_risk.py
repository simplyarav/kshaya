class ExecutableRiskChecker:
    def is_risky(self, data: bytes) -> bool:
        # Check MZ (PE), ELF, DEX anywhere in the chunk (simulating deep scan)
        if b'MZ\x90\x00' in data: return True
        if b'\x7fELF' in data: return True
        if b'dex\n' in data: return True
        return False
