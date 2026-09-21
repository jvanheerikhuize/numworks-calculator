"""DFU protocol implementation for NumWorks communication."""

import re
import struct
import time
from typing import Callable, Optional, List, Dict, Any, Tuple
import usb.core
import usb.util

from .constants import (
    DfuRequest,
    DfuState,
    DfuStatus,
    StDfuCommand,
)

DFU_REQUEST_OUT = (
    usb.util.CTRL_OUT | usb.util.CTRL_TYPE_CLASS | usb.util.CTRL_RECIPIENT_INTERFACE
)
DFU_REQUEST_IN = (
    usb.util.CTRL_IN | usb.util.CTRL_TYPE_CLASS | usb.util.CTRL_RECIPIENT_INTERFACE
)


class DfuError(Exception):
    """Exception raised for DFU protocol errors."""
    pass


class DfuDevice:
    """Manages DFU protocol communication over USB."""

    def __init__(
        self,
        dev: usb.core.Device,
        interface_number: int = 0,
        alternate_setting: int = 0,
        transfer_size: int = 2048,
    ):
        self.dev = dev
        self.interface_number = interface_number
        self.alternate_setting = alternate_setting
        self.transfer_size = transfer_size

    def claim(self) -> None:
        """Claim the DFU USB interface."""
        try:
            if self.dev.is_kernel_driver_active(self.interface_number):
                self.dev.detach_kernel_driver(self.interface_number)
        except Exception:
            pass

        try:
            self.dev.set_interface_altsetting(
                interface=self.interface_number,
                alternate_setting=self.alternate_setting,
            )
        except Exception:
            pass

        usb.util.claim_interface(self.dev, self.interface_number)

    def release(self) -> None:
        """Release the claimed DFU interface."""
        try:
            usb.util.release_interface(self.dev, self.interface_number)
        except Exception:
            pass

    def get_status(self) -> Tuple[DfuStatus, int, DfuState, int]:
        """Request the current status from the DFU device.
        Returns:
            (status, poll_timeout_ms, state, i_string)
        """
        raw = self.dev.ctrl_transfer(
            DFU_REQUEST_IN,
            DfuRequest.GETSTATUS,
            0,
            self.interface_number,
            6,
            timeout=5000,
        )
        if len(raw) < 6:
            raise DfuError(f"Truncated DFU status response: {len(raw)} bytes")

        status = DfuStatus(raw[0])
        poll_timeout = raw[1] | (raw[2] << 8) | (raw[3] << 16)
        state = DfuState(raw[4])
        i_string = raw[5]
        return status, poll_timeout, state, i_string

    def clear_status(self) -> None:
        """Clear DFU error status."""
        self.dev.ctrl_transfer(
            DFU_REQUEST_OUT,
            DfuRequest.CLRSTATUS,
            0,
            self.interface_number,
            None,
            timeout=5000,
        )

    def abort(self) -> None:
        """Abort current DFU operation and return to dfuIDLE."""
        self.dev.ctrl_transfer(
            DFU_REQUEST_OUT,
            DfuRequest.ABORT,
            0,
            self.interface_number,
            None,
            timeout=5000,
        )

    def ensure_idle(self) -> None:
        """Ensure device is in dfuIDLE state, clearing errors or aborting if needed."""
        try:
            status, _, state, _ = self.get_status()
            if state == DfuState.dfuERROR:
                self.clear_status()
                status, _, state, _ = self.get_status()
            if state != DfuState.dfuIDLE:
                self.abort()
                status, _, state, _ = self.get_status()
        except Exception as err:
            raise DfuError(f"Failed to reset device to dfuIDLE: {err}") from err

    def wait_state(
        self,
        target_state: DfuState,
        timeout_seconds: float = 5.0,
    ) -> Tuple[DfuStatus, int, DfuState, int]:
        """Poll until device reaches target state or timeout occurs."""
        start = time.time()
        while time.time() - start < timeout_seconds:
            status, poll_timeout, state, i_string = self.get_status()
            if status != DfuStatus.OK and state == DfuState.dfuERROR:
                raise DfuError(f"DFU error in wait_state: status={status.name}")
            if state == target_state:
                return status, poll_timeout, state, i_string
            delay = max(poll_timeout / 1000.0, 0.005)
            time.sleep(delay)
        raise DfuError(f"Timeout waiting for state {target_state.name}")

    def wait_not_busy(self, timeout_seconds: float = 5.0) -> Tuple[DfuStatus, int, DfuState, int]:
        """Poll until device is not in dfuDNBUSY state."""
        start = time.time()
        while time.time() - start < timeout_seconds:
            status, poll_timeout, state, i_string = self.get_status()
            if state != DfuState.dfuDNBUSY:
                return status, poll_timeout, state, i_string
            delay = max(poll_timeout / 1000.0, 0.005)
            time.sleep(delay)
        raise DfuError("Timeout waiting for dfuDNBUSY to clear")

    def set_address(self, address: int) -> None:
        """Issue ST DFU SET_ADDRESS_POINTER command."""
        self.ensure_idle()

        # Command: [0x21, addr_byte0, addr_byte1, addr_byte2, addr_byte3]
        payload = struct.pack("<BI", StDfuCommand.SET_ADDRESS_POINTER, address)
        self.dev.ctrl_transfer(
            DFU_REQUEST_OUT,
            DfuRequest.DNLOAD,
            0,
            self.interface_number,
            payload,
            timeout=5000,
        )

        status, _, state, _ = self.wait_not_busy()
        if state != DfuState.dfuDNLOAD_IDLE:
            raise DfuError(f"Expected dfuDNLOAD_IDLE after set_address, got {state.name}")

        # Return to dfuIDLE
        self.abort()

    def upload_block(self, block_number: int, length: int) -> bytes:
        """Upload (read) a single block from the device."""
        raw = self.dev.ctrl_transfer(
            DFU_REQUEST_IN,
            DfuRequest.UPLOAD,
            block_number,
            self.interface_number,
            length,
            timeout=5000,
        )
        return bytes(raw)

    def download_block(self, block_number: int, data: bytes) -> None:
        """Download (write) a single block to the device."""
        self.dev.ctrl_transfer(
            DFU_REQUEST_OUT,
            DfuRequest.DNLOAD,
            block_number,
            self.interface_number,
            data,
            timeout=5000,
        )
        self.wait_not_busy()

    def upload(
        self,
        address: int,
        length: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """Read `length` bytes of memory starting at `address`."""
        self.set_address(address)
        self.ensure_idle()

        result = bytearray()
        block_number = 2  # DFU upload block sequence starts at 2 after set_address

        while len(result) < length:
            chunk_size = min(self.transfer_size, length - len(result))
            chunk = self.upload_block(block_number, chunk_size)
            if not chunk:
                break
            result.extend(chunk)
            block_number += 1
            if progress_callback:
                progress_callback(len(result), length)

        self.abort()
        return bytes(result[:length])

    def download(
        self,
        address: int,
        data: bytes,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Write `data` to memory starting at `address`."""
        self.set_address(address)
        block_number = 2
        offset = 0

        while offset < len(data):
            chunk = data[offset : offset + self.transfer_size]
            self.download_block(block_number, chunk)
            offset += len(chunk)
            block_number += 1
            if progress_callback:
                progress_callback(offset, len(data))

        # Finalize download with empty block 0
        self.dev.ctrl_transfer(
            DFU_REQUEST_OUT,
            DfuRequest.DNLOAD,
            0,
            self.interface_number,
            b"",
            timeout=5000,
        )
        self.wait_not_busy()
        self.abort()

    @staticmethod
    def parse_memory_layout(descriptor_string: str) -> List[Dict[str, Any]]:
        """Parse standard ST DFU descriptor string into memory segment dictionaries.
        Example descriptor:
            @Internal Flash  /0x08000000/04*016Kg,01*064Kg,03*128Kg
        """
        segments = []
        parts = descriptor_string.split("/")
        if len(parts) < 3:
            return segments

        idx = 1
        page_pattern = re.compile(r"(\d+)\*(\d+)([K|M])g")

        while idx < len(parts):
            try:
                base_addr = int(parts[idx], 0)
                subparts = parts[idx + 1].split(",")
                current_addr = base_addr

                for item in subparts:
                    m = page_pattern.match(item.strip())
                    if not m:
                        continue
                    nb_pages = int(m.group(1))
                    page_size = int(m.group(2))
                    unit = m.group(3)

                    if unit == "K":
                        page_size *= 1024
                    elif unit == "M":
                        page_size *= 1048576

                    total_size = nb_pages * page_size
                    segments.append({
                        "address": current_addr,
                        "last_address": current_addr + total_size - 1,
                        "size": total_size,
                        "nb_pages": nb_pages,
                        "page_size": page_size,
                    })
                    current_addr += total_size
            except Exception:
                pass
            idx += 2

        return segments
