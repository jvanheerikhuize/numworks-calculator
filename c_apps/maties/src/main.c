#include <eadk.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
#include <stdio.h>

// App Metadata
const char eadk_app_name[] __attribute__((section(".rodata.eadk_app_name"))) = "Maties";
const uint32_t eadk_api_level __attribute__((section(".rodata.eadk_api_level"))) = 0;

// Screen dimensions
#define SW 320
#define SH 240
#define HUD_H 20

// RGB565 color helper
#define RGB(r, g, b) (eadk_color_t)((((r) >> 3) << 11) | (((g) >> 2) << 5) | ((b) >> 3))

// Game Colors
static const eadk_color_t COLOR_WHITE       = RGB(255, 255, 255);
static const eadk_color_t COLOR_CEIL        = RGB(15, 15, 35);
static const eadk_color_t COLOR_FLOOR       = RGB(70, 60, 50);
static const eadk_color_t COLOR_WALL_1      = RGB(150, 40, 40);
static const eadk_color_t COLOR_WALL_2      = RGB(40, 90, 150);
static const eadk_color_t COLOR_WALL_3      = RGB(150, 150, 40);
static const eadk_color_t COLOR_WALL_4      = RGB(40, 150, 70);
static const eadk_color_t COLOR_WALL_5      = RGB(150, 40, 150);
static const eadk_color_t COLOR_WALL_DEF    = RGB(120, 120, 120);
static const eadk_color_t COLOR_ENEMY       = RGB(220, 40, 40);
static const eadk_color_t COLOR_ENEMY_OUT   = RGB(90, 10, 10);
static const eadk_color_t COLOR_HUD_BG      = RGB(10, 10, 16);
static const eadk_color_t COLOR_HUD_TEXT    = RGB(230, 230, 230);
static const eadk_color_t COLOR_WAVE_TEXT   = RGB(255, 220, 100);
static const eadk_color_t COLOR_HEALTH_BG   = RGB(40, 15, 15);
static const eadk_color_t COLOR_HEALTH_FG   = RGB(90, 200, 90);
static const eadk_color_t COLOR_HEALTH_LOW  = RGB(210, 50, 40);
static const eadk_color_t COLOR_CROSSHAIR   = RGB(255, 255, 255);
static const eadk_color_t COLOR_MUZZLE      = RGB(255, 250, 200);
static const eadk_color_t COLOR_HIT_FLASH   = RGB(255, 220, 80);
static const eadk_color_t COLOR_RETICLE_BG  = RGB(20, 20, 26);
static const eadk_color_t COLOR_RADAR_BG    = RGB(14, 18, 14);
static const eadk_color_t COLOR_RADAR_WALL  = RGB(90, 95, 60);
static const eadk_color_t COLOR_RADAR_PLYR  = RGB(255, 255, 255);
static const eadk_color_t COLOR_RADAR_ENMY  = RGB(230, 40, 40);
static const eadk_color_t COLOR_RADAR_BORD  = RGB(70, 80, 70);

// Map definition
#define ROWS 32
#define COLS 16
#define BSZ (ROWS * COLS)

static const char* MAP_STR = 
  "1111111111111111"
  "1000000000000001"
  "1003333000222001"
  "1000004000002001"
  "1000004000002001"
  "1003333000000001"
  "1000000000000001"
  "1000400040000001"
  "1113131113003111"
  "1111111111300311"
  "1111111111300311"
  "1131111111300311"
  "1400000000000001"
  "3000000000000001"
  "1000000000000001"
  "1002000003404301"
  "1005000000303001"
  "1002000000000001"
  "1000000000000001"
  "3000000000000001"
  "1400000040040001"
  "1133003313313111"
  "1111300311111111"
  "1133400433333333"
  "1300000000000003"
  "3000000000000003"
  "3000000000000003"
  "3005000500050003"
  "3000000000000003"
  "3000000000000003"
  "3000000000000003"
  "3333333333333333";

static inline int wall_at(int x, int y) {
  if (x < 0 || y < 0 || y >= ROWS || x >= COLS) return 1;
  return MAP_STR[y * COLS + x] - '0';
}

static inline eadk_color_t get_wall_color(int id) {
  switch (id) {
    case 1: return COLOR_WALL_1;
    case 2: return COLOR_WALL_2;
    case 3: return COLOR_WALL_3;
    case 4: return COLOR_WALL_4;
    case 5: return COLOR_WALL_5;
    default: return COLOR_WALL_DEF;
  }
}

