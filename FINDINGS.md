# NumWorks Epsilon Python Environment Findings

This document summarizes the technical findings, memory constraints, and DFU quirks discovered while developing complex games (like 3D raycasters `FLOOM` and `Maties`) for the NumWorks N0120 calculator running Epsilon OS.

## 1. Storage Buffer & Memory Limits
- **Buffer Size**: Epsilon allocates exactly 43,008 bytes (42KB) of flash memory/RAM for the Python script storage buffer. 
- **Padding & Footer**: The buffer *must* be padded with `\x00` bytes to exactly 43,008 bytes and MUST end with the 32-bit magic footer `BADD0BEE`. If this footer is missing, Epsilon assumes the memory is corrupt and quietly restores factory default scripts (`squares.py`, etc.).
- **System Scripts**: The buffer contains two hidden system records: `gp.sys` and `pr.sys`. If these are removed or corrupted, Epsilon may reject the buffer and trigger a factory reset of the Python environment.

## 2. MicroPython Compiler & Heap Constraints
The calculator has an extremely limited heap (~30-40KB) for MicroPython. Memory allocation errors (`MemoryError: memory allocation failed, allocating XXXX bytes`) are common and typically caused by two things:
1. **Abstract Syntax Tree (AST) Size**: Large list-of-lists literals (e.g., a 32x16 integer map `MAP = [[1, 1...], ...]`) require massive amounts of heap space to compile into an AST. 
   - *Fix*: Compress large arrays into a single string (e.g., `MAP_STR = "111000..."`) and parse them at runtime using integer math. This drastically reduces compilation memory.
2. **Heap Fragmentation**: Dynamic list allocations inside loops (e.g., `pieces = []` or list comprehensions like `[(x, y) for ...]`) quickly fragment the tiny heap.
   - *Fix*: Avoid allocating lists during the main game loop. Use in-place updates, pre-allocated `bytearray` buffers, or iterative logic. Calling `import gc; gc.collect()` at the start of a frame also helps mitigate fragmentation.

## 3. Graphics & Rendering (Kandinsky)
- **No Hardware Double-Buffering**: The NumWorks display controller updates the screen immediately when `kandinsky.fill_rect` is called. 
- **Tearing/Flickering**: Clearing the screen (e.g., drawing a full ceiling/floor background) and then drawing sprites on top causes severe flickering because intermediate frames are drawn to the screen.
- *Fix*: To achieve flicker-free rendering, use a "single-pass" vertical strip renderer. Calculate exactly what needs to be drawn for each vertical column (ceiling, wall, sprite slices, floor) and draw them sequentially with non-overlapping `fill_rect` calls.

## 4. USB DFU Protocol Quirks
- **DFU Upload State Bug**: After performing a DFU `upload` command to read the memory buffer, the calculator's USB endpoint is left stalled in the `dfuUPLOADIDLE` state. You MUST send an `abort()` request to return it to `dfuIDLE` before issuing further commands (like `set_address` or `download`), otherwise it will throw `[Errno 19] No such device`.
- **Reconnections**: Sending the `DETACH` request gracefully exits USB mode and reboots Epsilon. To send further commands, the calculator must be physically replugged or manually returned to the USB "Connected" screen.

## 5. Python Syntax
- **No F-Strings**: Stock Epsilon MicroPython lacks support for Python f-strings (`f"Score: {score}"`). You must use `.format()` or `%` formatting.
- **Key Intercepts**: Epsilon natively traps `ion.KEY_BACK` as a hard interrupt for the Python script. If you need a "Menu" or "Restart" button inside a script loop without crashing the app, map it to `ion.KEY_CLEAR` (which is named `KEY_BACKSPACE` in the `ion` module) or `KEY_EXE`.


## 6. MicroPython Syntax Constraints
- **Extended Iterable Unpacking**: Epsilon OS runs a slightly older version of MicroPython that does not fully support Python 3.5+ extended unpacking syntax. Placing a positional argument *after* an unpacked tuple (e.g., `kandinsky.fill_rect(*r, color)`) will throw a `SyntaxError` at compilation time.
- *Fix*: Always manually index the unpacked elements (e.g., `kandinsky.fill_rect(r[0], r[1], r[2], r[3], color)`) or place the unpacked iterable at the very end of the argument list.

