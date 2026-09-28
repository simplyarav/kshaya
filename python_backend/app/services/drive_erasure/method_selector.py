from typing import List
from ..device.models import DeviceCapability

class MethodSelector:
    @staticmethod
    def recommend_methods(capability: DeviceCapability) -> List[str]:
        methods = []
        
        is_ssd = capability.device_type in ["SATA SSD", "NVMe SSD"]
        is_removable = capability.device_type in ["USB flash", "SD card"]
        
        if is_removable:
            # Enforce CRITICAL RULE
            methods.append("Clear (logical overwrite) — Purge not achieved on this device")
            return methods
            
        if is_ssd:
            if capability.firmware_sanitize_available:
                if capability.device_type == "NVMe SSD":
                    if capability.nvme_sanitize_supported:
                        methods.append("NVMe Block Erase (Purge)")
                    if capability.nvme_format_supported:
                        methods.append("NVMe Crypto Erase (Purge)")
                elif capability.device_type == "SATA SSD":
                    if capability.ata_sanitize_supported:
                        methods.append("ATA Block Erase (Purge)")
                        
                # Always offer crypto scramble if encryption indicators exist
                if capability.encryption_indicators:
                    methods.append("Crypto Scramble (Purge)")
            else:
                # Enforce CRITICAL RULE: No firmware sanitize available
                methods.append("Clear (logical overwrite) — Purge not achieved on this device")
                
        else:
            # HDD
            methods.append("Zero Overwrite (Clear)")
            methods.append("Random Overwrite (Clear)")
            methods.append("Pattern Overwrite (Clear)")
            
            # If HDD supports Sanitize, we could do Purge
            if capability.firmware_sanitize_available and capability.ata_sanitize_supported:
                methods.append("ATA Block Erase (Purge)")
                
        # Deduplicate and return
        return list(dict.fromkeys(methods))
