# NumWorks Calculator Games

A collection of optimized games for the NumWorks N0120 graphing calculator running Epsilon OS.

---

## Games Collection

> Looking for **Maties**, the 3D wave-survival shooter? It now lives as a native C app at [`c_apps/maties/`](../c_apps/maties/) — full 60 FPS with hardware V-Sync instead of the Python engine's software renderer. Build it with `make -C c_apps/maties` and sideload with `numworks deploy-nwa c_apps/maties/output/app.nwa`. See [docs/c-apps-sdk.md](../docs/c-apps-sdk.md).

### 1. Floom (`games/floom.py`)
- **Genre**: 3D Raycasting Maze Crawler
- **Features**:
  - Generative 16x16 maze layout
  - Guinea pig enemy sprites
  - Clipped minimap
  - Custom block-letter "FLOOM" title screen
- **Controls**:
  - `Arrow Keys`: Move & turn
  - `OK`: Shoot
  - `Clear` (`KEY_BACKSPACE`): Menu / Restart

### 2. Snake (`games/snake.py`)
- **Genre**: Classic 2D Grid Arcade
- **Features**: Compact, lightweight 2D grid rendering

---

## Game Development Standards

Before adding or modifying any game in this directory, ensure it adheres to the following rules:

1. **Memory Safety**:
   - Must pass static allocation audit:
     ```bash
     python3 tools/test_allocs.py games/your_game.py
     ```
   - Must have **zero dynamic allocations** inside the main game loop.
   - Use `bytearray` for fixed integer arrays; avoid lists where possible.
   - Avoid multiple assignments (`a, b = c, d`) and tuple returns in hot loops.

2. **Size Budget**:
   - Total uncompressed script size should be **under 20 KB** (ideally < 15 KB).
   - Use `python3 tools/minify.py your_game.py` if comments/docstrings push size over limit.

3. **Key Mappings**:
   - **Never use `ion.KEY_BACK`** (it terminates the Python app).
   - Use `ion.KEY_BACKSPACE` (Clear key) or `ion.KEY_EXE` for in-game menus and restarts.

4. **Deploying to Hardware**:
   ```bash
   numworks deploy games/floom.py --clean
   ```