## 7. Garbage Collection & Heap Tuning
- When complex geometric functions (like dynamic rect-hole subtraction for UI clipping) are forced to allocate temporary lists (`pieces = []`) hundreds of times per frame, the tiny 30KB heap rapidly fragments, leading to a `MemoryError` even if the average memory used is small.
- *Fix*: If you cannot eliminate the list allocations entirely, you MUST explicitly call `import gc; gc.collect()` at the beginning of your main game loop. This ensures the heap is completely defragmented before the heavy per-frame allocations begin, allowing complex pure-Python geometry engines to run stably.

## 8. Micro-Allocations & Intra-Frame Fragmentation
- Even with `gc.collect()` at the start of a frame, calling functions that create small, temporary lists or tuples inside hot loops (like drawing 40 vertical columns) will cause intra-frame fragmentation. 
- In our case, a geometry clipping function returning a small list of tuples caused `MemoryError: memory allocation failed, allocating 417 bytes` because it exhausted the heap *before* the frame finished and the next garbage collection cycle could run.
- *Fix*: Hot loop rendering functions must be entirely mathematically driven. Use recursive calls or inline calculations to process geometry pieces sequentially, rather than appending them to a list and processing the list later. **Zero-allocation design is mandatory for 3D graphics on Epsilon.**

## 9. Generator Expressions and Hidden Allocations
- In Python, generator expressions like `any(x)` or `sum(1 for x in list if cond)` dynamically allocate generator objects in memory. While tiny (usually ~60 bytes), calling these continuously in a hot game loop (e.g. checking if any enemies are alive every frame) will silently fragment the micro-heap and cause `545 bytes` memory errors.
- *Fix*: Rewrite all generator expressions into classic imperative `for` loops with accumulator variables. 

## 10. List vs Bytearray for Global Arrays
- In MicroPython, allocating a global list of integers like `[0] * 512` dynamically allocates an array of object pointers, not raw bytes. A 512-element list requires a single contiguous memory block of ~2500 bytes. Because the heap is small (30KB) and highly fragmented after parsing the script's AST, allocating a 2500-byte list during `init()` will routinely crash with `MemoryError: memory allocation failed, allocating 2543 bytes`.
- *Fix*: If you need a large contiguous array of integers (e.g. for BFS queues, distance fields, etc.), **always use `bytearray(N)` instead of `[0]*N`**. A `bytearray` of 512 elements takes exactly 512 bytes, uses primitive C arrays without pointer overhead, and easily fits in the fragmented heap.

## 11. Static Memory Analysis Requirement
- **The Tuple Unpacking Trap**: In older MicroPython engines, simply returning multiple variables (`return x, y`) or unpacking assignments (`a, b = c, d`) dynamically allocates a temporary tuple object on the heap. If done in a hot render loop, these micro-allocations will fracture the heap and eventually trigger a `MemoryError` (e.g., `allocating 319 bytes`).
- *Fix*: Use `test_allocs.py` to statically verify that no dynamic lists, tuples, or generators are allocated outside of the initialization phase. **All future scripts must pass this static AST check before deployment.**

## 12. Complete Rewrite Lessons (Session 2)
- **Shadowed Parameters Bug**: When converting `_dda_step` to use global return variables (`DDA_SIDE`, `DDA_MAP_X`, etc.), the `_dda_depth` function's parameter list was changed to use the global names but the function body still referenced the old local names (`side`, `map_x`, `cos_a`, etc.). This caused a silent crash at runtime. Lesson: when refactoring return values to globals, update ALL references in ALL calling functions.
- **Dict Comprehension with Unpacking**: `{v: kd.color(*rgb) for v, rgb in WALL_RGB.items()}` uses `*rgb` argument unpacking, which is not supported in Epsilon's MicroPython. Replace with an explicit if-chain function.
- **Undefined Constants**: After aggressive variable renaming, `CROSSHAIR_ARM`, `CROSSHAIR_GAP`, and `CROSSHAIR_THICK` were referenced in `draw_crosshair()` but never defined. The crosshair was rewritten to use inline numeric constants.
- **Script Size vs Heap**: A 21KB script was eating ~12KB of heap just for AST compilation, leaving barely any room for runtime allocations. Reducing the script to ~15KB freed ~6KB of heap — enough to eliminate all initialization crashes.
- **EA/vi as bytearray**: Enemy active flags (`EA`) and visibility indices (`vi`) only need values 0-255, so they were converted from Python `list` (8 bytes/element) to `bytearray` (1 byte/element).
- **gc.collect() during init**: Calling `gc.collect()` between groups of allocations during `init_tables()` allows the heap to be defragmented mid-initialization, preventing the cascading fragmentation that caused the original 2543-byte allocation failure.
