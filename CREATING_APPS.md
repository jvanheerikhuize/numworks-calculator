# 🎮 How to Make Games & Apps for NumWorks (Beginner's Guide)

Welcome! If you have a NumWorks calculator (like the N0120), you are holding a tiny, powerful handheld computer. It has an ARM Cortex processor running at up to 550 MHz and a crisp color screen.

This guide will teach you how to build your own games from scratch—no previous calculator hacking experience required!

---

## 🧭 The Two Ways to Build Games

You can build games in two different ways. Pick the one that fits what you want to do:

| Feature | 🐍 Route 1: Python Script | ⚡ Route 2: Native C App |
|---|---|---|
| **Difficulty** | Super easy & fast to write | A little more code, but blazing fast |
| **Where it appears** | Inside the calculator's **Python** app | As its **own app icon** on the main home screen! |
| **Speed** | Good for 2D games, puzzles, turn-based RPGs | Ultra-smooth **60 FPS** (perfect for 3D games & fast arcade action) |
| **Screen Area** | 320 × 222 (top bar is reserved by the OS) | **Full 320 × 240** (you own every single pixel) |
| **Storage Limit** | ~42 KB | **Up to 2.5 MB – 6 MB** (plenty of room for music, maps, and graphics!) |

---

## 📐 How the Screen Works

Think of the screen as a grid of tiny light dots called **pixels**:
- **Width (X)**: 320 pixels across (from `0` on the far left to `319` on the far right).
- **Height (Y)**: 240 pixels tall (from `0` at the very top to `239` at the bottom).
- The point `(0, 0)` is the **top-left corner**.

```
(0,0) ------------------------> X (319)
  |
  |     Your Game Screen
  |
  v
Y (239)
```

---

## 🐍 Route 1: Making a Python Game

### Step 1: The Three Magic Modules
Every NumWorks Python game uses three built-in tools:
1. `import kandinsky as kd` — Used to draw colors, rectangles, and text.
2. `import ion` — Used to check which buttons you are pressing.
3. `import time` — Used to control game speed and delays.

### Step 2: Drawing on the Screen
```python
import kandinsky as kd

# Draw a red rectangle: fill_rect(x, y, width, height, color)
kd.fill_rect(50, 40, 60, 30, kd.color(255, 0, 0))

# Draw some text: draw_string(text, x, y, text_color, background_color)
kd.draw_string("Hello Player 1!", 10, 10, kd.color(255, 255, 255), kd.color(0, 0, 0))
```

### Step 3: Checking Keys
```python
import ion

if ion.keydown(ion.KEY_RIGHT):
    player_x += 2
if ion.keydown(ion.KEY_LEFT):
    player_x -= 2
```

### 📋 The Starter Python Game Template
Save this as `games/my_game.py`. You control a moving square on screen!

```python
import kandinsky as kd
import ion
import time

# Player starting position and color
x = 140
y = 100
player_color = kd.color(0, 200, 255)
bg_color = kd.color(20, 20, 30)

# Clear the screen once at the start
kd.fill_rect(0, 0, 320, 222, bg_color)

# Game loop
while True:
    # 1. Check if user wants to quit (press Backspace / Clear key)
    if ion.keydown(ion.KEY_BACKSPACE):
        break

    # 2. Remember old position so we can erase the old square
    old_x = x
    old_y = y

    # 3. Handle player movement
    if ion.keydown(ion.KEY_LEFT) and x > 0:
        x -= 3
    if ion.keydown(ion.KEY_RIGHT) and x < 300:
        x += 3
    if ion.keydown(ion.KEY_UP) and y > 0:
        y -= 3
    if ion.keydown(ion.KEY_DOWN) and y < 200:
        y += 3

    # 4. Redraw only if the player moved (keeps the game smooth!)
    if x != old_x or y != old_y:
        kd.fill_rect(old_x, old_y, 20, 20, bg_color)    # Erase old position
        kd.fill_rect(x, y, 20, 20, player_color)        # Draw new position

    # 5. Short pause to keep game speed steady (~50 FPS)
    time.sleep(0.02)
```

### Step 4: Send It to Your Calculator!
Plug in your calculator using USB, make sure the calculator says **"Connected"**, and in your terminal run:

```bash
numworks deploy games/my_game.py
```

The tool will automatically verify your code is clean and push it directly to your calculator! Now open the **Python** app on your NumWorks and select `my_game` to play.

> [!TIP]
> **Golden Rules for NumWorks Python:**
> 1. **Do not use `KEY_BACK`**: The calculator's operating system uses the `back` key to kill Python apps instantly. Always use `KEY_BACKSPACE` (the physical **Clear** button) instead for in-game menus!
> 2. **Keep it under 20 KB**: Calculators have tiny memory heaps. Check your code anytime with `python3 tools/test_allocs.py games/my_game.py`.

---

## ⚡ Route 2: Making a Native C App (60 FPS Power!)

If you want to build super-fast 3D games (like our **Maties** raycaster), smooth arcade games, or your own custom app with an icon on the home screen, native C is the way to go.

