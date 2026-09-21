# NumWorks Native C/C++ App Development (EADK & .nwa)

A complete guide to building, compiling, and sideloading native C/C++ applications (`.nwa` binaries) on the NumWorks N0120 calculator running Epsilon OS (v22+ through v26+).

---

## 1. Why Native C/C++ (Route 2)?

While Python scripts are convenient, complex games quickly hit hard limits on the N0120:

| Feature | Python Script (Route 1) | Native C/C++ App (Route 2) |
|---|---|---|
| **Max Storage Size** | 43 KB total (shared across scripts) | **Up to 2.5 MB – 6 MB** per app |
| **Execution Speed** | Interpreted bytecode (~10–15 FPS for 3D) | **Native 550 MHz ARM Cortex-M7 + FPU (60 FPS)** |
| **RAM / Heap** | 32 KB shared heap (fragile, easily exhausted) | **Dedicated heap + stack with newlib `malloc`/`free`** |
| **Display Rendering** | `fill_rect` only; no double buffer | **Direct full-frame buffer push (`eadk_display_push_rect`)** |
| **Tearing & V-Sync** | No V-Blank synchronization (screen tearing) | **Hardware V-Blank (`eadk_display_wait_for_vblank`)** |
| **Key Handling** | `KEY_BACK` forcefully kills the script | **Full keyboard control (`eadk_keyboard_scan`)** |

---

## 2. Toolchain Setup (Already Configured)

Your development environment is already fully configured in this repository:

1. **ARM Cross-Compiler**:
   - `arm-none-eabi-gcc` 14.2 is installed in `~/.local/bin/` with Newlib multilib support for Cortex-M7 hard-FPU (`thumb/v7e-m+fp/hard`).
2. **Linker & Packager**:
   - `nwlink` (v0.0.19) via `npx` generates the relocatable `.nwa` container and converts icons into ELF objects.
3. **Build System**:
   - GNU `make`.

---

## 3. Project Structure

A sample C application is located in `c_apps/sample_app/`:

```
c_apps/sample_app/
├── Makefile            # Pre-configured with sysroot and nwlink flags
├── README.md           # Application documentation
├── src/
│   ├── main.c          # C application source
│   └── icon.png        # 56x56 pixel app icon shown on the home screen
└── output/             # Generated binaries
    └── app.nwa         # The distributable NumWorks Application
```

### Anatomy of an EADK Application (`main.c`):

```c
#include <eadk.h>

// 1. Mandatory metadata sections
const char eadk_app_name[] __attribute__((section(".rodata.eadk_app_name"))) = "MyGame";
const uint32_t eadk_api_level  __attribute__((section(".rodata.eadk_api_level"))) = 0;

int main(int argc, char * argv[]) {
  // Clear screen to black
  eadk_display_push_rect_uniform(eadk_screen_rect, eadk_color_black);

  // Main game loop
  while (true) {
    // 2. Scan keyboard
    eadk_keyboard_state_t kbd = eadk_keyboard_scan();
    if (eadk_keyboard_key_down(kbd, eadk_key_back)) {
      return 0; // Exit cleanly to home screen
    }

    // 3. Hardware V-Blank sync (smooth 60 FPS)
    eadk_display_wait_for_vblank();

    // 4. Render graphics
    // ...
  }
}
```

---

## 4. Building the Application

Compile the C code into an `.nwa` binary:

```bash
make -C c_apps/sample_app
```

Output:
```
CC      src/main.c
ICON    src/icon.png
LD      output/app.nwa
```

---

## 5. Sideloading to the Calculator

### Method A: Via CLI (`numworks deploy-nwa`)
Connect the calculator with USB, navigate to the USB "Connected" screen, then run:

```bash
numworks deploy-nwa c_apps/sample_app/output/app.nwa
```

Or directly via `make`:
```bash
make -C c_apps/sample_app run
```

### Method B: Via WebUSB (Browser)
If you prefer a web-based loader without local terminal commands:
1. Open Chromium or Chrome.
2. Go to **[Nwagyu](https://nwagyu.app)** or the official **[NumWorks External Apps Portal](https://my.numworks.com/apps)**.
3. Plug in your calculator and select the generated `c_apps/sample_app/output/app.nwa` file to upload.

---

## 6. EADK API Summary

| Function | Description |
|---|---|
| `eadk_display_push_rect(rect, pixels)` | Push an array of 16-bit RGB565 pixels directly to screen |
| `eadk_display_push_rect_uniform(rect, color)` | Hardware-fill a rectangle with a solid color |
| `eadk_display_pull_rect(rect, pixels)` | Read back pixels from LCD controller |
| `eadk_display_wait_for_vblank()` | Pause execution until the next vertical blank period |
| `eadk_display_draw_string(str, pt, ...)` | Draw text using built-in calculator font |
| `eadk_keyboard_scan()` | Capture instantaneous 64-bit keyboard state |
| `eadk_keyboard_key_down(state, key)` | Check if a specific `eadk_key_*` is pressed |
| `eadk_timing_millis()` | High-precision millisecond monotonic timestamp |
| `eadk_timing_usleep(us)` | Microsecond sleep |
| `eadk_random()` | Hardware random 32-bit integer |
