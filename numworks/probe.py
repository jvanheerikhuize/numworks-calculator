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
        """Scan memory and RAM for Epsilon kernel and userland headers."""
        fw = FirmwareInfo()
        if not self.dfu:
            return fw

        # 1. Try Slot Info in RAM (Used on Epsilon 16+ / N0120 / N0110)
        rev = self.device.dev.bcdDevice
        model_def = MODELS.get(rev)
        ram_start = model_def.ram_start if model_def else 0x24000000

        try:
            slot_info = self.dfu.upload(ram_start, 16)
            if slot_info.startswith(MAGIC_SLOT_INFO) and slot_info.endswith(MAGIC_SLOT_INFO):
                k_addr, u_addr = struct.unpack_from("<II", slot_info, 4)
                if k_addr:
                    raw_k = self.dfu.upload(k_addr, 24)
                    if raw_k.startswith(MAGIC_KERNEL_HEADER):
                        self._parse_kernel_header(raw_k, fw)
                if u_addr:
                    raw_u = self.dfu.upload(u_addr, 48)
                    if raw_u.startswith(MAGIC_USERLAND_HEADER):
                        self._parse_userland_header(raw_u, fw)
                return fw
        except Exception:
            pass

        if not memory_layout:
            return fw

        base_addr = memory_layout[0]["address"]

        # 2. Try Header0 (older Epsilon)
        try:
            raw_h0 = self.dfu.upload(base_addr + HEADER0_OFFSET, HEADER0_SIZE)
            if raw_h0.startswith(MAGIC_KERNEL_HEADER):
                self._parse_kernel_header(raw_h0, fw)
                return fw
        except Exception:
            pass

        # 3. Try Header1
        try:
            raw_h1 = self.dfu.upload(base_addr + HEADER1_OFFSET, HEADER1_SIZE)
            if raw_h1.startswith(MAGIC_KERNEL_HEADER):
                self._parse_kernel_header(raw_h1, fw)
                return fw
        except Exception:
            pass

        return fw

    def _parse_userland_header(self, raw: bytes, fw: FirmwareInfo) -> None:
        """Extract userland version, storage address, and limits from userland header."""
        # Userland Header:
        # [0:4] MAGIC (0xFEEDC0DE)
        # [4:12] Version string
        # [12:16] Storage address (uint32_t LE)
        # [16:20] Storage size (uint32_t LE)
        # [20:24] External apps flash start (uint32_t LE)
        # [24:28] External apps flash end (uint32_t LE)
        # [28:32] External apps RAM start (uint32_t LE)
        # [32:36] External apps RAM end (uint32_t LE)
        try:
            v_end = raw.find(b"\x00", 4)
            fw.userland_version = raw[4 : v_end if v_end != -1 else 12].decode("utf-8", errors="replace")
        except Exception:
            pass

        if len(raw) >= 16:
            fw.storage_address = struct.unpack_from("<I", raw, 12)[0]
        if len(raw) >= 20:
            fw.storage_size = struct.unpack_from("<I", raw, 16)[0]
        if len(raw) >= 24:
            fw.external_apps_flash_start = struct.unpack_from("<I", raw, 20)[0]
        if len(raw) >= 28:
            fw.external_apps_flash_end = struct.unpack_from("<I", raw, 24)[0]
        if len(raw) >= 32:
            fw.external_apps_ram_start = struct.unpack_from("<I", raw, 28)[0]
        if len(raw) >= 36:
            fw.external_apps_ram_end = struct.unpack_from("<I", raw, 32)[0]

    def _parse_kernel_header(self, raw: bytes, fw: FirmwareInfo) -> None:
        """Extract version and storage address from kernel header."""
        # Kernel Header:
        # [0:4] MAGIC (0xF00DC0DE)
        # [4:12] Version string
        # [12:20] Git patch hash
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
            s_addr = struct.unpack_from("<I", raw, 20)[0]
            if s_addr and not fw.storage_address:
                fw.storage_address = s_addr

        if len(raw) >= 28:
            s_size = struct.unpack_from("<I", raw, 24)[0]
            if s_size and fw.storage_size == DEFAULT_STORAGE_SIZE:
                fw.storage_size = s_size

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
