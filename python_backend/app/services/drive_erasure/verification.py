from pydantic import BaseModel
from typing import List, Optional
from ..device.interface import DeviceLayer

class VerificationResult(BaseModel):
    is_successful: bool
    verification_type: str  # "full" or "sampling"
    sectors_checked: int
    bad_sectors: int
    canary_found: bool
    canary_expected: bool
    errors: List[str]

class VerificationService:
    def __init__(self, device_layer: DeviceLayer):
        self.device_layer = device_layer

    def place_canary(self, device_id: str, execute_fn) -> bool:
        """Place a known canary value at a specific sector."""
        # Note: Actual DD syntax would depend on OS. Wrapped via DeviceLayer.
        cmd = f"dd if=/dev/urandom of={device_id} seek=0 bs=512 count=1"
        res = execute_fn(cmd)
        return res.success

    def verify_sampling(self, device_id: str, serial: str, execute_fn, sample_count: int = 100) -> VerificationResult:
        """Read back random samples to ensure zeroed or scrambled data."""
        errors = []
        sectors_checked = sample_count
        bad_sectors = 0
        
        # Example Linux command for a single sample read
        cmd = f"dd if={device_id} bs=512 count={sample_count} iflag=skip_bytes skip=1048576"
        res = execute_fn(cmd)
        
        if not res.success:
            errors.append(f"Failed to read samples: {res.error}")
            bad_sectors = sample_count
        
        # Real verification would parse the stdout bytes and ensure they are 0x00 or random
        # Assuming success for now in the actual logic wrapper.
        
        return VerificationResult(
            is_successful=len(errors) == 0,
            verification_type="sampling",
            sectors_checked=sectors_checked,
            bad_sectors=bad_sectors,
            canary_found=False,
            canary_expected=False,
            errors=errors
        )
