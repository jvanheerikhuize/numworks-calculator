# NumWorks MicroPython Language Gotchas & Restrictions

This reference covers specific syntax limitations, missing standard library modules, and runtime behavioral quirks in Epsilon OS MicroPython.

---

## 1. Syntax Restrictions

### 1.1 No F-Strings
Stock Epsilon MicroPython does not support PEP 498 format string literals:
```python
# SYNTAX ERROR:
msg = f"Score: {score}"

# VALID:
msg = "Score: " + str(score)
msg = "Score: {}".format(score)
msg = "Score: %d" % score
```

### 1.2 No Extended Unpacking (`*args` with positional arguments)
Placing a positional argument after an unpacked sequence triggers a syntax error:
```python
# SYNTAX ERROR in Epsilon:
kandinsky.fill_rect(*rect, color)

# VALID:
kandinsky.fill_rect(rect[0], rect[1], rect[2], rect[3], color)
```
Unpacking is only supported when the `*iterable` is the final parameter in the call.

### 1.3 Tuple Unpacking in Loops Allocates Memory
While syntactically valid, multiple assignment creates temporary tuple objects:
```python
# ALLOCATES HEAP (dangerous in 20 FPS game loops):
dx, dy = target_x - px, target_y - py
for dx, dy in ((1, 0), (-1, 0)): ...

# ZERO ALLOCATION (safe for hot loops):
dx = target_x - px
dy = target_y - py
```

### 1.4 Unsupported Modern Features
- **Walrus operator (`:=`)**: Not supported
- **Structural pattern matching (`match/case`)**: Not supported
- **Positional-only parameters (`/`)**: Not supported

---

## 2. Missing Standard Library Modules

The following modules are **completely absent** from Epsilon OS:
- `os` / `uos` (no filesystem)
- `sys` (no system exit/argv)
- `array` (use built-in `bytearray` instead)
- `struct` (no binary unpacking in Python space)
- `json` (parse simple strings manually)
- `re` (use string methods: `find`, `split`, `replace`)
- `socket`, `network`, `requests` (no network hardware)

### Available Modules:
- `kandinsky` (graphics: `fill_rect`, `draw_string`, `color`, `get_pixel`, `set_pixel`)
- `ion` (keyboard: `keydown`, `KEY_*`)
- `math` (`cos`, `sin`, `tan`, `sqrt`, `atan2`, `pi`, `radians`, etc.)
- `random` (`randint`, `random`, `choice`, `randrange`)
- `time` (`monotonic()`, `sleep()`)
- `gc` (`collect()`, `mem_alloc()`, `mem_free()`)

---

## 3. Hardware / OS Traps

### 3.1 `KEY_BACK` is a Hard Kill Switch
Epsilon's native window manager intercepts `ion.KEY_BACK` at the kernel level. Pressing it forcefully terminates the Python interpreter and returns to the home screen.
- **Do not use `KEY_BACK` for in-game menus or pause screens.**
- **Use `KEY_BACKSPACE` (the physical `Clear` key)** or `KEY_EXE` instead.

### 3.2 Key Detection is Non-Latching
`ion.keydown(KEY)` checks the instantaneous electrical contact state.
To implement a single-shot press (e.g., shooting a weapon):
```python
ok = ion.keydown(ion.KEY_OK)
if ok and not prev_ok:
    shoot()
prev_ok = ok
```

### 3.3 Kandinsky Has No Double-Buffering
All `fill_rect` calls write directly to LCD controller memory.
- Clearing the entire screen and then drawing objects on top produces heavy visible flicker.
- Draw in a **single pass column-by-column** (e.g., ceiling slice, wall slice, floor slice).
