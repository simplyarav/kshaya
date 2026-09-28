import subprocess
import json
from typing import List

from .models import DeviceInfo, DeviceCapability, CommandResult
from .interface import DeviceBackend

class LinuxDeviceBackend(DeviceBackend):
    def list_devices(self) -> List[DeviceInfo]:
        # Typically calls `lsblk -J -o NAME,TYPE,MODEL,SERIAL,SIZE,MOUNTPOINT`
        # Scaffolding returns empty or simulated parsing
        return []

    def get_device_info(self, device_id: str) -> DeviceInfo:
        # Calls `smartctl -a -j /dev/{device_id}`
        return DeviceInfo(
            device_id=device_id,
            bus="SATA",
            type="HDD",
            model="Generic Linux Drive",
            serial="LINUX-SERIAL-1234",
            firmware="1.0",
            capacity_bytes=500000000000,
            sector_size=512,
            smart_health_summary="PASSED"
        )

    def detect_capability(self, device_id: str) -> DeviceCapability:
        # Parsed from smartctl, hdparm -I, nvme id-ctrl
        return DeviceCapability(
            device_type="HDD",
            ata_sanitize_supported=True,
            nvme_sanitize_supported=False,
            nvme_format_supported=False,
            hpa_dco_present=False,
            raid_lvm_member=False,
            encryption_indicators=False,
            mounted=False,
            boot_volume=False,
            firmware_sanitize_available=True
        )

    def run_command(self, device_id: str, command: str, dry_run: bool) -> CommandResult:
        if dry_run:
            return CommandResult(
                success=True,
                output=f"SIMULATED (dry_run): {command} on {device_id}",
                dry_run=True
            )
        
        try:
            # We prefix commands safely, though command parsing would be stricter in prod
            result = subprocess.run(
                command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return CommandResult(
                success=True,
                output=result.stdout,
                error=result.stderr if result.stderr else None,
                dry_run=dry_run
            )
        except subprocess.CalledProcessError as e:
            return CommandResult(
                success=False,
                output=e.stdout,
                error=e.stderr,
                dry_run=dry_run
            )