// Raycaster Settings
#define NUM_RAYS 80
#define COL_W (SW / NUM_RAYS) // 4 pixels per column
#define FOV (3.14159265f / 3.0f)
#define HALF_FOV (FOV / 2.0f)
#define PROJ_DIST ((SW / 2.0f) / 0.57735027f) // tan(30 deg) = 1/sqrt(3)

// HUD & Reserved Rectangles
#define CSZ 16
#define CX0 (SW / 2 - CSZ / 2)
#define CX1 (CX0 + CSZ)
#define CY0 (SH / 2 - CSZ / 2)
#define CY1 (CY0 + CSZ)

#define RADAR_CELLS 11
#define RADAR_PX 7
#define RSZ (RADAR_CELLS * RADAR_PX)
#define RADAR_MARGIN 4
#define RX0 (SW - RSZ - RADAR_MARGIN)
#define RY0 (HUD_H + RADAR_MARGIN)
#define RX1 (RX0 + RSZ)
#define RY1 (RY0 + RSZ)

// Player State
static float px = 1.5f;
static float py = 5.5f;
static float pa = 0.0f;
static float av = 0.0f;
static int score = 0;
static int player_health = 100;
static float player_invuln = 0.0f;
static float muzzle_flash = 0.0f;
static float hit_flash_x = 0.0f;
static float hit_flash_time = 0.0f;
static int wave = 1;
static int wave_remaining = 0;
static float spawn_cd = 0.0f;
static int score_mult = 1;
static float wave_banner_time = 0.0f;
static float path_timer = 0.0f;
static int high_score = 0;

#define MOVE_SPEED 3.2f
#define ROT_SPEED 2.2f
#define ROT_ACCEL 11.0f

// Enemies
#define MAX_ENEMIES 8
#define ENEMY_SPEED 1.2f
#define ENEMY_TOUCH_RANGE 0.45f
#define ENEMY_DAMAGE 10
#define SPAWN_MIN_DIST 6.5f

typedef struct {
  float x;
  float y;
  bool alive;
} Enemy;

static Enemy enemies[MAX_ENEMIES];

// Ray depth buffer for sprite occlusion
static float depth_buffer[NUM_RAYS];

// Flow Field Pathfinding buffers
static uint8_t flow_dist[BSZ];
static uint8_t queue_x[BSZ];
static uint8_t queue_y[BSZ];

static const int DIR_X[4] = {1, -1, 0, 0};
static const int DIR_Y[4] = {0, 0, 1, -1};

static const float STEER_ANGLES[9] = {
  0.0f, 0.52359877f, -0.52359877f, 1.04719755f, -1.04719755f,
  1.57079632f, -1.57079632f, 2.0943951f, -2.0943951f
};

// Clipped drawing helpers (holes for radar and crosshair)
static inline void draw_rect(int x, int y, int w, int h, eadk_color_t c) {
  if (w > 0 && h > 0) {
    eadk_display_push_rect_uniform((eadk_rect_t){(uint16_t)x, (uint16_t)y, (uint16_t)w, (uint16_t)h}, c);
  }
}

static void draw_with_hole(int x, int y, int w, int h, int hx, int hy, int hw, int hh, eadk_color_t c,
                           void (*next_fn)(int, int, int, int, eadk_color_t)) {
  if (w <= 0 || h <= 0) return;
  if (x >= hx + hw || x + w <= hx || y >= hy + hh || y + h <= hy) {
    next_fn(x, y, w, h, c);
    return;
  }
  if (y < hy) {
    next_fn(x, y, w, hy - y, c);
  }
  if (y + h > hy + hh) {
    next_fn(x, hy + hh, w, y + h - (hy + hh), c);
  }
  int my0 = (y > hy) ? y : hy;
  int my1 = ((y + h) < (hy + hh)) ? (y + h) : (hy + hh);
  if (my1 > my0) {
    if (x < hx) {
      next_fn(x, my0, hx - x, my1 - my0, c);
    }
    if (x + w > hx + hw) {
      int lx = (x > (hx + hw)) ? x : (hx + hw);
      next_fn(lx, my0, x + w - lx, my1 - my0, c);
    }
  }
}

static void clip_radar(int x, int y, int w, int h, eadk_color_t c) {
  draw_with_hole(x, y, w, h, RX0, RY0, RSZ, RSZ, c, draw_rect);
}

static void clip_all(int x, int y, int w, int h, eadk_color_t c) {
  draw_with_hole(x, y, w, h, CX0, CY0, CSZ, CSZ, c, clip_radar);
}

