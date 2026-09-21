# NumWorks N0120 Hardware & Software Reference

A comprehensive reference for developing games and applications on the NumWorks N0120 calculator running Epsilon OS.

---

## 1. Hardware Specifications

| Component | Specification |
|---|---|
| **MCU** | STMicroelectronics **STM32H725** (ARM Cortex-M7) |
| **Clock Speed** | Up to **550 MHz** |
| **Internal SRAM** | **256 KB** |
| **External Flash** | **8 MB** SPI NOR (firmware + OS slots) |
| **Display** | 2.8" IPS LCD, **320 × 240 pixels** (222 usable in Python; top 18px reserved for status bar) |
| **LCD Controller** | Built-in LTDC with Chrom-ART Accelerator (hardware DMA2D) |
| **Battery** | **1450 mAh** lithium-polymer, rechargeable via USB-C |
| **USB** | USB-C, DFU mode for firmware flashing |

---

## 2. Memory Architecture

### 2.1 Python Storage Buffer
- **Total Size**: Exactly **43,008 bytes** (43016 with headers/footers)
- **Magic Header**: `BADD0BEE` (4 bytes at start)
- **Magic Footer**: `BADD0BEE` (4 bytes at end, after padding)
- **Record Format**: Name (null-terminated string) + 2-byte size + content bytes
- **System Records**: `gp.sys` and `pr.sys` are hidden mandatory records. If missing, Epsilon factory-resets the Python environment.
- **Max Scripts**: ~8 scripts total
- **Script Content Prefix**: Each Python script record starts with `\x01` and ends with `\x00`

### 2.2 MicroPython Heap
- **Heap Size**: **32 KB** on stock Epsilon firmware
- **Shared With**: The AST compiler, all imported modules, and all runtime objects
- **No Unloading**: Once a module is imported, it cannot be freed — it stays in the heap for the lifetime of the script
- **Alternative**: Omega firmware increases the heap to ~100 KB

### 2.3 Memory Budget Breakdown (approximate)
| Usage | Bytes |
|---|---|
| AST compilation of script | 5–15 KB (depends on script complexity) |
| Module imports (`math`, `random`, `time`, `ion`, `kandinsky`) | ~3–5 KB |
| Global variables & constants | ~2–4 KB |
| **Remaining for game logic** | **~8–20 KB** |

> [!CAUTION]
> The AST compiler parses the entire script into memory before executing a single line. A 20KB script with many nested list literals can exhaust the heap *during compilation*, before any game code runs.

---

## 3. Display & Graphics

### 3.1 Screen Geometry
- **Physical Resolution**: 320 × 240 pixels
- **Python Usable Area**: 320 × 222 pixels (y: 0–221)
- **Color Depth**: 16-bit RGB565
- **Coordinate Origin**: Top-left corner (0, 0)

### 3.2 Kandinsky Module API
| Function | Description |
|---|---|
| `color(r, g, b)` | Create a color from RGB (0–255 each). Returns an integer. |
| `fill_rect(x, y, w, h, color)` | Fill a rectangle. The workhorse for all rendering. |
| `draw_string(text, x, y, fg, bg)` | Draw text. Font is ~10px wide, ~18px tall. |
| `set_pixel(x, y, color)` | Set a single pixel. **Extremely slow** — avoid in loops. |
| `get_pixel(x, y)` | Read a pixel's color as `(r, g, b)` tuple. Allocates a tuple! |

### 3.3 Rendering Constraints
- **No Double Buffering**: `fill_rect` writes directly to the LCD framebuffer. There is no offscreen buffer or V-sync.
- **Tearing/Flickering**: Drawing a background and then overdrawing sprites causes visible flicker. Use single-pass column rendering instead.
- **Performance**: `fill_rect` is fast for large rectangles (DMA-accelerated). `set_pixel` is ~100x slower per pixel than `fill_rect`.
- **Color Tuples**: Passing `(r, g, b)` tuples to drawing functions works but **allocates a tuple on the heap every call**. Pre-compute colors with `color()` at init time.

> [!TIP]
> For flicker-free 3D rendering, draw each vertical column top-to-bottom in a single pass: ceiling → wall → floor. Never clear the screen first.

---

## 4. Input (Ion Module)

### 4.1 Available Keys
| Physical Key | Ion Constant | Notes |
|---|---|---|
| Arrow keys | `KEY_LEFT`, `KEY_RIGHT`, `KEY_UP`, `KEY_DOWN` | Primary movement |
| OK button | `KEY_OK` | Center of D-pad, primary action |
| Back | `KEY_BACK` | ⚠️ **Intercepted by Epsilon** — terminates the Python script! |
| Clear | `KEY_BACKSPACE` | Safe alternative for in-game menu/restart |
| EXE | `KEY_EXE` | Safe, usable as secondary action |
| Shift | `KEY_SHIFT` | Available |
| Alpha | `KEY_ALPHA` | Available |
| Home | `KEY_HOME` | ⚠️ May be intercepted by OS |
| On/Off | `KEY_ONOFF` | ⚠️ System key |
| Number keys | `KEY_ZERO` through `KEY_NINE` | Available |
| XNT | `KEY_XNT` | Available |
| Var | `KEY_VAR` | Available |
| Toolbox | `KEY_TOOLBOX` | Available |

