"""High-level probe operations for NumWorks calculator."""

from dataclasses import dataclass, field
import struct
from typing import Optional, List, Dict, Any, Callable

import usb.core
import usb.util

from .constants import (
    MAGIC_KERNEL_HEADER,
    MAGIC_USERLAND_HEADER,
    MAGIC_SLOT_INFO,
    MAGIC_STORAGE_RECORD,
    HEADER0_OFFSET,
    HEADER0_SIZE,
    HEADER1_OFFSET,
    HEADER1_SIZE,
    DEFAULT_STORAGE_SIZE,
    MODELS,
)
from .device import NumWorksDevice, DeviceInfo
from .dfu import DfuDevice, DfuError
from .storage import Storage, Script, StorageError


@dataclass
class FirmwareInfo:
    kernel_version: str = "Unknown"
    kernel_patch: str = "Unknown"
    userland_version: str = "Unknown"
    storage_address: Optional[int] = None
    storage_size: int = DEFAULT_STORAGE_SIZE
    external_apps_flash_start: Optional[int] = None
    external_apps_flash_end: Optional[int] = None
    external_apps_ram_start: Optional[int] = None
    external_apps_ram_end: Optional[int] = None


@dataclass
class ProbeResult:
    device_info: DeviceInfo
    memory_layout: List[Dict[str, Any]] = field(default_factory=list)
    firmware_info: FirmwareInfo = field(default_factory=FirmwareInfo)
    scripts: List[Script] = field(default_factory=list)
    storage_used_bytes: int = 0
    storage_total_bytes: int = 0
    raw_storage_accessible: bool = False
    error: Optional[str] = None


class CalculatorProbe:
    """Performs deep probing of a connected NumWorks calculator."""

    def __init__(self, device: NumWorksDevice):
        self.device = device
        self.dfu: Optional[DfuDevice] = None

    def probe(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ProbeResult:
        """Run full hardware, firmware, and script probe."""
        dev_info = self.device.get_info()
        result = ProbeResult(device_info=dev_info)

        if dev_info.is_dfu_mode:
            result.error = "Calculator is in STM32 ROM Recovery/DFU mode (OS not running)"
            return result

        if progress_callback:
            progress_callback("Connecting to DFU interface...")

        try:
            self.dfu = self.device.get_dfu()
            self.dfu.claim()
        except Exception as e:
            result.error = (
                f"Failed to access USB device: {e}\n"
                "Tip: Ensure the udev rule is installed or run with sufficient permissions."
            )
            return result

        try:
            # 1. Probe Memory Layout
            if progress_callback:
                progress_callback("Probing memory layout...")
            result.memory_layout = self._probe_memory_layout()

            # 2. Probe Firmware Headers
            if progress_callback:
                progress_callback("Reading firmware headers...")
            result.firmware_info = self._probe_firmware_headers(result.memory_layout)

            # 3. Probe Storage & Python Scripts
            if result.firmware_info.storage_address:
                if progress_callback:
                    progress_callback("Reading storage and scripts...")
                scripts, used, total, ok = self._probe_storage(result.firmware_info)
                result.scripts = scripts
                result.storage_used_bytes = used
                result.storage_total_bytes = total
                result.raw_storage_accessible = ok

        except Exception as e:
            result.error = f"Probing encountered an error: {e}"
        finally:
            try:
                self.dfu.release()
            except Exception:
                pass

        return result

    def _probe_memory_layout(self) -> List[Dict[str, Any]]:
        """Read and parse memory layout from DFU string descriptor."""
        try:
            cfg = self.device.dev.get_active_configuration()
            intf = cfg[(0, 0)]
            if intf.iInterface:
                desc_str = usb.util.get_string(self.device.dev, intf.iInterface)
                if desc_str:
                    return DfuDevice.parse_memory_layout(desc_str)
        except Exception:
            pass
        return []

    def _probe_firmware_headers(self, memory_layout: List[Dict[str, Any]]) -> FirmwareInfo:
        """Scan memory base for Epsilon kernel and userland headers."""
        fw = FirmwareInfo()
        if not self.dfu or not memory_layout:
            return fw

        base_addr = memory_layout[0]["address"]

        # Try Header0
        try:
            raw_h0 = self.dfu.upload(base_addr + HEADER0_OFFSET, HEADER0_SIZE)
            if raw_h0.startswith(MAGIC_KERNEL_HEADER):
                self._parse_kernel_header(raw_h0, fw)
                return fw
        except Exception:
            pass

        # Try Header1
        try:
            raw_h1 = self.dfu.upload(base_addr + HEADER1_OFFSET, HEADER1_SIZE)
            if raw_h1.startswith(MAGIC_KERNEL_HEADER):
                self._parse_kernel_header(raw_h1, fw)
                return fw
        except Exception:
            pass

        return fw

    def _parse_kernel_header(self, raw: bytes, fw: FirmwareInfo) -> None:
        """Extract version and storage address from kernel header."""
        # Kernel Header:
        # [0:4] MAGIC (0xF00DC0DE)
        # [4:12] Version string (null-terminated or fixed 8 bytes)
        # [12:20] Git patch hash (null-terminated or fixed 8 bytes)
        # [20:24] Storage address (uint32_t LE)
        # [24:28] Optional storage size (uint32_t LE)
        try:
            v_end = raw.find(b"\x00", 4)
            fw.kernel_version = raw[4 : v_end if v_end != -1 else 12].decode("utf-8", errors="replace")
        except Exception:
            pass

        try:
            p_end = raw.find(b"\x00", 12)
            fw.kernel_patch = raw[12 : p_end if p_end != -1 else 20].decode("utf-8", errors="replace")
        except Exception:
            pass

        if len(raw) >= 24:
            fw.storage_address = struct.unpack_from("<I", raw, 20)[0]

        if len(raw) >= 28:
            fw.storage_size = struct.unpack_from("<I", raw, 24)[0]

    def _probe_storage(self, fw: FirmwareInfo):
        """Read storage memory buffer and parse stored Python scripts."""
        if not self.dfu or not fw.storage_address:
            return [], 0, 0, False

        try:
            read_len = fw.storage_size + 2 * len(MAGIC_STORAGE_RECORD)
            buf = self.dfu.upload(fw.storage_address, read_len)
            storage = Storage(buf)
            scripts = storage.get_scripts()
            return scripts, storage.total_used_bytes(), fw.storage_size, True
        except Exception:
            return [], 0, fw.storage_size, False

    def dump_memory(
        self,
        address: int,
        length: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """Dump arbitrary memory range via DFU upload."""
        if not self.dfu:
            self.dfu = self.device.get_dfu()
            self.dfu.claim()
        return self.dfu.upload(address, length, progress_callback)
