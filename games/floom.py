import kandinsky
import ion
import math
import time
import random

SW, SH = 320, 222
FOV = math.pi / 3
HALF_FOV = FOV / 2
CASTED_RAYS = 80
STEP_ANGLE = FOV / CASTED_RAYS
STRIP_WIDTH = SW // CASTED_RAYS
MAX_DEPTH = 16
MAP_SIZE = 16

COLOR_WALL = (150, 150, 150)
COLOR_FLOOR = (50, 50, 50)
COLOR_CEIL = (100, 150, 200)
COLOR_FLASH = (255, 255, 200)

MAP = []
enemies = []

def init_game():
    global MAP, enemies
    MAP = [["#" for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
    stack = [(1, 1)]
    MAP[1][1] = "."
    while stack:
        x, y = stack[-1]
        neighbors = []
        for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
            nx, ny = x + dx, y + dy
            if 0 < nx < MAP_SIZE - 1 and 0 < ny < MAP_SIZE - 1 and MAP[ny][nx] == "#":
                neighbors.append((nx, ny, dx, dy))
        if neighbors:
            nx, ny, dx, dy = random.choice(neighbors)
            MAP[y + dy//2][x + dx//2] = "."
            MAP[ny][nx] = "."
            stack.append((nx, ny))
        else:
            stack.pop()
    for _ in range(15):
        MAP[random.randint(1, MAP_SIZE-2)][random.randint(1, MAP_SIZE-2)] = "."
        
    enemies = []
    for _ in range(8):
        while True:
            ex, ey = random.randint(1, MAP_SIZE-2), random.randint(1, MAP_SIZE-2)
            if MAP[ey][ex] == "." and (ex != 1 or ey != 1):
                enemies.append([ex + 0.5, ey + 0.5, True])
                break

def get_sprite_segs(pct):
    bc = (139, 69, 19)
    ec = (255, 0, 0)
    nc = (255, 150, 150)
    if pct < 0.15 or pct > 0.85:
        return [(0.3, 0.9, bc)]
    elif pct < 0.35 or pct > 0.65:
        return [(0.2, 0.35, bc), (0.35, 0.5, ec), (0.5, 0.9, bc)]
    else:
        return [(0.2, 0.6, bc), (0.6, 0.8, nc), (0.8, 0.9, bc)]

def draw_rect(x, y, w, h, c):
    y2 = y + h
    if x >= 260 and y < 55:
        if y2 <= 55: return
        y = 55
        h = y2 - y
    if h > 0:
        kandinsky.fill_rect(int(x), int(y), int(w), int(h), c)

def draw_bg(x, y1, y2, wy1, wy2, wc):
    if y1 < wy1:
        ey = min(y2, wy1)
        draw_rect(x, y1, STRIP_WIDTH, ey - y1, COLOR_CEIL)
        y1 = ey
    if y1 < wy2 and y1 < y2:
        ey = min(y2, wy2)
        draw_rect(x, y1, STRIP_WIDTH, ey - y1, wc)
        y1 = ey
    if y1 < y2:
        draw_rect(x, y1, STRIP_WIDTH, y2 - y1, COLOR_FLOOR)

def render(px, py, pa, flash):
    start_angle = pa - HALF_FOV
    
    ray_sprites = [None] * CASTED_RAYS
    for e in enemies:
        if not e[2]: continue
        dx, dy = e[0] - px, e[1] - py
        dist = math.sqrt(dx*dx + dy*dy)
        angle = math.atan2(dy, dx)
        diff = angle - pa
        while diff < -math.pi: diff += 2 * math.pi
        while diff > math.pi: diff -= 2 * math.pi
        
        if abs(diff) < HALF_FOV + 0.3 and dist > 0.5:
            screen_x = int((0.5 * (diff / HALF_FOV) + 0.5) * CASTED_RAYS)
            s_dist = dist * math.cos(diff)
            if s_dist < 0.1: s_dist = 0.1
            s_size = int((SH / 2) / s_dist)
            
            sx = max(0, screen_x - s_size // 4)
            ex = min(CASTED_RAYS, screen_x + s_size // 4)
            for r in range(sx, ex):
                if ray_sprites[r] is None or s_dist < ray_sprites[r][0]:
                    pct = (r - (screen_x - s_size // 4)) / max(1, (s_size // 2))
                    ray_sprites[r] = (s_dist, s_size, pct, e)

    for ray in range(CASTED_RAYS):
        ray_angle = start_angle + ray * STEP_ANGLE
        sin_a, cos_a = math.sin(ray_angle), math.cos(ray_angle)
        
        depth = 0.0
        tx, ty = 0.0, 0.0
        while depth < MAX_DEPTH:
            tx, ty = px + cos_a * depth, py + sin_a * depth
            ix, iy = int(tx), int(ty)
            if ix < 0 or ix >= MAP_SIZE or iy < 0 or iy >= MAP_SIZE or MAP[iy][ix] == '#':
                break
            depth += 0.2
            
        x_pos = ray * STRIP_WIDTH
        if flash:
            draw_rect(x_pos, 0, STRIP_WIDTH, SH, COLOR_FLASH)
            continue
            
        depth *= math.cos(pa - ray_angle)
        if depth < 0.1: depth = 0.1
            
        proj_h = int((SH / 2) / depth)
        wy1 = max(0, (SH // 2) - proj_h)
        wy2 = min(SH, (SH // 2) + proj_h)
        
        # Texture panels
        tx_coord = int((tx + ty) * 8) % 8
        c_val = max(50, int(255 - depth * 15))
        if tx_coord < 2:
            wc = (c_val//2, c_val//2, c_val//2)
        elif tx_coord == 2:
            wc = (min(255, c_val*5//4), min(255, c_val*5//4), min(255, c_val*5//4))
        else:
            wc = (c_val, c_val, c_val)
        
        sp = ray_sprites[ray]
        if sp and sp[0] < depth:
            s_dist, s_size, pct = sp[0], sp[1], sp[2]
            sy = (SH // 2) - s_size
            sh = s_size * 2
            
            segs = get_sprite_segs(pct)
            cur_y = 0
            for (sy_pct, ey_pct, color) in segs:
                seg_y1 = max(0, sy + int(sy_pct * sh))
                seg_y2 = min(SH, sy + int(ey_pct * sh))
                draw_bg(x_pos, cur_y, seg_y1, wy1, wy2, wc)
                if seg_y1 < seg_y2:
                    draw_rect(x_pos, seg_y1, STRIP_WIDTH, seg_y2 - seg_y1, color)
                cur_y = seg_y2
            draw_bg(x_pos, cur_y, SH, wy1, wy2, wc)
        else:
            draw_bg(x_pos, 0, SH, wy1, wy2, wc)

def main_menu():
    kandinsky.fill_rect(0, 0, 320, 222, (0, 0, 0))
    fc = (255, 0, 0)
    kandinsky.fill_rect(60, 40, 40, 10, fc); kandinsky.fill_rect(60, 40, 10, 50, fc); kandinsky.fill_rect(60, 60, 30, 10, fc)
    kandinsky.fill_rect(110, 40, 10, 50, fc); kandinsky.fill_rect(110, 80, 30, 10, fc)
    kandinsky.fill_rect(150, 40, 30, 50, fc); kandinsky.fill_rect(160, 50, 10, 30, (0,0,0))
    kandinsky.fill_rect(190, 40, 30, 50, fc); kandinsky.fill_rect(200, 50, 10, 30, (0,0,0))
    kandinsky.fill_rect(230, 40, 10, 50, fc); kandinsky.fill_rect(240, 50, 10, 20, fc); kandinsky.fill_rect(250, 40, 10, 50, fc)
    
    kandinsky.draw_string("by legendary noobs gaming, 2026", 5, 105, (150, 150, 150), (0, 0, 0))
    kandinsky.draw_string("Press OK to Start", 80, 140, (255, 255, 255), (0, 0, 0))
    kandinsky.draw_string("Press CLEAR to Menu/Restart", 25, 170, (150, 150, 150), (0, 0, 0))
    kandinsky.draw_string("Press HOME to Quit", 70, 190, (100, 100, 100), (0, 0, 0))
    time.sleep(0.5)
    while True:
        if ion.keydown(ion.KEY_OK): return True
        if ion.keydown(ion.KEY_HOME): return False
        time.sleep(0.05)

def run():
    px, py, pa = 1.5, 1.5, 0.0
    flash_frames = 0
    score, last_score = 0, -1
    
    kandinsky.fill_rect(0, 0, SW, SH//2, COLOR_CEIL)
    kandinsky.fill_rect(0, SH//2, SW, SH//2, COLOR_FLOOR)
    
    kandinsky.fill_rect(260, 0, 60, 55, (30, 30, 30))
    mx, my = 265, 3
    for iy in range(MAP_SIZE):
        for ix in range(MAP_SIZE):
            c = (150, 150, 150) if MAP[iy][ix] == '#' else (50, 50, 50)
            kandinsky.fill_rect(mx + ix*3, my + iy*3, 3, 3, c)
            
    for e in enemies:
        kandinsky.fill_rect(mx + int(e[0]*3)-1, my + int(e[1]*3)-1, 3, 3, (255, 0, 0))
        
    old_px, old_py = px, py
    
    while True:
        if ion.keydown(ion.KEY_BACKSPACE):
            break
            
        if flash_frames > 0: flash_frames -= 1
            
        if ion.keydown(ion.KEY_OK) and flash_frames == 0:
            flash_frames = 2
            for e in enemies:
                if not e[2]: continue
                dx, dy = e[0] - px, e[1] - py
                dist = math.sqrt(dx*dx + dy*dy)
                diff = math.atan2(dy, dx) - pa
                while diff < -math.pi: diff += 2*math.pi
                while diff > math.pi: diff -= 2*math.pi
                
                if abs(diff) < 0.2 and dist < 8.0:
                    e[2] = False
                    score += 1
                    kandinsky.fill_rect(mx + int(e[0]*3)-1, my + int(e[1]*3)-1, 3, 3, (50, 50, 50))
            
        if ion.keydown(ion.KEY_LEFT): pa -= 0.2
        if ion.keydown(ion.KEY_RIGHT): pa += 0.2
            
        if ion.keydown(ion.KEY_UP):
            nx, ny = px + math.cos(pa) * 0.3, py + math.sin(pa) * 0.3
            if MAP[int(ny)][int(nx)] != '#': px, py = nx, ny
        if ion.keydown(ion.KEY_DOWN):
            nx, ny = px - math.cos(pa) * 0.3, py - math.sin(pa) * 0.3
            if MAP[int(ny)][int(nx)] != '#': px, py = nx, ny
                
        render(px, py, pa, flash_frames > 0)
        
        if score != last_score:
            kandinsky.draw_string("Score: {}".format(score), 5, 5, (255,255,255), COLOR_CEIL)
            last_score = score
            
        if int(old_px*3) != int(px*3) or int(old_py*3) != int(py*3):
            c = (150, 150, 150) if MAP[int(old_py)][int(old_px)] == '#' else (50, 50, 50)
            kandinsky.fill_rect(mx + int(old_px*3)-1, my + int(old_py*3)-1, 3, 3, c)
            for e in enemies:
                if e[2]: kandinsky.fill_rect(mx + int(e[0]*3)-1, my + int(e[1]*3)-1, 3, 3, (255, 0, 0))
            old_px, old_py = px, py
            
        kandinsky.fill_rect(mx + int(px*3)-1, my + int(py*3)-1, 3, 3, (0, 255, 0))
        
        if sum(1 for e in enemies if e[2]) == 0:
            kandinsky.fill_rect(0, 0, SW, SH, (0, 0, 0))
            kandinsky.draw_string("YOU WIN!", 120, 100, (0, 255, 0), (0, 0, 0))
            kandinsky.draw_string("Press CLEAR to Restart", 50, 130, (255, 255, 255), (0, 0, 0))
            while not ion.keydown(ion.KEY_BACKSPACE): time.sleep(0.1)
            break

try:
    while main_menu():
        init_game()
        run()
except Exception as e:
    kandinsky.draw_string("Error: {}".format(e), 0, 0)
    while not ion.keydown(ion.KEY_BACKSPACE): time.sleep(0.1)
