# NumWorks MicroPython Memory Model & Optimization Guide

A comprehensive technical guide to the memory architecture, constraints, and optimization strategies for running Python on the NumWorks N0120 (Epsilon OS).

---

## 1. Physical Memory Budget

| Region | Physical Size | Accessible to MicroPython | Notes |
|---|---|---|---|
| **MCU Internal SRAM** | 256 KB | ~32 KB | Remainder reserved by Epsilon kernel, display LTDC, stacks |
| **Python Heap** | **32 KB** | 100% | Single unified heap for bytecode, AST, globals, and runtime objects |
| **Python Script Storage** | **43,008 B** | N/A (Flash/RAM) | Dedicated storage buffer holding raw script files (.py) |

> [!CAUTION]
> The **32 KB heap limit is shared between compilation and execution**. A script that is 20 KB on disk may consume 10–15 KB of heap simply to build its Abstract Syntax Tree (AST) before line 1 even runs.

---

## 2. Heap Lifecycle & Compiling Overhead

When a user selects and launches a script in the Python app:
1. **Source Loading**: The script string is read into RAM.
2. **Lexing & Parsing**: The AST is built on the heap. Large nested literals (`[[...]]`, large dicts) explode AST node count.
3. **Bytecode Emission**: Compiled bytecode is generated in heap RAM.
4. **AST Deallocation**: The AST is freed, but the heap is left fragmented with small allocations.
5. **Execution**: Global statements execute. If large lists are allocated here, heap exhaustion occurs.

### Optimization: Compile-Time Footprint Reduction
- **Dense String Encoding**: Never define large 2D arrays as list-of-lists (`[[1, 0, ...], ...]`). Encode maps as flat strings (`MAP_STR = "1001..."`) and index mathematically: `MAP_STR[y * COLS + x]`.
- **Short Variable Names**: Shortening internal names reduces bytecode string table size and AST memory.
- **Pre-deploy Minification**: Run `tools/minify.py` to strip comments, docstrings, and blank lines before uploading.

---

## 3. Data Structures: `bytearray` vs `list`

In standard MicroPython:
- An integer `list` like `[0] * 512` allocates an array of 512 **object pointers** (4 bytes each) plus list header = **~2,100 to 2,500 bytes** of contiguous heap.
- If the heap is already fragmented, finding a contiguous block of 2.5 KB will fail with:
  ```
  MemoryError: memory allocation failed, allocating 2543 bytes
  ```
- A `bytearray(512)` allocates a flat, primitive C byte buffer = **exactly 512 bytes** with zero pointer overhead.

### Rule:
| Use Case | Data Structure | Why |
|---|---|---|
| Fixed integer buffers (0–255) | `bytearray(N)` | 1 byte/element, zero pointer overhead |
| BFS / Flood fill queues | Pair of `bytearray(N)` | `BQX`, `BQY` instead of list of tuples |
| Distance / Flow fields | `bytearray(N)` | Max distance in 32x16 map is 48, fits in uint8 |
| Active flags / Index buffers | `bytearray(N)` | 1 byte vs 8 bytes per slot in list |
| Floating point arrays | Pre-allocated `[0.0] * N` | Allocate *only* during `init()` at startup |

---

## 4. Zero-Allocation Game Loop Design

For real-time 3D or 2D rendering on Epsilon, **the game loop must perform zero dynamic allocations**.

### Banned in Hot Loops:
1. **List / Dict creation**: `items = []`, `coords = {}`
2. **List comprehensions**: `[f(x) for x in arr]`
3. **Generator expressions**: `sum(1 for x in arr if x)` or `any(arr)` (allocates ~60-byte generator objects)
4. **Tuple packing / unpacking**: `a, b = c, d` or returning `return x, y` (allocates temporary tuples)
5. **Dynamic geometry subtraction**: Creating `pieces = []` to slice rectangles for UI clipping

### Permitted Patterns:
- **Global C-Style Return Variables**: Set `DDA_HIT = hit`, `DDA_SIDE = side` instead of `return hit, side`.
- **Pre-allocated Work Buffers**: Pre-allocate sort buffers (`vis_depth = [0.0] * 8`, `vis_idx = bytearray(8)`) and sort in-place with insertion sort.
- **Imperative Accumulator Loops**:
  ```python
  # BAD (allocates generator):
  alive = sum(1 for a in EA if a)

  # GOOD (zero allocation):
  alive = 0
  for i in range(MAX_ENEMIES):
      if EA[i]: alive += 1
  ```

---

## 5. Garbage Collection Strategy

- Call `gc.collect()` explicitly at the **start of each frame** in the main loop.
- Call `gc.collect()` **between groups of allocations** during initialization (`init_tables()`).
- Monitor heap in development using:
  ```python
  import gc
  print("Allocated:", gc.mem_alloc(), "Free:", gc.mem_free())
  ```
- Statically audit any script before flashing:
  ```bash
  python3 tools/test_allocs.py games/my_game.py
  ```