### Step 1: How Native Apps Work
Native apps are written in C, compiled into an ARM `.nwa` (NumWorks Application) file, and sideloaded into the calculator's flash memory. When you turn on your calculator, your game sits right next to the built-in apps like Calculation and Grapher!

### Step 2: Copy the Starter Template
We created a ready-to-use template in `c_apps/sample_app/`. To make your own game, simply copy it:

```bash
cp -r c_apps/sample_app c_apps/super_game
```

### Step 3: Customize Your Game's Name & Icon
1. Open `c_apps/super_game/src/main.c` in an editor.
2. Change the app name at the top:
   ```c
   const char eadk_app_name[] __attribute__((section(".rodata.eadk_app_name"))) = "SuperGame";
   ```
3. (Optional) Replace `c_apps/super_game/src/icon.png` with your own 55×56 pixel PNG drawing.

### 📋 The Starter C Game Template (`src/main.c`)
Here is a complete, clean 60 FPS bouncing ball game in C:

```c
#include <eadk.h>
#include <stdbool.h>

// App metadata
const char eadk_app_name[] __attribute__((section(".rodata.eadk_app_name"))) = "Bouncy";
const uint32_t eadk_api_level __attribute__((section(".rodata.eadk_api_level"))) = 0;

// Color helper (Red, Green, Blue from 0 to 255)
#define RGB(r, g, b) (eadk_color_t)((((r) >> 3) << 11) | (((g) >> 2) << 5) | ((b) >> 3))

int main(int argc, char * argv[]) {
  // Clear the whole screen to dark navy
  eadk_color_t bg_color = RGB(15, 15, 25);
  eadk_display_push_rect_uniform(eadk_screen_rect, bg_color);

  // Ball position and speed
  int x = 160, y = 120;
  int vx = 3, vy = 2;
  int size = 16;
  eadk_color_t ball_color = RGB(255, 220, 50);

  // Main game loop
  while (true) {
    // 1. Check for exit button (BACK key returns to home screen)
    eadk_keyboard_state_t kbd = eadk_keyboard_scan();
    if (eadk_keyboard_key_down(kbd, eadk_key_back)) {
      return 0; // Clean exit to calculator menu
    }

    // 2. Erase the old ball
    eadk_display_push_rect_uniform((eadk_rect_t){(uint16_t)x, (uint16_t)y, (uint16_t)size, (uint16_t)size}, bg_color);

    // 3. Move the ball
    x += vx;
    y += vy;

    // Bounce off walls
    if (x <= 0 || x + size >= EADK_SCREEN_WIDTH) vx = -vx;
    if (y <= 0 || y + size >= EADK_SCREEN_HEIGHT) vy = -vy;

    // 4. Draw new ball
    eadk_display_push_rect_uniform((eadk_rect_t){(uint16_t)x, (uint16_t)y, (uint16_t)size, (uint16_t)size}, ball_color);

    // 5. Hardware V-Blank sync: keeps your game running at buttery smooth 60 FPS!
    eadk_display_wait_for_vblank();
  }
}
```

### Step 4: Compile & Sideload in One Command!
1. Plug your calculator in with your USB cable.
2. In your terminal, run:

```bash
# 1. Compile the code
make -C c_apps/super_game

# 2. Sideload to your calculator
numworks deploy-nwa c_apps/super_game/output/app.nwa
```

You will see the upload progress bar hit 100%, your calculator will reboot to the home menu, and **Bouncy** will be sitting right there on your home screen! 🎉

---

## 🕹️ Button Cheat Sheet

Here are all the key names to use in your code:

| Calculator Key | Python (`ion`) | Native C (`eadk`) |
|---|---|---|
| ⬆️ Up Arrow | `ion.KEY_UP` | `eadk_key_up` |
| ⬇️ Down Arrow | `ion.KEY_DOWN` | `eadk_key_down` |
| ⬅️ Left Arrow | `ion.KEY_LEFT` | `eadk_key_left` |
| ➡️ Right Arrow | `ion.KEY_RIGHT` | `eadk_key_right` |
| 🔘 OK Button | `ion.KEY_OK` | `eadk_key_ok` |
| ↩️ EXE Button | `ion.KEY_EXE` | `eadk_key_exe` (or `eadk_key_ok`) |
| 🔙 Back Button | ⚠️ *Do not use in Python!* | `eadk_key_back` |
| ⌫ Clear Button | `ion.KEY_BACKSPACE` | `eadk_key_backspace` |
| 0️⃣ through 9️⃣ | `ion.KEY_ZERO` ... `ion.KEY_NINE` | `eadk_key_zero` ... `eadk_key_nine` |

---

## 💡 Quick Tips for Beginners

1. **Start Small**: Build a simple game first—like Pong, Snake, or a Maze game. Once that works, add high scores, sound effects, or power-ups!
2. **Look at Existing Code**: Check out `games/maties.py` (Python) and `c_apps/maties/src/main.c` (C) to see how a complete 3D game is built.
3. **Have Fun!** Showing off a game you coded yourself on a school calculator is one of the coolest feelings in computer science!
