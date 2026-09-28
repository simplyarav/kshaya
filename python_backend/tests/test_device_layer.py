import pytest
from unittest.mock import patch, MagicMock

from app.services.device.models import (
    DeviceInfo, 
    DeviceCapability, 
    CapabilityLimitation, 
    SafetyViolation
)
from app.services.device.interface import DeviceLayer
from app.services.device.linux_backend import LinuxDeviceBackend
from app.services.device.windows_backend import WindowsDeviceBackend

@pytest.fixture
def mock_linux_backend():
    backend = LinuxDeviceBackend()
    backend.get_device_info = MagicMock(return_value=DeviceInfo(
        device_id="test1",
        bus="SATA",
        type="HDD",
        model="Test HDD",
        serial="TEST-SERIAL-123",
        firmware="1.0",
        capacity_bytes=500,
        sector_size=512,
        smart_health_summary="PASSED"
    ))
    backend.detect_capability = MagicMock(return_value=DeviceCapability(
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
    ))
    return backend

@pytest.fixture
def mock_windows_backend():
    backend = WindowsDeviceBackend()
    backend.get_device_info = MagicMock(return_value=DeviceInfo(
        device_id="test2",
        bus="NVMe",
        type="NVMe SSD",
        model="Test NVMe",
        serial="TEST-SERIAL-WIN",
        firmware="2.0",
        capacity_bytes=1000,
        sector_size=4096,
        smart_health_summary="OK"
    ))
    # Note: firmware_sanitize_available = False for Windows usually
    backend.detect_capability = MagicMock(return_value=DeviceCapability(
        device_type="NVMe SSD",
        ata_sanitize_supported=False,
        nvme_sanitize_supported=False,
        nvme_format_supported=False,
        hpa_dco_present=False,
        raid_lvm_member=False,
        encryption_indicators=False,
        mounted=False,
        boot_volume=False,
        firmware_sanitize_available=False
    ))
    return backend

def test_dry_run_never_calls_subprocess(mock_linux_backend):
    layer = DeviceLayer(backend=mock_linux_backend)
    
    with patch('subprocess.run') as mock_run:
        result = layer.run_command("test1", "smartctl -a /dev/test1", dry_run=True)
        assert result.success is True
        assert result.dry_run is True
        mock_run.assert_not_called()

def test_missing_confirmed_serial_raises_safety_violation(mock_linux_backend):
    layer = DeviceLayer(backend=mock_linux_backend)
    
    with pytest.raises(SafetyViolation, match="confirmed_serial must be provided"):
        layer.run_command("test1", "hdparm --security-erase", dry_run=False)

def test_wrong_confirmed_serial_raises_safety_violation(mock_linux_backend):
    layer = DeviceLayer(backend=mock_linux_backend)
    
    with pytest.raises(SafetyViolation, match="Serial number mismatch"):
        layer.run_command("test1", "hdparm --security-erase", dry_run=False, confirmed_serial="WRONG-SERIAL")

def test_mounted_device_raises_safety_violation(mock_linux_backend):
    # Override capability to simulate mounted device
    cap = mock_linux_backend.detect_capability()
    cap.mounted = True
    mock_linux_backend.detect_capability.return_value = cap
    
    layer = DeviceLayer(backend=mock_linux_backend)
    
    with pytest.raises(SafetyViolation, match="Cannot run commands on a mounted device"):
        layer.run_command("test1", "lsblk", dry_run=True)

def test_legal_hold_raises_safety_violation(mock_linux_backend):
    layer = DeviceLayer(backend=mock_linux_backend)
    
    with pytest.raises(SafetyViolation, match="Cannot run commands on a device under legal hold"):
        layer.run_command("test1", "lsblk", dry_run=True, protection_flags={"legal_hold": True})

def test_windows_purge_blocked_by_capability(mock_windows_backend):
    layer = DeviceLayer(backend=mock_windows_backend)
    
    with pytest.raises(CapabilityLimitation, match="Firmware sanitize operations are not available"):
        layer.run_command("test2", "nvme sanitize /dev/test2", dry_run=True)

def test_windows_non_purge_allowed(mock_windows_backend):
    layer = DeviceLayer(backend=mock_windows_backend)
    
    with patch('subprocess.run') as mock_run:
        result = layer.run_command("test2", "Get-PhysicalDisk", dry_run=True)
        assert result.success is True
        mock_run.assert_not_called()
