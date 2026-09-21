"""NumWorks Calculator Hardware & Firmware Probe Toolkit."""

try:
    from .device import NumWorksDevice, DeviceInfo
    from .probe import CalculatorProbe, ProbeResult, FirmwareInfo
    from .dfu import DfuDevice, DfuError
except ImportError:
    NumWorksDevice = None  # type: ignore
    DeviceInfo = None  # type: ignore
    CalculatorProbe = None  # type: ignore
    ProbeResult = None  # type: ignore
    FirmwareInfo = None  # type: ignore
    DfuDevice = None  # type: ignore
    DfuError = None  # type: ignore

from .storage import Storage, Script, Record
from .deploy import run_all_checks

__version__ = "0.1.0"
__all__ = [
    "NumWorksDevice",
    "DeviceInfo",
    "CalculatorProbe",
    "ProbeResult",
    "FirmwareInfo",
    "DfuDevice",
    "DfuError",
    "Storage",
    "Script",
    "Record",
    "run_all_checks",
]