// Raycasting DDA Engine
static inline bool is_free(float x, float y) {
  return wall_at((int)x, (int)y) == 0;
}

static void cast_and_draw() {
  float cos_p = cosf(pa);
  float sin_p = sinf(pa);

  for (int r = 0; r < NUM_RAYS; r++) {
    float ray_offset = -HALF_FOV + FOV * (float)r / (float)NUM_RAYS;
    float cos_o = cosf(ray_offset);
    float sin_o = sinf(ray_offset);
    float ca = cos_p * cos_o - sin_p * sin_o;
    float sa = sin_p * cos_o + cos_p * sin_o;

    if (fabsf(sa) < 1e-6f) sa = 1e-6f;
    if (fabsf(ca) < 1e-6f) ca = 1e-6f;

    int map_x = (int)px;
    int map_y = (int)py;
    float delta_x = fabsf(1.0f / ca);
    float delta_y = fabsf(1.0f / sa);
    int step_x, step_y;
    float side_x, side_y;

    if (ca > 0.0f) {
      step_x = 1;
      side_x = ((float)map_x + 1.0f - px) * delta_x;
    } else {
      step_x = -1;
      side_x = (px - (float)map_x) * delta_x;
    }
    if (sa > 0.0f) {
      step_y = 1;
      side_y = ((float)map_y + 1.0f - py) * delta_y;
    } else {
      step_y = -1;
      side_y = (py - (float)map_y) * delta_y;
    }

    int hit = 0;
    int side = 0;
    for (int s = 0; s < ROWS + COLS + 8; s++) {
      if (side_x < side_y) {
        side_x += delta_x;
        map_x += step_x;
        side = 0;
      } else {
        side_y += delta_y;
        map_y += step_y;
        side = 1;
      }
      hit = wall_at(map_x, map_y);
      if (hit) break;
    }

    int x = r * COL_W;
    if (!hit) {
      clip_all(x, HUD_H, COL_W, SH / 2 - HUD_H, COLOR_CEIL);
      clip_all(x, SH / 2, COL_W, SH - SH / 2, COLOR_FLOOR);
      depth_buffer[r] = 999.0f;
      continue;
    }

    float depth;
    if (side == 0) {
      depth = ((float)map_x - px + (1.0f - (float)step_x) / 2.0f) / ca;
    } else {
      depth = ((float)map_y - py + (1.0f - (float)step_y) / 2.0f) / sa;
    }
    depth *= cos_o;
    if (depth < 0.05f) depth = 0.05f;
    depth_buffer[r] = depth;

    float proj_h = PROJ_DIST / depth;
    if (proj_h > SH * 3) proj_h = (float)(SH * 3);

    int wall_top = (int)(SH / 2.0f - proj_h / 2.0f);
    int wall_h = (int)proj_h;

    if (wall_top < HUD_H) {
      wall_h -= (HUD_H - wall_top);
      wall_top = HUD_H;
    }
    if (wall_top + wall_h > SH) {
      wall_h = SH - wall_top;
    }
    if (wall_h < 0) wall_h = 0;

    eadk_color_t color = get_wall_color(hit);
    int wall_bottom = wall_top + wall_h;

    if (wall_top > HUD_H) {
      clip_all(x, HUD_H, COL_W, wall_top - HUD_H, COLOR_CEIL);
    }
    if (wall_h > 0) {
      clip_all(x, wall_top, COL_W, wall_h, color);
    }
    if (wall_bottom < SH) {
      clip_all(x, wall_bottom, COL_W, SH - wall_bottom, COLOR_FLOOR);
    }
  }
}

// Flow Field Pathfinding
static void update_flow_field() {
  memset(flow_dist, 255, sizeof(flow_dist));
  int cpx = (int)px;
  int cpy = (int)py;
  if (cpx < 0 || cpx >= COLS || cpy < 0 || cpy >= ROWS) return;

  flow_dist[cpy * COLS + cpx] = 0;
  queue_x[0] = (uint8_t)cpx;
  queue_y[0] = (uint8_t)cpy;
  int qi = 0;
  int qlen = 1;

  while (qi < qlen) {
    int cx = queue_x[qi];
    int cy = queue_y[qi];
    int cur = cy * COLS + cx;
    qi++;

    for (int d = 0; d < 4; d++) {
      int nx = cx + DIR_X[d];
      int ny = cy + DIR_Y[d];
      if (nx < 0 || nx >= COLS || ny < 0 || ny >= ROWS) continue;
      int nidx = ny * COLS + nx;
      if (MAP_STR[nidx] != '0') continue;
      if (flow_dist[nidx] == 255) {
        flow_dist[nidx] = flow_dist[cur] + 1;
        queue_x[qlen] = (uint8_t)nx;
        queue_y[qlen] = (uint8_t)ny;
        qlen++;
      }
    }
  }
}