### 4.2 Input API
```python
ion.keydown(ion.KEY_OK)  # Returns True if key is currently held down
```
- **Polling only**: There are no key events, interrupts, or key-up callbacks
- **No debouncing**: You must implement your own edge detection (track `prev_ok` state)
- **Simultaneous keys**: Multiple keys can be detected simultaneously

> [!WARNING]
> `KEY_BACK` is a **hard kill switch**. Epsilon intercepts it at the OS level and forcefully terminates the running Python script. Never use it for in-game navigation. Use `KEY_BACKSPACE` (the Clear key) instead.

---

## 5. Available Python Modules

| Module | Status | Notes |
|---|---|---|
| `math` | ✅ Full | `cos`, `sin`, `tan`, `sqrt`, `atan2`, `pi`, `radians`, etc. |
| `cmath` | ✅ Full | Complex number math |
| `random` | ✅ Full | `randint`, `random`, `choice`, etc. |
| `time` | ✅ Partial | `monotonic()`, `sleep()`. No `ticks_ms()` guaranteed. |
| `kandinsky` | ✅ Full | Graphics (see §3.2) |
| `ion` | ✅ Full | Keyboard input (see §4) |
| `turtle` | ✅ Full | Turtle graphics (very slow for games) |
| `gc` | ✅ Partial | `gc.collect()`, `gc.mem_alloc()`, `gc.mem_free()` |
| `micropython` | ⚠️ Varies | `mem_info()` may be available |
| `os` | ❌ Missing | No filesystem access |
| `sys` | ❌ Missing | No system-level access |
| `array` | ❌ Missing | No typed arrays — use `bytearray` |
| `struct` | ❌ Missing | No binary struct packing |
| `socket`/`network` | ❌ Missing | No networking hardware |
| `json` | ❌ Missing | Must parse manually |
| `re` | ❌ Missing | No regex |

---

## 6. Python Language Restrictions (Epsilon MicroPython)

| Feature | Supported? | Notes |
|---|---|---|
| F-strings (`f"..."`) | ❌ | Use `str()` concatenation or `.format()` |
| Extended unpacking (`*args` mid-call) | ❌ | `func(*t, x)` fails. Use `func(t[0], t[1], x)` |
| Walrus operator (`:=`) | ❌ | Not supported |
| `match`/`case` | ❌ | Not supported |
| Classes | ✅ | Supported but each instance allocates heap |
| Generators | ✅ | Supported but allocate heap — avoid in hot loops |
| List comprehensions | ✅ | Allocate a list — avoid in hot loops |
| `bytearray` | ✅ | **Preferred** over lists for large buffers (5x less memory) |
| Integer arithmetic | ✅ | Arbitrary precision (but slow for big numbers) |
| Float arithmetic | ✅ | Hardware FPU on Cortex-M7 |

---

## 7. Performance Guidelines

### 7.1 Achievable Frame Rates
| Workload | Approximate FPS |
|---|---|
| Simple 2D tile game (minimal fill_rect) | 20–30 FPS |
| 3D raycaster (40 columns, enemies, HUD) | 8–15 FPS |
| Full-screen redraw per frame | 5–10 FPS |
| Per-pixel rendering (set_pixel loop) | < 1 FPS |

### 7.2 Optimization Strategies
1. **Minimize `fill_rect` calls**: Each call has fixed overhead. Batch draws where possible.
2. **Pre-compute constants**: Calculate trig tables, colors, and lookup tables once at init.
3. **Avoid object creation in loops**: No lists, tuples, dicts, generators, or string concatenation in the game loop.
4. **Use `bytearray` for large arrays**: 1 byte per element vs ~8 bytes per element for lists.
5. **Use global variables for function returns**: Instead of returning tuples, write to pre-allocated globals.
6. **Call `gc.collect()` once per frame**: At the top of the main loop to defragment the heap.
7. **Reduce ray count for speed**: 40 rays at 8px columns is a good balance. 20 rays at 16px is faster but blockier.

### 7.3 Static Memory Analysis
Always run `test_allocs.py` before deploying:
```bash
python3 test_allocs.py my_game.py
# [PASS] All allocations are safe (Global/Init only).
```
This AST-based tool flags any dynamic allocation (list, tuple, dict, generator) inside game functions. **All game loop functions must be zero-allocation.**

---

## 8. DFU / USB Flashing

### 8.1 Storage Address
- **RAM address**: `0x2400657c`
- **Alt Setting**: 1 (for RAM access)
- **Buffer size**: 43016 bytes (43008 data + 8 bytes magic)

### 8.2 Protocol Quirks
- After `upload()`, the device is left in `dfuUPLOADIDLE` state. Send `abort()` before any `download()`.
- After `download()`, the device reboots and disconnects. Must be re-plugged for further operations.
- The `DETACH` command gracefully exits USB mode.

### 8.3 Installation Workflow
```python
# 1. Read current storage
buf = dfu.upload(0x2400657c, 43016)
# 2. Parse records
storage = Storage(buf)
# 3. Modify records (remove old, add new)
storage.records = [r for r in storage.records if r.name != "old.py"]
storage.records.append(Record(name="new.py", content=b"\x01" + code + b"\x00", ...))
# 4. Rebuild and upload
new_buf = Storage.build_storage_buffer(storage.records, 43008)
dfu.download(0x2400657c, new_buf)
```
