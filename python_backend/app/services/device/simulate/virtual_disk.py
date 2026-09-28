from typing import List

from ..models import DeviceInfo, DeviceCapability, CommandResult
from ..interface import DeviceBackend

class VirtualDiskBackend(DeviceBackend):
    """A fully in-memory device backend for end-to-end simulation and UI demos."""

    def __init__(self):
        self._devices = {
            "vdisk1": DeviceInfo(
                device_id="vdisk1",
                bus="USB",
                type="USB flash",
                model="Simulated Flash Drive",
                serial="VIRTUAL-SERIAL-001",
                firmware="1.0.0",
                capacity_bytes=32000000000,
                sector_size=512,
                smart_health_summary="GOOD"
            ),
            "vdisk2": DeviceInfo(
                device_id="vdisk2",
                bus="NVMe",
                type="NVMe SSD",
                model="Simulated NVMe Drive",
                serial="VIRTUAL-SERIAL-002",
                firmware="1.2.3",
                capacity_bytes=500000000000,
                sector_size=4096,
                smart_health_summary="WARNING"
            )
        }

    def list_devices(self) -> List[DeviceInfo]:
        return list(self._devices.values())

    def get_device_info(self, device_id: str) -> DeviceInfo:
        if device_id not in self._devices:
            raise ValueError(f"Device {device_id} not found.")
        return self._devices[device_id]

    def detect_capability(self, device_id: str) -> DeviceCapability:
        # Return different capabilities for demo purposes
        if device_id == "vdisk1":
            return DeviceCapability(
                device_type="USB flash",
                ata_sanitize_supported=False,
                nvme_sanitize_supported=False,
                nvme_format_supported=False,
                hpa_dco_present=False,
                raid_lvm_member=False,
                encryption_indicators=False,
                mounted=False,
                boot_volume=False,
                firmware_sanitize_available=False
            )
        else:
            return DeviceCapability(
                device_type="NVMe SSD",
                ata_sanitize_supported=False,
                nvme_sanitize_supported=True,
                nvme_format_supported=True,
                hpa_dco_present=False,
                raid_lvm_member=False,
                encryption_indicators=False,
                mounted=False,
                boot_volume=False,
                firmware_sanitize_available=True
            )

    def run_command(self, device_id: str, command: str, dry_run: bool) -> CommandResult:
        return CommandResult(
            success=True,
            output=f"VIRTUAL COMMAND EXECUTED: {command} on {device_id} (dry_run={dry_run})",
            dry_run=dry_run
        )
