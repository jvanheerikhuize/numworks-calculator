# NumWorks Calculator Games

A collection of optimized games for the NumWorks N0120 graphing calculator running Epsilon OS.

---

## Games Collection

### 1. Maties (`games/maties.py`)
- **Genre**: 3D Raycasting PvE Wave Survival Shooter
- **Features**:
  - Distance flow field enemy AI (zero-allocation O(1) pathfinding)
  - 8-enemy active tracking via fixed-size C-style parallel arrays
  - Real-time HUD and live radar display
  - Single-pass non-overlapping column renderer (zero flicker)
  - Custom retro red block-letter "MATIES" title screen
  - Wave progression, score multiplier, muzzle flash, hit markers
- **Controls**:
  - `Arrow Keys`: Move forward/backward, rotate left/right
  - `OK`: Fire weapon
  - `Clear` (`KEY_BACKSPACE`): In-game restart / menu

### 2. Floom (`games/floom.py`)
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

### 3. Snake (`games/snake.py`)
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
   numworks deploy games/maties.py --clean
   ```
