import kandinsky
import ion
import time
import random

# Screen dimensions
WIDTH = 320
HEIGHT = 222
GRID_SIZE = 10

# Colors
BG_COLOR = kandinsky.color(0, 0, 0)
SNAKE_COLOR = kandinsky.color(0, 255, 0)
FOOD_COLOR = kandinsky.color(255, 0, 0)
TEXT_COLOR = kandinsky.color(255, 255, 255)

def draw_rect(x, y, color):
    kandinsky.fill_rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE, color)

def play():
    kandinsky.fill_rect(0, 0, WIDTH, HEIGHT, BG_COLOR)
    
    snake = [(16, 11), (15, 11), (14, 11)]
    dx = 1
    dy = 0
    score = 0
    
    food = (random.randint(0, (WIDTH//GRID_SIZE)-1), random.randint(0, (HEIGHT//GRID_SIZE)-1))
    
    for s in snake:
        draw_rect(s[0], s[1], SNAKE_COLOR)
    draw_rect(food[0], food[1], FOOD_COLOR)
    
    last_time = time.monotonic()
    
    while True:
        # Input handling
        if ion.keydown(ion.KEY_UP) and dy == 0:
            dx, dy = 0, -1
        elif ion.keydown(ion.KEY_DOWN) and dy == 0:
            dx, dy = 0, 1
        elif ion.keydown(ion.KEY_LEFT) and dx == 0:
            dx, dy = -1, 0
        elif ion.keydown(ion.KEY_RIGHT) and dx == 0:
            dx, dy = 1, 0
        
        # Check if user wants to exit (e.g., BACK or HOME)
        # ion.KEY_BACK is usually available
        if ion.keydown(ion.KEY_BACK):
            break

        current_time = time.monotonic()
        if current_time - last_time > 0.1:
            last_time = current_time
            
            # Move snake
            head = snake[0]
            new_head = (head[0] + dx, head[1] + dy)
            
            # Game over conditions
            if new_head[0] < 0 or new_head[0] >= WIDTH//GRID_SIZE or \
               new_head[1] < 0 or new_head[1] >= HEIGHT//GRID_SIZE or \
               new_head in snake:
                kandinsky.draw_string("GAME OVER - Score: {}".format(score), 60, 100, TEXT_COLOR, BG_COLOR)
                kandinsky.draw_string("Press OK to restart", 70, 120, TEXT_COLOR, BG_COLOR)
                while not ion.keydown(ion.KEY_OK):
                    if ion.keydown(ion.KEY_BACK):
                        return
                    time.sleep(0.05)
                return True # Signal to restart
            
            snake.insert(0, new_head)
            
            # Check food
            if new_head == food:
                score += 1
                while food in snake:
                    food = (random.randint(0, (WIDTH//GRID_SIZE)-1), random.randint(0, (HEIGHT//GRID_SIZE)-1))
                draw_rect(food[0], food[1], FOOD_COLOR)
            else:
                tail = snake.pop()
                draw_rect(tail[0], tail[1], BG_COLOR)
                
            draw_rect(new_head[0], new_head[1], SNAKE_COLOR)
        
        time.sleep(0.01)

while True:
    restart = play()
    if not restart:
        break
