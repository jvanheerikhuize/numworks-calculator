# 🎮 NumWorks Game Maker

**Turn your NumWorks calculator into a game console — and build the games yourself.**

Yes, the same calculator you bring to math class can run your own 3D shooters, mazes, and arcade games. This repo gives you everything you need to write a game on your computer and beam it onto your calculator in seconds. No permission slip, no soldering, no boring stuff — just code and play.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/hardware-NumWorks%20N0100%20%7C%20N0110%20%7C%20N0120-red.svg)](https://www.numworks.com/)

---

## 🚀 Get a game on your calculator in 3 steps

You'll need a NumWorks calculator, a USB cable, and a computer with [Python 3.9+](https://www.python.org/downloads/) installed. That's it.

### 1. Install the tool

```bash
git clone https://github.com/jvanheerikhuize/numworks.git
cd numworks
pip install -e .
```

**Plugging in your calculator for the first time?** Your computer needs permission to talk to it over USB:
- **Linux:** run `./setup-udev.sh`
- **Windows:** install the `WinUSB` driver with [Zadig](https://zadig.akeo.ie/) — [full steps here](#usb-driver-setup-windows)
- **macOS:** works out of the box

### 2. Plug in your calculator

Connect it with a USB cable and make sure the calculator's screen says **"Connected"**.

### 3. Send it a game!

```bash
numworks deploy games/snake.py
```

Now open the **Python** app on your calculator, select `snake`, and play. That's genuinely it — you just put a game on your calculator. 🎉

---

## 🕹️ Games included, ready to play

| Game | What it is |
|---|---|
| `games/snake.py` | The classic. Eat, grow, don't hit yourself. |
| `games/floom.py` | A 3D maze you walk through, raycaster-style — like a tiny Wolfenstein. |
| `games/maties.py` | A fast-paced 3D wave-shooter. Enemies keep coming — how long can you survive? |

Try them all:

```bash
numworks deploy games/floom.py
numworks deploy games/maties.py
```

---

## 🛠️ Want to make your OWN game?

This is where it gets good. You don't need to be an expert — if you can follow a recipe, you can make a calculator game.

**👉 Start here: [CREATING_APPS.md](CREATING_APPS.md)**

It walks you through:
- How the screen and pixels work
- Drawing shapes, text, and colors
- Reading button presses
- A complete starter game template you can copy and modify
- How to level up to native C apps that run at a buttery-smooth 60 FPS with their own home-screen icon

Once your game works, send it to your calculator the same way:

```bash
numworks deploy games/my_game.py
```

---

## 💡 Tips for your first game

1. **Copy before you create.** Open `games/snake.py`, change one number, redeploy, see what happens. That's how you learn fastest.
2. **Start tiny.** A square that moves when you press arrow keys is a complete game. Build up from there.
3. **Don't use the `back` button in your code** — it's reserved by the calculator to instantly quit. Use `KEY_BACKSPACE` (the Clear button) instead. Full explanation in [CREATING_APPS.md](CREATING_APPS.md).
4. **Show it off.** Coding a game that runs on the calculator you bring to class is genuinely one of the coolest things you can do with it.

---

<a id="reference"></a>
## 📚 Reference (for when you want to go deeper)

<details>
<summary><strong>Everything below is background info — you don't need it to make your first game. It's here for when you're curious or ready to go pro.</strong></summary>

### What's actually in this toolkit

- **Dual Engine Architecture**:
  - 🐍 **MicroPython**: Instant deploy to the calculator's Python app with automatic memory profiling and heap checks.
  - ⚡ **Native C/C++ (EADK)**: Compile native ARM Cortex-M7 binaries (`.nwa`) up to 6 MB with 60 FPS hardware V-Sync and custom home-screen icons.
- **Automated Deployment Pipeline (`numworks deploy`)**: Pre-flight checks (AST allocation analysis, size limits, syntax validation) before flashing.
- **Sideload Command (`numworks deploy-nwa`)**: 1-click CLI upload of native `.nwa` apps directly to the calculator over USB via DFU.
- **Static Memory Profiler (`tools/test_allocs.py`)**: AST analyzer that enforces zero-allocation game loop constraints so your scripts never crash from heap fragmentation.
- **Hardware & Firmware Probe**: Deep USB inspection of flash memory layout, Epsilon version, storage buffer addresses, and USB state.

### Directory structure

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

<a id="usb-driver-setup-windows"></a>
### USB driver setup (Windows)

Windows binds its own STMicroelectronics driver to the calculator by default, which `pyusb`'s `libusb` backend can't talk to. You need to replace it with a `WinUSB` driver using [Zadig](https://zadig.akeo.ie/):

1. Download and run Zadig (no install required).
2. Connect the calculator via USB and put it in the mode you need (normal Epsilon mode, or DFU/bootloader mode for flashing).
3. In Zadig, select `Options > List All Devices`, then pick the NumWorks device from the dropdown (it may show as "STM32 ..." or the device's USB ID `0483:A291` for normal mode / `0483:DF11` for DFU mode).
4. Choose `WinUSB` as the replacement driver and click `Replace Driver` (or `Install Driver`).
5. Repeat for the *other* USB ID if you use both normal and DFU mode (e.g. once for `0483:A291`, once for `0483:DF11`) — Zadig only binds one device at a time.

*(This driver swap only affects how Windows routes USB access for this specific device/mode; it doesn't uninstall the calculator's normal Epsilon-mode driver as seen by other software.)*

### Full CLI usage

**Deploying a Python game**, with pre-flight safety checks (syntax check, size limits, and zero-allocation verification):

```bash
numworks deploy games/maties.py            # Deploy with pre-flight safety checks
numworks deploy games/maties.py --clean    # Clean other non-system scripts and install fresh
numworks ls                                # Quick list of scripts stored on device
```

**Sideloading a native C application (`.nwa`)**, for 60 FPS native performance, true V-Sync, and up to 6 MB storage:

```bash
make -C c_apps/maties                              # 1. Build the native C app
numworks deploy-nwa c_apps/maties/output/app.nwa    # 2. Sideload to the calculator via USB
```

*(Your calculator will automatically reboot and display your game's icon on the home screen!)*

**Probing hardware & firmware:**

```bash
numworks info       # Quick USB metadata
numworks probe      # Full memory layout, firmware version, and storage buffer
```

### Developer tooling

**Static allocation analysis** — Epsilon's 32 KB heap cannot tolerate dynamic allocations (lists, tuples, generators) inside a fast game loop. Verify your script before flashing:

```bash
python3 tools/test_allocs.py games/maties.py
```

**Token-safe minifier** — reduce file size to conserve AST compilation heap memory without breaking Python indentation:

```bash
python3 tools/minify.py input.py output.py
```

**Running the test suite:**

```bash
python3 -m unittest discover -s tests
```

### Documentation

- **[CREATING_APPS.md](CREATING_APPS.md)** — Beginner's guide: How to make games in Python and C.
- **[docs/c-apps-sdk.md](docs/c-apps-sdk.md)** — Native C/C++ EADK development and `.nwa` packaging.
- **[HARDWARE.md](HARDWARE.md)** — STM32H725 @ 550MHz specs, display, and hardware benchmarks.
- **[docs/memory-model.md](docs/memory-model.md)** — 32 KB MicroPython heap limits, AST budget, and `bytearray` guidelines.
- **[docs/micropython-gotchas.md](docs/micropython-gotchas.md)** — Missing modules, syntax traps, `KEY_BACK` kill switch.
- **[docs/dfu-protocol.md](docs/dfu-protocol.md)** — USB DFU protocol, RAM address `0x2400657c`, and storage format.
- **[games/README.md](games/README.md)** — Game catalog and design standards.

### Supported hardware

NumWorks N0100, N0110, N0115, and N0120, running Epsilon OS v22–v26+.

</details>

---

## License

This project is licensed under the [MIT License](LICENSE) — free to use, modify, and distribute for personal, educational, and commercial projects.