static bool has_clear_path(float x0, float y0, float x1, float y1) {
  float dx = x1 - x0;
  float dy = y1 - y0;
  float dist = sqrtf(dx * dx + dy * dy);
  if (dist < 1e-4f) return true;

  float angle = atan2f(dy, dx);
  float ca = cosf(angle);
  float sa = sinf(angle);
  if (fabsf(sa) < 1e-6f) sa = 1e-6f;
  if (fabsf(ca) < 1e-6f) ca = 1e-6f;

  int map_x = (int)x0;
  int map_y = (int)y0;
  float delta_x = fabsf(1.0f / ca);
  float delta_y = fabsf(1.0f / sa);
  int step_x = (ca > 0.0f) ? 1 : -1;
  int step_y = (sa > 0.0f) ? 1 : -1;
  float side_x = (ca > 0.0f) ? (((float)map_x + 1.0f - x0) * delta_x) : ((x0 - (float)map_x) * delta_x);
  float side_y = (sa > 0.0f) ? (((float)map_y + 1.0f - y0) * delta_y) : ((y0 - (float)map_y) * delta_y);

  for (int s = 0; s < ROWS + COLS + 8; s++) {
    int side;
    if (side_x < side_y) {
      side_x += delta_x;
      map_x += step_x;
      side = 0;
    } else {
      side_y += delta_y;
      map_y += step_y;
      side = 1;
    }
    if (wall_at(map_x, map_y)) {
      float d = (side == 0) ? (((float)map_x - x0 + (1.0f - (float)step_x) / 2.0f) / ca)
                            : (((float)map_y - y0 + (1.0f - (float)step_y) / 2.0f) / sa);
      return d >= dist;
    }
  }
  return true;
}

static void spawn_enemy() {
  for (int try = 0; try < 20; try++) {
    int cx = eadk_random() % COLS;
    int cy = eadk_random() % ROWS;
    if (MAP_STR[cy * COLS + cx] != '0') continue;

    float sx = (float)cx + 0.5f;
    float sy = (float)cy + 0.5f;
    float d2 = (sx - px) * (sx - px) + (sy - py) * (sy - py);
    if (d2 < SPAWN_MIN_DIST * SPAWN_MIN_DIST) continue;
    if (has_clear_path(px, py, sx, sy)) continue;

    for (int i = 0; i < MAX_ENEMIES; i++) {
      if (!enemies[i].alive) {
        enemies[i].x = sx;
        enemies[i].y = sy;
        enemies[i].alive = true;
        return;
      }
    }
  }
}

static void start_wave() {
  wave_remaining = 5 + (wave - 1) * 2;
  if (wave_remaining > 16) wave_remaining = 16;
  spawn_cd = 0.0f;
  score_mult = 1 << (wave / 3);
  wave_banner_time = 1.5f;
}

