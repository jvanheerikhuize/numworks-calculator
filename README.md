# NumWorks Calculator Toolkit & Game Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/hardware-NumWorks%20N0100%20%7C%20N0110%20%7C%20N0120-red.svg)](https://www.numworks.com/)
[![Epsilon](https://img.shields.io/badge/OS-Epsilon%20v22%E2%80%93v26+-green.svg)](https://github.com/numworks/epsilon)

A complete open-source development toolkit, CLI, and game engine for the **NumWorks graphing calculator** (N0100, N0110, N0115, and N0120) running Epsilon OS. Build and deploy games in **MicroPython** or compile native **C/C++ ARM binaries** (`.nwa`) running at 60 FPS with hardware V-Sync!

---

> 🎮 **New here? Want to code your first calculator game?**  
> Check out the beginner-friendly step-by-step tutorial: **[CREATING_APPS.md](CREATING_APPS.md)**!  
> *(Written so anyone—including high-school students—can build their own game in minutes!)*

---

## Features

- **Dual Engine Architecture**:
  - 🐍 **MicroPython**: Instant deploy to the calculator's Python app with automatic memory profiling and heap checks.
  - ⚡ **Native C/C++ (EADK)**: Compile native ARM Cortex-M7 binaries (`.nwa`) up to 6 MB with 60 FPS hardware V-Sync and custom home-screen icons.
- **Automated Deployment Pipeline (`numworks deploy`)**: Pre-flight checks (AST allocation analysis, size limits, syntax validation) before flashing.
- **Sideload Command (`numworks deploy-nwa`)**: 1-click CLI upload of native `.nwa` apps directly to the calculator over USB via DFU.
- **MicroPython Game Library**: Battle-tested 3D raycasters and games optimized for Epsilon's 32 KB heap (`maties`, `floom`, `snake`).
- **Static Memory Profiler (`tools/test_allocs.py`)**: AST analyzer that enforces zero-allocation game loop constraints so your scripts never crash from heap fragmentation.
- **Hardware & Firmware Probe**: Deep USB inspection of flash memory layout, Epsilon version, storage buffer addresses, and USB state.

---

## Directory Structure

```
├── numworks/               # Core Python SDK & CLI
│   ├── cli.py              # CLI entry point (info, probe, deploy, deploy-nwa, ls)
│   ├── deploy.py           # Pre-flight checks and deploy pipeline
│   ├── device.py           # USB device discovery & metadata
│   ├── dfu.py              # USB DFU protocol & alternate settings
│   ├── probe.py            # Memory layout & firmware inspection
│   └── storage.py          # Epsilon storage buffer parser & builder
├── c_apps/                 # Native C/C++ Applications (.nwa)
│   ├── maties/             # High-performance 3D raycaster shooter (60 FPS, 80 rays)
│   └── sample_app/         # Official starter template for new C apps
├── games/                  # Python Games (.py)
│   ├── maties.py           # 3D raycasting wave survival shooter (zero-allocation)
│   ├── floom.py            # 3D raycaster maze crawler
│   └── snake.py            # Classic 2D grid arcade
├── tools/                  # Developer Tooling
│   ├── test_allocs.py      # Static AST allocation checker
│   └── minify.py           # Token-safe script minifier
├── tests/                  # Automated Test Suite
│   ├── test_storage.py     # Storage buffer parsing/packing unit tests
│   └── test_games.py       # Pre-deploy checks for all games
├── docs/                   # Deep Technical Documentation
│   ├── c-apps-sdk.md       # Complete guide to native C/C++ EADK development
│   ├── memory-model.md     # 32KB heap architecture, bytearray vs list, GC
│   ├── micropython-gotchas.md # Language quirks, syntax limits, traps
│   └── dfu-protocol.md     # DFU state machine, storage buffer structure
├── CREATING_APPS.md        # Beginner guide: How to make games in Python & C
├── HARDWARE.md             # N0120 hardware specifications & benchmarks
├── LICENSE                 # MIT License
└── pyproject.toml          # Package configuration
```

---

## Quickstart

### 1. Set Up USB Permissions (Linux)

```bash
./setup-udev.sh
```

*(Or copy `50-numworks-calculator.rules` to `/etc/udev/rules.d/` and run `sudo udevadm control --reload-rules && sudo udevadm trigger`).*

### 2. Activate Environment & Install

```bash
source .venv/bin/activate
pip install -e .
```

---

## CLI Usage

### Deploying a Python Game

Deploy a script directly to the calculator with pre-flight safety checks (syntax check, size limits, and zero-allocation verification):

```bash
# Deploy with pre-flight safety checks
numworks deploy games/maties.py

# Clean other non-system scripts and install fresh
numworks deploy games/maties.py --clean

# Quick list of scripts stored on device
numworks ls
```

### Sideloading a Native C Application (.nwa)

For 60 FPS native performance, true V-Sync, and up to 6 MB storage:

```bash
# 1. Build the native C app
make -C c_apps/maties

# 2. Sideload to the calculator via USB
numworks deploy-nwa c_apps/maties/output/app.nwa
```

*(Your calculator will automatically reboot and display your game's icon on the home screen!)*

### Probing Hardware & Firmware

```bash
numworks info       # Quick USB metadata
numworks probe      # Full memory layout, firmware version, and storage buffer
```

---

## Developer Tooling

### Static Allocation Analysis

Epsilon's 32 KB heap cannot tolerate dynamic allocations (lists, tuples, generators) inside a fast game loop. Verify your script before flashing:

```bash
python3 tools/test_allocs.py games/maties.py
```

### Token-Safe Minifier

Reduce file size to conserve AST compilation heap memory without breaking Python indentation:

```bash
python3 tools/minify.py input.py output.py
```

### Running Test Suite

```bash
python3 -m unittest discover -s tests
```

---

## Documentation

- **[CREATING_APPS.md](CREATING_APPS.md)** — Beginner's guide: How to make games in Python and C.
- **[docs/c-apps-sdk.md](docs/c-apps-sdk.md)** — Native C/C++ EADK development and `.nwa` packaging.
- **[HARDWARE.md](HARDWARE.md)** — STM32H725 @ 550MHz specs, display, and hardware benchmarks.
- **[docs/memory-model.md](docs/memory-model.md)** — 32 KB MicroPython heap limits, AST budget, and `bytearray` guidelines.
- **[docs/micropython-gotchas.md](docs/micropython-gotchas.md)** — Missing modules, syntax traps, `KEY_BACK` kill switch.
- **[docs/dfu-protocol.md](docs/dfu-protocol.md)** — USB DFU protocol, RAM address `0x2400657c`, and storage format.
- **[games/README.md](games/README.md)** — Game catalog and design standards.

---

## License

This project is licensed under the [MIT License](LICENSE) — free to use, modify, and distribute for personal, educational, and commercial projects.
