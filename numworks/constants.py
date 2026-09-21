"""Constants, magic numbers, and hardware definitions for NumWorks calculators."""

from dataclasses import dataclass
from enum import IntEnum

# USB Vendor and Product IDs
VENDOR_ID_STM = 0x0483

PRODUCT_ID_CALCULATOR = 0xA291  # Standard / Epsilon OS mode
PRODUCT_ID_DFU = 0xDF11         # STM32 ROM Bootloader / Recovery mode

# DFU Requests (USB Class-Specific Requests)
class DfuRequest(IntEnum):
    DETACH = 0
    DNLOAD = 1
    UPLOAD = 2
    GETSTATUS = 3
    CLRSTATUS = 4
    GETSTATE = 5
    ABORT = 6

# DFU Device States
class DfuState(IntEnum):
    appIDLE = 0
    appDETACH = 1
    dfuIDLE = 2
    dfuDNLOAD_SYNC = 3
    dfuDNBUSY = 4
    dfuDNLOAD_IDLE = 5
    dfuMANIFEST_SYNC = 6
    dfuMANIFEST = 7
    dfuMANIFEST_WAIT_RESET = 8
    dfuUPLOAD_IDLE = 9
    dfuERROR = 10

# DFU Status Codes
class DfuStatus(IntEnum):
    OK = 0x00
    errTARGET = 0x01
    errFILE = 0x02
    errWRITE = 0x03
    errERASE = 0x04
    errCHECK_ERASED = 0x05
    errPROG = 0x06
    errVERIFY = 0x07
    errADDRESS = 0x08
    errNOTDONE = 0x09
    errFIRMWARE = 0x0A
    errVENDOR = 0x0B
    errUSBR = 0x0C
    errPOR = 0x0D
    errUNKNOWN = 0x0E
    errSTALLEDPKT = 0x0F

# STMicroelectronics DFU Extension Commands
class StDfuCommand(IntEnum):
    SET_ADDRESS_POINTER = 0x21
    ERASE_PAGE = 0x41
    READ_UNPROTECT = 0x92

# Epsilon Magic Signatures (Stored as big-endian hex words in memory)
MAGIC_KERNEL_HEADER = bytes.fromhex("F00DC0DE")    # b"\xf0\r\xc0\xde"
MAGIC_USERLAND_HEADER = bytes.fromhex("FEEDC0DE")  # b"\xfe\xed\xc0\xde"
MAGIC_SLOT_INFO = bytes.fromhex("BADBEEEF")        # b"\xba\xdb\xee\xef"
MAGIC_STORAGE_RECORD = bytes.fromhex("BADD0BEE")   # b"\xba\xdd\x0b\xee"

# Header Offsets (within flash base)
HEADER0_OFFSET = 428   # 0x1AC
HEADER0_SIZE = 24
HEADER1_OFFSET = 452   # 0x1C4
HEADER1_SIZE = 32

SLOT_INFO_SIZE = 16
DEFAULT_STORAGE_SIZE = 4096

@dataclass(frozen=True)
class ModelDef:
    name: str
    electronic_signature_address: int
    ram_start: int
    ram_end: int

MODELS = {
    0x0100: ModelDef(
        name="N0100",
        electronic_signature_address=0x20000000 - 0x10000,
        ram_start=0x20000000,
        ram_end=0x20040000,
    ),
    0x0110: ModelDef(
        name="N0110",
        electronic_signature_address=0x1FFF7A10,
        ram_start=0x20000000,
        ram_end=0x20040000,
    ),
    0x0115: ModelDef(
        name="N0115",
        electronic_signature_address=0x1FFF7A10,
        ram_start=0x20000000,
        ram_end=0x20040000,
    ),
    0x0120: ModelDef(
        name="N0120",
        electronic_signature_address=0x1FF1E800,
        ram_start=0x24000000,
        ram_end=0x24050000,
    ),
}