static void update_enemies(float dt) {
  path_timer -= dt;
  if (path_timer <= 0.0f) {
    path_timer = 1.2f;
    update_flow_field();
  }

  for (int i = 0; i < MAX_ENEMIES; i++) {
    if (!enemies[i].alive) continue;
    float ex = enemies[i].x;
    float ey = enemies[i].y;
    float dx = px - ex;
    float dy = py - ey;
    float dist = sqrtf(dx * dx + dy * dy);

    if (dist <= ENEMY_TOUCH_RANGE) {
      if (player_invuln <= 0.0f) {
        player_health -= ENEMY_DAMAGE;
        player_invuln = 0.5f;
      }
      enemies[i].alive = false;
      continue;
    }

    int bd = 255;
    float tdx = dx;
    float tdy = dy;
    int cx = (int)ex;
    int cy = (int)ey;

    for (int d = 0; d < 4; d++) {
      int nx = cx + DIR_X[d];
      int ny = cy + DIR_Y[d];
      if (nx >= 0 && nx < COLS && ny >= 0 && ny < ROWS) {
        int v = flow_dist[ny * COLS + nx];
        if (v < bd) {
          bd = v;
          tdx = (float)nx + 0.5f - ex;
          tdy = (float)ny + 0.5f - ey;
        }
      }
    }

    float step = ENEMY_SPEED * dt;
    float base_angle = atan2f(tdy, tdx);
    bool moved = false;

    for (int s = 0; s < 9; s++) {
      float ang = base_angle + STEER_ANGLES[s];
      float nx = ex + cosf(ang) * step;
      float ny = ey + sinf(ang) * step;
      if (is_free(nx, ny)) {
        enemies[i].x = nx;
        enemies[i].y = ny;
        moved = true;
        break;
      }
    }
    if (!moved && dist > 0.001f) {
      if (is_free(ex + (dx / dist) * step, ey)) enemies[i].x += (dx / dist) * step;
      if (is_free(ex, ey + (dy / dist) * step)) enemies[i].y += (dy / dist) * step;
    }
  }

  if (wave_remaining > 0) {
    int alive_count = 0;
    for (int i = 0; i < MAX_ENEMIES; i++) {
      if (enemies[i].alive) alive_count++;
    }
    if (alive_count < MAX_ENEMIES) {
      spawn_cd -= dt;
      if (spawn_cd <= 0.0f) {
        spawn_cd = 0.5f;
        spawn_enemy();
        wave_remaining--;
      }
    }
  } else {
    bool any_alive = false;
    for (int i = 0; i < MAX_ENEMIES; i++) {
      if (enemies[i].alive) { any_alive = true; break; }
    }
    if (!any_alive) {
      wave++;
      start_wave();
    }
  }
}

static void try_shoot() {
  muzzle_flash = 0.12f;
  int best_i = -1;
  float best_dist = 11.0f;

  for (int i = 0; i < MAX_ENEMIES; i++) {
    if (!enemies[i].alive) continue;
    float dx = enemies[i].x - px;
    float dy = enemies[i].y - py;
    float d = sqrtf(dx * dx + dy * dy);
    if (d < 1e-4f || d > 10.0f) continue;

    float at = atan2f(dy, dx) - pa;
    while (at > 3.14159265f) at -= 2.0f * 3.14159265f;
    while (at < -3.14159265f) at += 2.0f * 3.14159265f;

    if (fabsf(at) > 0.087266f) continue; // ~5 deg FOV
    if (d < best_dist) {
      best_dist = d;
      best_i = i;
    }
  }

  if (best_i >= 0) {
    if (has_clear_path(px, py, enemies[best_i].x, enemies[best_i].y)) {
      float dx = enemies[best_i].x - px;
      float dy = enemies[best_i].y - py;
      float at = atan2f(dy, dx) - pa;
      while (at > 3.14159265f) at -= 2.0f * 3.14159265f;
      while (at < -3.14159265f) at += 2.0f * 3.14159265f;

      hit_flash_x = (float)(SW / 2) + tanf(at) * PROJ_DIST;
      hit_flash_time = 0.15f;
      score += score_mult;
      enemies[best_i].alive = false;
    }
  }
}

// Enemy Sprite Rendering
static void draw_enemies() {
  float vis_depth[MAX_ENEMIES];
  int vis_idx[MAX_ENEMIES];
  int vc = 0;

  for (int i = 0; i < MAX_ENEMIES; i++) {
    if (!enemies[i].alive) continue;
    float dx = enemies[i].x - px;
    float dy = enemies[i].y - py;
    float d = sqrtf(dx * dx + dy * dy);
    if (d < 0.2f) continue;

    float at = atan2f(dy, dx) - pa;
    while (at > 3.14159265f) at -= 2.0f * 3.14159265f;
    while (at < -3.14159265f) at += 2.0f * 3.14159265f;

    if (fabsf(at) > HALF_FOV) continue;
    float depth = d * cosf(at);
    if (depth < 0.1f) continue;

    vis_depth[vc] = depth;
    vis_idx[vc] = i;
    vc++;
  }

  // Sort by depth (farthest first)
  for (int i = 1; i < vc; i++) {
    float d = vis_depth[i];
    int ix = vis_idx[i];
    int j = i - 1;
    while (j >= 0 && vis_depth[j] < d) {
      vis_depth[j + 1] = vis_depth[j];
      vis_idx[j + 1] = vis_idx[j];
      j--;
    }
    vis_depth[j + 1] = d;
    vis_idx[j + 1] = ix;
  }

  for (int i = 0; i < vc; i++) {
    int ix = vis_idx[i];
    float dx = enemies[ix].x - px;
    float dy = enemies[ix].y - py;
    float at = atan2f(dy, dx) - pa;
    while (at > 3.14159265f) at -= 2.0f * 3.14159265f;
    while (at < -3.14159265f) at += 2.0f * 3.14159265f;

    float sx = (float)(SW / 2) + tanf(at) * PROJ_DIST;
    float depth = vis_depth[i];
    float sz = PROJ_DIST * 0.5f / depth;
    int col = (int)(sx / (float)COL_W);

    if (col < 0 || col >= NUM_RAYS) continue;
    if (depth > depth_buffer[col] - 0.05f) continue;

    int s = (int)sz;
    if (s < 2) s = 2;
    int left = (int)(sx - (float)s / 2.0f);
    int top = (int)((float)(SH / 2) - (float)s / 2.0f);

    if (left < -s || left > SW || top < -s || top > SH) continue;

    clip_all(left, top, s, s, COLOR_ENEMY_OUT);
    int ins = s / 6;
    if (ins < 1) ins = 1;
    if (ins > (s - 1) / 2) ins = (s - 1) / 2;
    int inn = s - ins * 2;
    clip_all(left + ins, top + ins, inn, inn, COLOR_ENEMY);
  }
}

