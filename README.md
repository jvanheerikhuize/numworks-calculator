# NumWorks Probe Toolkit

A Python toolkit and CLI for probing, inspecting, and interacting with NumWorks graphing calculators (N0100, N0110, N0115, and N0120) over USB.

---

## Features

- **Device Discovery & Identification**: Automatic detection of connected NumWorks calculators, hardware model detection (including the latest USB-C N0120), serial number, and operating mode (Epsilon OS vs. DFU Recovery).
- **Firmware & Memory Probing**: Inspects the flash memory layout, Epsilon OS version, git commit hash, and storage buffer offsets.
- **Python Script Management**:
  - List all Python scripts stored in the calculator's internal storage.
  - View syntax-highlighted scripts directly in the terminal.
  - Dump/extract all Python scripts to local `.py` files.
- **Raw Memory & Flash Dump**: Read and dump arbitrary memory segments via DFU upload.
- **Clean Python API**: High-level classes (`NumWorksDevice`, `CalculatorProbe`, `DfuDevice`, `Storage`) for custom scripting and reverse engineering.

---

## Getting Started

### 1. Set Up USB Permissions (Linux udev Rule)

On Linux, non-root users require a udev rule to send USB control transfers to the calculator. Run the included setup script:

```bash
./setup-udev.sh
```

*(Alternatively, copy `50-numworks-calculator.rules` to `/etc/udev/rules.d/` and reload with `sudo udevadm control --reload-rules && sudo udevadm trigger`).*

Unplug and re-plug your calculator after setting up the rule.

### 2. Activate Environment

The Python virtual environment is already prepared in `.venv/`:

```bash
source .venv/bin/activate
```

---

## CLI Usage

### Quick Device Info
Identify the connected calculator without needing root access:
```bash
numworks info
```

### Full Hardware & Firmware Probe
Perform a deep probe of hardware revision, Epsilon version, memory layout, and stored scripts:
```bash
numworks probe
```

### Python Scripts Management

**List scripts stored on the calculator:**
```bash
numworks scripts list
```

**View a script in the terminal:**
```bash
numworks scripts view mandelbrot.py
```

**Dump all scripts to a local directory:**
```bash
numworks scripts dump ./my_scripts/
```

### Raw Memory Dump
Dump a memory region (e.g. 4096 bytes from storage address):
```bash
numworks dump-memory 0x90000000 4096 flash_dump.bin
```

---

## Python API Example

You can also use the library programmatically in your own scripts:

```python
from numworks import NumWorksDevice, CalculatorProbe

# 1. Discover device
calc = NumWorksDevice.find_first()
if not calc:
    print("No calculator found!")
    exit(1)

# 2. Basic USB metadata
info = calc.get_info()
print(f"Connected: {info.model_name} (Serial: {info.serial_number})")

# 3. Full probe
probe = CalculatorProbe(calc)
result = probe.probe()

print(f"Epsilon Version: {result.firmware_info.kernel_version}")
print(f"Stored Scripts: {len(result.scripts)}")

for script in result.scripts:
    print(f" - {script.name} ({script.size} bytes, auto-import={script.auto_import})")
```

---

## Supported Hardware

| Model | Port | Processor | USB Mode |
|---|---|---|---|
| **N0100** | Micro-USB | STM32F412 | Supported |
| **N0110** | Micro-USB | STM32F730 | Supported |
| **N0115** | Micro-USB | STM32F730 | Supported |
| **N0120** | USB-C | STM32H7 / STM32F7 | Supported |
