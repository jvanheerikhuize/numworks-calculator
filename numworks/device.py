"""Device discovery and USB connection management for NumWorks."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import usb.core
import usb.util

from .constants import (
    VENDOR_ID_STM,
    PRODUCT_ID_CALCULATOR,
    PRODUCT_ID_DFU,
    MODELS,
    ModelDef,
)
from .dfu import DfuDevice, DfuError


@dataclass
class DeviceInfo:
    vendor_id: int
    product_id: int
    manufacturer: str
    product_name: str
    serial_number: str
    revision: int
    model_name: str
    is_dfu_mode: bool
    bus: int
    address: int
    port: str


class NumWorksDevice:
    """Represents a connected NumWorks calculator."""

    def __init__(self, dev: usb.core.Device):
        self.dev = dev
        self._dfu: Optional[DfuDevice] = None

    @classmethod
    def find_all(cls) -> List["NumWorksDevice"]:
        """Find all connected NumWorks calculators."""
        devices = []
        for d in usb.core.find(find_all=True, idVendor=VENDOR_ID_STM):
            if d.idProduct in (PRODUCT_ID_CALCULATOR, PRODUCT_ID_DFU):
                devices.append(cls(d))
        return devices

    @classmethod
    def find_first(cls) -> Optional["NumWorksDevice"]:
        """Find the first connected NumWorks calculator."""
        devs = cls.find_all()
        return devs[0] if devs else None

    def get_info(self) -> DeviceInfo:
        """Extract USB descriptor metadata."""
        vid = self.dev.idVendor
        pid = self.dev.idProduct
        is_dfu = pid == PRODUCT_ID_DFU
        rev = self.dev.bcdDevice

        # Model determination
        model_def = MODELS.get(rev)
        if model_def:
            model_name = model_def.name
        elif is_dfu:
            model_name = "STM32 Bootloader (Recovery)"
        else:
            model_name = f"Unknown (Rev 0x{rev:04x})"

        # Serial & names
        mfg = "Unknown"
        prod = "Unknown"
        serial = "Unknown"
        try:
            mfg = usb.util.get_string(self.dev, self.dev.iManufacturer) or ""
        except Exception:
            pass

        try:
            prod = usb.util.get_string(self.dev, self.dev.iProduct) or ""
        except Exception:
            pass

        try:
            serial = usb.util.get_string(self.dev, self.dev.iSerialNumber) or ""
        except Exception:
            pass

        # Linux sysfs fallback if descriptors could not be read directly
        if not serial or not prod or not mfg or mfg == "Unknown":
            from pathlib import Path
            sysfs_base = Path("/sys/bus/usb/devices")
            if sysfs_base.exists():
                for p in sysfs_base.iterdir():
                    try:
                        v_file = p / "idVendor"
                        p_file = p / "idProduct"
                        if v_file.exists() and p_file.exists():
                            if v_file.read_text().strip().lower() == f"{vid:04x}" and p_file.read_text().strip().lower() == f"{pid:04x}":
                                if not serial or serial == "Unknown":
                                    s_file = p / "serial"
                                    if s_file.exists():
                                        serial = s_file.read_text().strip()
                                if not prod or prod == "Unknown":
                                    pr_file = p / "product"
                                    if pr_file.exists():
                                        prod = pr_file.read_text().strip()
                                if not mfg or mfg == "Unknown":
                                    m_file = p / "manufacturer"
                                    if m_file.exists():
                                        mfg = m_file.read_text().strip()
                                break
                    except Exception:
                        pass

        ports = ".".join(str(p) for p in self.dev.port_numbers) if self.dev.port_numbers else str(self.dev.bus)

        return DeviceInfo(
            vendor_id=vid,
            product_id=pid,
            manufacturer=mfg,
            product_name=prod,
            serial_number=serial,
            revision=rev,
            model_name=model_name,
            is_dfu_mode=is_dfu,
            bus=self.dev.bus,
            address=self.dev.address,
            port=ports,
        )

    def get_dfu(self, intf_num: int = 0, alt_setting: int = 0) -> DfuDevice:
        """Create and claim DFU interface."""
        if self._dfu is None:
            # Check transfer size from DFU functional descriptor if present
            transfer_size = 2048
            try:
                cfg = self.dev.get_active_configuration()
                intf = cfg[(intf_num, alt_setting)]
                # Look for DFU functional descriptor (type 0x21 / 33)
                for desc in intf.extra_descriptors:
                    if len(desc) >= 9 and desc[1] == 0x21:
                        transfer_size = desc[5] | (desc[6] << 8)
                        break
            except Exception:
                pass

            self._dfu = DfuDevice(
                dev=self.dev,
                interface_number=intf_num,
                alternate_setting=alt_setting,
                transfer_size=transfer_size,
            )
        return self._dfu

    def close(self) -> None:
        """Release DFU interface and close device."""
        if self._dfu is not None:
            self._dfu.release()
            self._dfu = None
        try:
            usb.util.dispose_resources(self.dev)
        except Exception:
            pass