// UI Drawing
static void draw_hud() {
  draw_rect(0, 0, SW, HUD_H, COLOR_HUD_BG);

  char buf[32];
  if (wave_banner_time > 0.0f) {
    snprintf(buf, sizeof(buf), "Wave %d", wave);
    eadk_display_draw_string(buf, (eadk_point_t){6, 2}, true, COLOR_WAVE_TEXT, COLOR_HUD_BG);
  } else {
    if (score_mult > 1) {
      snprintf(buf, sizeof(buf), "Score %d (x%d)", score, score_mult);
    } else {
      snprintf(buf, sizeof(buf), "Score %d", score);
    }
    eadk_display_draw_string(buf, (eadk_point_t){6, 2}, true, COLOR_HUD_TEXT, COLOR_HUD_BG);
  }

  // Health bar
  int bar_w = 80;
  int bar_h = 10;
  int bar_x = SW - bar_w - 8;
  int bar_y = (HUD_H - bar_h) / 2;
  draw_rect(bar_x, bar_y, bar_w, bar_h, COLOR_HEALTH_BG);

  float frac = (float)player_health / 100.0f;
  if (frac < 0.0f) frac = 0.0f;
  int fill_w = (int)((float)bar_w * frac);
  if (fill_w > 0) {
    eadk_color_t c = (frac > 0.3f) ? COLOR_HEALTH_FG : COLOR_HEALTH_LOW;
    draw_rect(bar_x, bar_y, fill_w, bar_h, c);
  }

  // Crosshair
  draw_rect(CX0, CY0, CSZ, CSZ, COLOR_RETICLE_BG);
  int cx = SW / 2;
  int cy = SH / 2;
  eadk_color_t cc = (muzzle_flash > 0.0f) ? COLOR_MUZZLE : COLOR_CROSSHAIR;
  draw_rect(cx - 1, cy - 7, 2, 4, cc);
  draw_rect(cx - 1, cy + 3, 2, 4, cc);
  draw_rect(cx - 7, cy - 1, 4, 2, cc);
  draw_rect(cx + 3, cy - 1, 4, 2, cc);
}

static void draw_radar() {
  int ccx = RX0 + RSZ / 2;
  int ccy = RY0 + RSZ / 2;
  int hl = RADAR_CELLS / 2;
  int cpx = (int)px;
  int cpy = (int)py;

  for (int row = -hl - 1; row <= hl + 1; row++) {
    int my = cpy + row;
    for (int col = -hl - 1; col <= hl + 1; col++) {
      int mx = cpx + col;
      eadk_color_t c = (mx >= 0 && mx < COLS && my >= 0 && my < ROWS && MAP_STR[my * COLS + mx] != '0')
                           ? COLOR_RADAR_WALL : COLOR_RADAR_BG;
      int pxv = ccx + (int)(((float)mx - px) * (float)RADAR_PX);
      int pyv = ccy + (int)(((float)my - py) * (float)RADAR_PX);
      int x0 = (pxv > RX0) ? pxv : RX0;
      int y0 = (pyv > RY0) ? pyv : RY0;
      int x1 = ((pxv + RADAR_PX) < RX1) ? (pxv + RADAR_PX) : RX1;
      int y1 = ((pyv + RADAR_PX) < RY1) ? (pyv + RADAR_PX) : RY1;
      if (x1 > x0 && y1 > y0) {
        draw_rect(x0, y0, x1 - x0, y1 - y0, c);
      }
    }
  }

  // Radar Enemies
  float hs = (float)RSZ / 2.0f;
  for (int i = 0; i < MAX_ENEMIES; i++) {
    if (!enemies[i].alive) continue;
    float rx = (enemies[i].x - px) * (float)RADAR_PX;
    float ry = (enemies[i].y - py) * (float)RADAR_PX;
    if (rx >= -hs && rx <= hs && ry >= -hs && ry <= hs) {
      draw_rect(ccx + (int)rx - 1, ccy + (int)ry - 1, 3, 3, COLOR_RADAR_ENMY);
    }
  }

  // Radar Player & Border
  draw_rect(ccx - 2, ccy - 2, 4, 4, COLOR_RADAR_PLYR);
  draw_rect(RX0, RY0, RSZ, 1, COLOR_RADAR_BORD);
  draw_rect(RX0, RY1 - 1, RSZ, 1, COLOR_RADAR_BORD);
  draw_rect(RX0, RY0, 1, RSZ, COLOR_RADAR_BORD);
  draw_rect(RX1 - 1, RY0, 1, RSZ, COLOR_RADAR_BORD);
}

