# NumWorks USB DFU Protocol & Storage Buffer Reference

Technical details on the USB Device Firmware Upgrade (DFU) protocol, memory map, and Python script storage buffer format for the NumWorks N0120 calculator.

---

## 1. DFU USB Configuration

| Attribute | Value |
|---|---|
| **Vendor ID (VID)** | `0x0483` (STMicroelectronics) |
| **Product ID (PID)** | `0xdf11` (DFU Mode) or `0xa291` (NumWorks Normal) |
| **Interface** | Class 0xFE (Application Specific), Subclass 0x01 (DFU) |
| **Alt Setting 0** | Flash memory access |
| **Alt Setting 1** | RAM memory access (contains the live storage buffer on N0120) |

---

## 2. Storage Buffer Binary Structure

On Epsilon, Python scripts are stored in a contiguous buffer in RAM at address `0x2400657c` (43,008 bytes data + 8 bytes magic).

```
Offset          Length      Description
0x0000          4 bytes     Start Magic: 0xEE, 0x0B, 0xDD, 0xBA ("BADD0BEE")
0x0004          Variable    Record List (sequential records)
...             2 bytes     Record Terminator: 0x00, 0x00
...             Variable    Padding: 0x00 filled up to offset 0xA804 (43,012)
0xA804          4 bytes     End Magic: 0xEE, 0x0B, 0xDD, 0xBA ("BADD0BEE")
Total: 43,016 bytes (0xA808)
```

### Record Format:
Each record represents one file or script:
```
Offset          Length      Description
0x00            2 bytes     Record total size (uint16_t, little-endian)
0x02            Variable    File name (null-terminated UTF-8 string)
...             Variable    Payload bytes
```

### Script Payload Details:
For `.py` files:
- **Byte 0**: `0x01` if auto-imported in python shell, `0x00` otherwise.
- **Bytes 1..N-1**: Python source code encoded as UTF-8.
- **Byte N**: Null terminator byte (`0x00`).

### Mandatory System Records:
The storage buffer must preserve two hidden system records:
- `gp.sys`
- `pr.sys`

> [!WARNING]
> If `BADD0BEE` magic header or footer is missing, or if `gp.sys` / `pr.sys` are absent, Epsilon's validation check fails and the OS silently restores factory default scripts (`squares.py`, `parabola.py`, etc.).

---

## 3. DFU State Machine Quirks

### 3.1 The `dfuUPLOADIDLE` Hang
When performing a DFU `upload` to read calculator memory:
1. The device transitions into `dfuUPLOADIDLE`.
2. Any subsequent write request (`download`, `set_address`) fails immediately with `[Errno 19] No such device` or a pipe error.
3. **Fix**: Issue a `DFU_ABORT` request immediately after reading to return the device to `dfuIDLE`.

### 3.2 Alternate Setting Selection
Always call `set_alt_setting(1)` before accessing the RAM storage buffer address `0x2400657c`. Calling without the correct alternate setting causes access violations.

---

## 4. Deployment Python API

The `numworks` Python library provides a clean high-level interface:

```python
from numworks.device import NumWorksDevice
from numworks.probe import CalculatorProbe

# 1. Connect
dev = NumWorksDevice.find_first()
probe = CalculatorProbe(dev)

# 2. Deploy script (with automatic buffer rebuild and magic verification)
probe.install_script("my_game.py", source_code, auto_import=False)

# 3. Clean all non-system scripts
probe.clean_scripts(keep_system=True)
```
