from pydantic import BaseModel
from typing import Optional, List

class DeviceCapability(BaseModel):
    device_type: str  # e.g., HDD, SATA SSD, NVMe SSD, USB flash, SD card
    ata_sanitize_supported: bool
    nvme_sanitize_supported: bool
    nvme_format_supported: bool
    hpa_dco_present: bool
    raid_lvm_member: bool
    encryption_indicators: bool
    mounted: bool
    boot_volume: bool
    firmware_sanitize_available: bool

class DeviceInfo(BaseModel):
    device_id: str
    bus: str
    type: str
    model: str
    serial: str
    firmware: str
    capacity_bytes: int
    sector_size: int
    smart_health_summary: str

class CommandResult(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    dry_run: bool

class CapabilityLimitation(Exception):
    """Raised when a command is not supported by the device or host OS."""
    pass

class SafetyViolation(Exception):
    """Raised when a command violates a safety constraint (e.g., wrong serial, mounted)."""
    pass