static void draw_hit_marker() {
  if (hit_flash_time <= 0.0f) return;
  int sx = (int)hit_flash_x;
  int ty = SH / 2;
  int gx = SW / 2;
  int gy = SH - 4;

  for (int s = 1; s < 5; s++) {
    float t = (float)s / 5.0f;
    int px_v = (int)((float)gx + ((float)sx - (float)gx) * t);
    int py_v = (int)((float)gy + ((float)ty - (float)gy) * t);
    draw_rect(px_v - 1, py_v - 1, 3, 3, COLOR_HIT_FLASH);
  }
  draw_rect(sx - 5, ty - 1, 11, 2, COLOR_HIT_FLASH);
  draw_rect(sx - 1, ty - 5, 2, 11, COLOR_HIT_FLASH);
}

// Title Screen
static const int TITLE_RECTS[] = {
  75,40,5,40,  90,40,5,40,  80,40,10,10,
  105,40,5,40, 120,40,5,40, 105,40,20,5, 105,55,20,5,
  135,40,20,5, 142,40,6,40,
  165,40,20,5, 172,40,6,40, 165,75,20,5,
  195,40,5,40, 195,40,20,5, 195,57,15,5, 195,75,20,5,
  225,40,20,5, 225,40,5,20, 225,57,20,5, 240,60,5,20, 225,75,20,5
};

static void show_intro() {
  draw_rect(0, 0, SW, SH, RGB(12, 12, 22));

  // Big Red Block Letters "MATIES"
  for (size_t i = 0; i < sizeof(TITLE_RECTS) / sizeof(TITLE_RECTS[0]); i += 4) {
    draw_rect(TITLE_RECTS[i], TITLE_RECTS[i+1], TITLE_RECTS[i+2], TITLE_RECTS[i+3], RGB(230, 40, 40));
  }

  eadk_display_draw_string("by legendary noobs gaming, 2026", (eadk_point_t){28, 105}, false, RGB(160, 160, 160), RGB(12, 12, 22));
  eadk_display_draw_string("Press OK to Start", (eadk_point_t){95, 145}, false, COLOR_WHITE, RGB(12, 12, 22));
  eadk_display_draw_string("Press BACK to Exit", (eadk_point_t){90, 175}, false, RGB(160, 160, 160), RGB(12, 12, 22));

  // Wait for key release
  while (true) {
    eadk_keyboard_state_t k = eadk_keyboard_scan();
    if (!eadk_keyboard_key_down(k, eadk_key_ok) && !eadk_keyboard_key_down(k, eadk_key_back)) break;
    eadk_timing_msleep(20);
  }
  // Wait for key press
  while (true) {
    eadk_keyboard_state_t k = eadk_keyboard_scan();
    if (eadk_keyboard_key_down(k, eadk_key_ok)) break;
    if (eadk_keyboard_key_down(k, eadk_key_back)) return;
    eadk_timing_msleep(20);
  }
}

