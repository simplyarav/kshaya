import platform
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from .models import (
    DeviceInfo,
    DeviceCapability,
    CommandResult,
    CapabilityLimitation,
    SafetyViolation
)

class DeviceBackend(ABC):
    @abstractmethod
    def list_devices(self) -> List[DeviceInfo]:
        pass

    @abstractmethod
    def get_device_info(self, device_id: str) -> DeviceInfo:
        pass

    @abstractmethod
    def detect_capability(self, device_id: str) -> DeviceCapability:
        pass

    @abstractmethod
    def run_command(self, device_id: str, command: str, dry_run: bool) -> CommandResult:
        pass


class DeviceLayer:
    def __init__(self, backend: Optional[DeviceBackend] = None):
        if backend is None:
            # Auto-detect backend based on OS
            os_name = platform.system().lower()
            if os_name == "windows":
                from .windows_backend import WindowsDeviceBackend
                self.backend = WindowsDeviceBackend()
            elif os_name == "linux":
                from .linux_backend import LinuxDeviceBackend
                self.backend = LinuxDeviceBackend()
            else:
                from .simulate.virtual_disk import VirtualDiskBackend
                self.backend = VirtualDiskBackend()
        else:
            self.backend = backend

    def list_devices(self) -> List[DeviceInfo]:
        return self.backend.list_devices()

    def get_device_info(self, device_id: str) -> DeviceInfo:
        return self.backend.get_device_info(device_id)

    def detect_capability(self, device_id: str) -> DeviceCapability:
        return self.backend.detect_capability(device_id)

    def run_command(self, device_id: str, command: str, dry_run: bool = True, 
                    confirmed_serial: Optional[str] = None, 
                    protection_flags: Optional[Dict[str, Any]] = None) -> CommandResult:
        
        info = self.get_device_info(device_id)
        cap = self.detect_capability(device_id)

        # 1. Safety Guard: Mounted or Boot volume
        # if cap.mounted:
        #     raise SafetyViolation(f"Cannot run commands on a mounted device: {device_id}")
        if cap.boot_volume:
            raise SafetyViolation(f"Cannot run commands on the boot volume: {device_id}")
            
        # 2. Safety Guard: Legal hold / Protection flags
        if protection_flags and protection_flags.get("legal_hold"):
            raise SafetyViolation(f"Cannot run commands on a device under legal hold: {device_id}")

        # 3. Safety Guard: Serial number verification for real runs
        if not dry_run:
            if confirmed_serial is None:
                raise SafetyViolation("confirmed_serial must be provided for a non-dry run.")
            if confirmed_serial.strip() != info.serial.strip():
                raise SafetyViolation(
                    f"Serial number mismatch! Provided '{confirmed_serial}' != Actual '{info.serial}'"
                )

        # 4. Capability Limitation Guard: Block "Purge" / "Sanitize" if not supported
        cmd_lower = command.lower()
        if "purge" in cmd_lower or "sanitize" in cmd_lower:
            if not cap.firmware_sanitize_available:
                raise CapabilityLimitation(
                    "Firmware sanitize operations are not available on this device/OS combination. "
                    "Use logical-level operations instead."
                )

        return self.backend.run_command(device_id, command, dry_run)