static void show_game_over() {
  draw_rect(0, 0, SW, SH, RGB(22, 8, 8));
  eadk_display_draw_string("Game Over", (eadk_point_t){110, 60}, true, RGB(240, 60, 60), RGB(22, 8, 8));

  char buf[32];
  snprintf(buf, sizeof(buf), "Final Score: %d", score);
  eadk_display_draw_string(buf, (eadk_point_t){90, 115}, false, COLOR_WHITE, RGB(22, 8, 8));

  if (score > high_score) high_score = score;
  snprintf(buf, sizeof(buf), "High Score:  %d", high_score);
  eadk_display_draw_string(buf, (eadk_point_t){90, 135}, false, COLOR_WAVE_TEXT, RGB(22, 8, 8));

  eadk_display_draw_string("Press OK to Play Again", (eadk_point_t){75, 180}, false, RGB(180, 180, 180), RGB(22, 8, 8));

  while (true) {
    eadk_keyboard_state_t k = eadk_keyboard_scan();
    if (!eadk_keyboard_key_down(k, eadk_key_ok) && !eadk_keyboard_key_down(k, eadk_key_back)) break;
    eadk_timing_msleep(20);
  }
  while (true) {
    eadk_keyboard_state_t k = eadk_keyboard_scan();
    if (eadk_keyboard_key_down(k, eadk_key_ok)) break;
    if (eadk_keyboard_key_down(k, eadk_key_back)) return;
    eadk_timing_msleep(20);
  }
}

static void reset_game() {
  px = 1.5f;
  py = 5.5f;
  pa = 0.0f;
  av = 0.0f;
  score = 0;
  player_health = 100;
  player_invuln = 0.0f;
  muzzle_flash = 0.0f;
  hit_flash_time = 0.0f;
  wave = 1;
  path_timer = 0.0f;
  for (int i = 0; i < MAX_ENEMIES; i++) enemies[i].alive = false;
  start_wave();
}

int main(int argc, char * argv[]) {
  show_intro();

  while (true) {
    reset_game();
    uint64_t last_time = eadk_timing_millis();
    bool prev_ok = false;

    while (true) {
      uint64_t now = eadk_timing_millis();
      float dt = (float)(now - last_time) / 1000.0f;
      last_time = now;
      if (dt <= 0.0f || dt > 0.1f) dt = 0.016f; // ~60 fps default

      eadk_keyboard_state_t kbd = eadk_keyboard_scan();
      if (eadk_keyboard_key_down(kbd, eadk_key_back) || eadk_keyboard_key_down(kbd, eadk_key_backspace)) {
        return 0; // Exit cleanly to home screen
      }

      // Movement Input
      float turn = 0.0f;
      if (eadk_keyboard_key_down(kbd, eadk_key_left)) turn -= 1.0f;
      if (eadk_keyboard_key_down(kbd, eadk_key_right)) turn += 1.0f;
      float target_v = turn * ROT_SPEED;
      if (av < target_v) {
        av += ROT_ACCEL * dt;
        if (av > target_v) av = target_v;
      } else if (av > target_v) {
        av -= ROT_ACCEL * dt;
        if (av < target_v) av = target_v;
      }
      pa += av * dt;
      while (pa > 6.2831853f) pa -= 6.2831853f;
      while (pa < 0.0f) pa += 6.2831853f;

      float dx = 0.0f;
      float dy = 0.0f;
      if (eadk_keyboard_key_down(kbd, eadk_key_up)) {
        dx += cosf(pa) * MOVE_SPEED * dt;
        dy += sinf(pa) * MOVE_SPEED * dt;
      }
      if (eadk_keyboard_key_down(kbd, eadk_key_down)) {
        dx -= cosf(pa) * MOVE_SPEED * dt;
        dy -= sinf(pa) * MOVE_SPEED * dt;
      }
      if (is_free(px + dx, py)) px += dx;
      if (is_free(px, py + dy)) py += dy;

      // Shooting Input
      bool ok = eadk_keyboard_key_down(kbd, eadk_key_ok);
      if (ok && !prev_ok) {
        try_shoot();
      }
      prev_ok = ok;

      // Enemy Updates
      update_enemies(dt);

      // Timers
      if (muzzle_flash > 0.0f) {
        muzzle_flash -= dt;
        if (muzzle_flash < 0.0f) muzzle_flash = 0.0f;
      }
      if (player_invuln > 0.0f) {
        player_invuln -= dt;
        if (player_invuln < 0.0f) player_invuln = 0.0f;
      }
      if (hit_flash_time > 0.0f) hit_flash_time -= dt;
      if (wave_banner_time > 0.0f) wave_banner_time -= dt;

      // 60 FPS V-Blank Synchronization
      eadk_display_wait_for_vblank();

      // Render Scene
      cast_and_draw();
      draw_enemies();
      draw_hit_marker();
      draw_hud();
      draw_radar();

      // Check Game Over
      if (player_health <= 0) {
        show_game_over();
        break;
      }
    }
  }
}
