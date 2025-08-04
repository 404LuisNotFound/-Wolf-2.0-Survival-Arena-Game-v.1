#pgzero
import random
import pygame
import math
import os
import sys
import time

start_time = time.time()
player_damage = 10

#iniciador python -m pgzrun main.py

boss_roar_played = False
boss_music_delay = 0

score = 0

game_state = "menu"
current_level = 1

bar_fill_width = 200
bar_fill_height = 24

drops = []

WIDTH = 800
HEIGHT = 600

WORLD_WIDTH = 1600
WORLD_HEIGHT = 1600

PLAYER_SPEED = 3
player = Actor("stand")
player.health = 200
player.max_health = 200
player.pos = WORLD_WIDTH // 2, WORLD_HEIGHT // 2

damage_cooldown = 0
DAMAGE_COOLDOWN_TIME = 1.0  
shotgun_img = None

BULLET_DAMAGE = 10

current_music_part = 1

game_over = False

shop_selected_option = 0

current_level = 1
max_levels = 5
in_shop = False

bullets = []
BULLET_SPEED = 10

shotgun_cooldown = 0
SHOTGUN_COOLDOWN_TIME = 0.5

boss_intro = True
boss_intro_timer = 0
boss_intro_duration = 3

spawn_timer = 0
SPAWN_INTERVAL = 3.0

escape = None

difficulty_timer = 0
DIFFICULTY_INTERVAL = 3.0  
enemy_spawn_count = 10 
enemy_speed_boost = 0
enemy_health_boost = 0
min_spawn_interval = 0.1  

game_timer = 94 
boss_spawned = False
boss = None
escape_open = False
boss_attacks = []
  
particles = []
flashes = []

screen_shake = 0
shake_offset_x = 0
shake_offset_y = 0

is_dashing = False
dash_timer = 0
dash_cooldown = 0
DASH_SPEED = 8
DASH_DURATION = 0.2 
DASH_COOLDOWN_TIME = 1  

camera_x = 0
camera_y = 0

enemies = []
for i in range(20):
    x = random.randint(100, WORLD_WIDTH - 100)
    y = random.randint(100, WORLD_HEIGHT - 100)
    enemy = Actor("enemy")
    enemy.pos = (x, y)
    enemy.health = 30 
    enemy.offset_x = random.randint(-80, 80)
    enemy.offset_y = random.randint(-80, 80)
    enemy.speed = random.uniform(0.8, 1.5)

    enemies.append(enemy)

def update():
    global dash_timer, is_dashing, dash_cooldown, damage_cooldown, spawn_timer, shotgun_cooldown
    global screen_shake, shake_offset_x, shake_offset_y, SPAWN_INTERVAL, difficulty_timer
    global enemy_spawn_count, enemy_speed_boost, enemy_health_boost
    global game_timer, boss_spawned, escape_open, current_music_part
    global boss_roar_played, boss_music_delay
    global boss_intro, boss_intro_timer
    global game_over
    global game_state
    global score

    if game_state != "playing":
        return
    if game_over:
        return

    if boss_spawned and boss_intro:
        global boss_intro_timer
        boss_intro_timer += 1 / 60

        camera_x = boss.x - WIDTH // 2
        camera_y = boss.y - HEIGHT // 2
        camera_x = max(0, min(WORLD_WIDTH - WIDTH, camera_x))
        camera_y = max(0, min(WORLD_HEIGHT - HEIGHT, camera_y))

        if boss_intro_timer >= boss_intro_duration:
            boss_intro = False
        return  

    move_player()
    update_camera()
    update_enemies()

    if keyboard.space and not is_dashing and dash_cooldown <= 0:
        start_dash()

    if is_dashing:
        dash_timer -= 1 / 60
        if dash_timer <= 0:
            is_dashing = False
            dash_cooldown = DASH_COOLDOWN_TIME
    elif dash_cooldown > 0:
        dash_cooldown -= 1 / 60

    if damage_cooldown > 0:
        damage_cooldown -= 1 / 60

    for bullet in bullets:
        bullet["x"] += bullet["dx"] * BULLET_SPEED
        bullet["y"] += bullet["dy"] * BULLET_SPEED

    for bullet in bullets[:]:
        hit = False
        for enemy in enemies[:]:
            dist = math.hypot(bullet["x"] - enemy.x, bullet["y"] - enemy.y)
            if dist < 20:
                enemy.health -= 10
                hit = True

                knockback_dx = enemy.x - bullet["x"]
                knockback_dy = enemy.y - bullet["y"]
                knockback_mag = math.hypot(knockback_dx, knockback_dy)
                if knockback_mag > 0:
                    knockback_dx /= knockback_mag
                    knockback_dy /= knockback_mag
                    enemy.x += knockback_dx * 10
                    enemy.y += knockback_dy * 10
                    enemy._update_pos()

                if enemy.health <= 0:
                    enemies.remove(enemy)
                    score += 100

                break

        if hit and bullet in bullets:
            bullets.remove(bullet)
        elif not (0 <= bullet["x"] <= WORLD_WIDTH) or not (0 <= bullet["y"] <= WORLD_HEIGHT):
            bullets.remove(bullet)

    if shotgun_cooldown > 0:
        shotgun_cooldown -= 1 / 60

    for p in particles[:]:
        p["x"] += p["dx"]
        p["y"] += p["dy"]
        p["life"] -= 1 / 60
        if p["life"] <= 0:
            particles.remove(p)

    for f in flashes[:]:
        f["life"] -= 1 / 60
        if f["life"] <= 0:
            flashes.remove(f)

    spawn_timer -= 1 / 60
    if spawn_timer <= 0:
        if len(enemies) < 300:
            spawn_enemy()
        spawn_timer = SPAWN_INTERVAL

    if screen_shake > 0:
        shake_offset_x = random.randint(-screen_shake, screen_shake)
        shake_offset_y = random.randint(-screen_shake, screen_shake)
        screen_shake -= 1
    else:
        shake_offset_x = 0
        shake_offset_y = 0

    if difficulty_timer >= DIFFICULTY_INTERVAL:
        difficulty_timer = 0
        if SPAWN_INTERVAL > min_spawn_interval:
            SPAWN_INTERVAL = max(SPAWN_INTERVAL - 0.2, min_spawn_interval)

    game_timer -= 1 / 60
    score += 1
    global current_music_part

    if current_music_part == 1 and game_timer <= 120:
        music.stop()
        music.play("music_part2")
        music.set_volume(0.4)
        current_music_part = 2

    elif current_music_part == 2 and game_timer <= 60:
        music.stop()
        music.play("music_part3")
        music.set_volume(0.4)
        current_music_part = 3

    elif current_music_part == 3 and game_timer <= 40:
        global boss_roar_played, boss_music_delay

        if not boss_roar_played:
            music.stop()
            music.set_volume(0.4)
            sounds.boss_roar.play()
            boss_roar_played = True
            boss_music_delay = 1.5

            spawn_final_boss()
            boss_spawned = True
            boss_intro = True
            boss_intro_timer = 0

        elif boss_music_delay > 0:
            boss_music_delay -= 1 / 60

        elif boss_music_delay <= 0 and not boss_intro:
            music.play("music_part4")
            current_music_part = 4

    if game_timer <= 40 and not boss_spawned:
        music.stop()
        spawn_final_boss()
        boss_spawned = True

    if boss_spawned and boss:
        update_boss_logic(boss, player)

    for atk in boss_attacks[:]:
        atk["x"] += atk["dx"]
        atk["y"] += atk["dy"]
        atk["life"] -= 1 / 60
        if atk["life"] <= 0:
            boss_attacks.remove(atk)
        elif math.hypot(atk["x"] - player.x, atk["y"] - player.y) < 25 and not is_dashing:
            player.health -= 20
            boss_attacks.remove(atk)

    if player.health <= 0 and not game_over:
        music.stop()
        game_over = True

def draw_menu():
    screen.fill("black")
    screen.draw.text("WOLF 2.0", center=(WIDTH // 2, HEIGHT // 2 - 100), fontsize=80, color="white")
    screen.draw.text("Presiona ENTER para comenzar", center=(WIDTH // 2, HEIGHT // 2 + 20), fontsize=40, color="gray")

def spawn_final_boss():
    global boss
    boss = Actor("boss")
    boss.pos = (WORLD_WIDTH // 2, 100)
    boss.attack_timer = 2.0
    boss.charging = False
    boss.radial_cooldown = 1
    boss.radial_timer = 0       


def fire_boss_attack_radial(boss):
    num_projectiles = 16
    speed = 5
    for i in range(num_projectiles):
        angle = i * (2 * math.pi / num_projectiles)
        boss_attacks.append({
            "x": boss.x,
            "y": boss.y,
            "dx": math.cos(angle) * speed,
            "dy": math.sin(angle) * speed,
            "life": 3
        })

def update_boss_logic(boss, player):
    boss.attack_timer -= 1 / 60
    if boss.attack_timer <= 0:
        boss.attack_timer = 1.5
        boss.target_x = player.x
        boss.target_y = player.y
        boss.charging = True
           
    if boss.charging:
        dx = boss.target_x - boss.x
        dy = boss.target_y - boss.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            dx /= dist
            dy /= dist
            boss.x += dx * 4
            boss.y += dy * 4
            boss._update_pos()

            boss.radial_timer += 1 / 60
            if boss.radial_timer >= boss.radial_cooldown:
                boss.radial_timer = 0
                fire_boss_attack_radial(boss)

def update_boss_attacks():
    global boss
    boss.attack_timer -= 1 / 60
    if boss.attack_timer <= 0:
        fire_boss_attack()
        boss.attack_timer = 2.0

def fire_boss_attack():
    base_angle = math.atan2(player.y - boss.y, player.x - boss.x)
    speed = 5

    for i in range(8):
        angle = base_angle + i * (math.pi / 4)
        boss_attacks.append({
            "x": boss.x,
            "y": boss.y,
            "dx": math.cos(angle) * speed,
            "dy": math.sin(angle) * speed,
            "life": 5
        })

def spawn_enemy():
    for _ in range(enemy_spawn_count):
        x = random.randint(100, WORLD_WIDTH - 100)
        y = random.randint(100, WORLD_HEIGHT - 100)
        enemy = Actor("enemy")
        enemy.pos = (x, y)
        enemy.health = 30 + enemy_health_boost  
        enemy.offset_x = random.randint(-80, 80)
        enemy.offset_y = random.randint(-80, 80)
        base_speed = random.uniform(0.8, 1.5)
        enemy.speed = base_speed + enemy_speed_boost
        enemies.append(enemy)

def update_enemies():
    global damage_cooldown
    for enemy in enemies:
        target_x = player.x
        target_y = player.y

        dx = target_x - enemy.x
        dy = target_y - enemy.y
        dist = (dx**2 + dy**2) ** 0.5

        if dist > 1:
            dx /= dist
            dy /= dist
            enemy.x += dx * enemy.speed
            enemy.y += dy * enemy.speed
            enemy._update_pos()

        if dist < 30 and damage_cooldown <= 0 and not is_dashing:
            player.health -= 10
            damage_cooldown = DAMAGE_COOLDOWN_TIME

def init():
    global shotgun_img
    shotgun_img = images.shotgun
    music.play("music_part1")
    music.set_volume(0.4)
init()


def draw():
    if current_level > max_levels:
        screen.fill("black")
        screen.draw.text("¡Ganaste el juego!", center=(WIDTH//2, HEIGHT//2), fontsize=60, color="gold")
        return

    draw_health_bar_with_image()

    if game_state == "menu":
        draw_menu()
        return

    screen.fill("black")
    draw_world()
    draw_health_bar_with_image()
    draw_shotgun()

    for bullet in bullets:
        bx = bullet["x"] - camera_x
        by = bullet["y"] - camera_y
        screen.draw.filled_circle((bx, by), 4, "yellow")

    for p in particles:
        px = p["x"] - camera_x
        py = p["y"] - camera_y
        screen.draw.filled_circle((px, py), 2, "orange")

    for f in flashes:
        fx = f["x"] - camera_x
        fy = f["y"] - camera_y
        screen.draw.filled_circle((fx, fy), f["radius"], f["color"])

    if boss:
        screen.blit("boss", (boss.x - camera_x - 40, boss.y - camera_y - 40))

    for atk in boss_attacks:
        screen.draw.filled_circle((atk["x"] - camera_x, atk["y"] - camera_y), 10, "black")
        
    elapsed_time = int(time.time() - start_time)
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    timer_text = f"{minutes:02}:{seconds:02}"
    screen.draw.text(f"Tiempo: {timer_text}", center=(WIDTH//2, 30), fontsize=50, color="white")
    screen.draw.text(f"Puntos: {int(score)}", topright=(WIDTH - 20, 20), fontsize=40, color="white")


    if game_over:
        screen.draw.filled_rect(Rect((0, 0), (WIDTH, HEIGHT)), "black")
        screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2), fontsize=80, color="red")
        screen.draw.text(f"Puntuación total: {int(score)}", center=(WIDTH//2, HEIGHT//2 + 40), fontsize=40, color="white")
        screen.draw.text("Presiona R para reiniciar", center=(WIDTH//2, HEIGHT//2 + 60), fontsize=40, color="white")

def start_dash():
    global is_dashing, dash_timer, dash_dx, dash_dy
    dash_dx, dash_dy = 0, 0
    if keyboard.w:
        dash_dy -= 1
    if keyboard.s:
        dash_dy += 1
    if keyboard.a:
        dash_dx -= 1
    if keyboard.d:
        dash_dx += 1

    if dash_dx != 0 or dash_dy != 0:
        mag = (dash_dx**2 + dash_dy**2) ** 0.5
        dash_dx /= mag
        dash_dy /= mag
        is_dashing = True
        dash_timer = DASH_DURATION

def move_player():
    global player
    dx, dy = 0, 0
    if keyboard.w:
        dy -= PLAYER_SPEED
        player.image = "behind_estatict"
    if keyboard.s:
        dy += PLAYER_SPEED
        player.image = "stand"
    if keyboard.a:
        dx -= PLAYER_SPEED
        player.image = "left_estatict"
    if keyboard.d:
        dx += PLAYER_SPEED
        player.image = "right_estatict"

    if dx != 0 and dy != 0:
        dx *= 0.7071
        dy *= 0.7071

    if is_dashing:
        player.x += dash_dx * DASH_SPEED
        player.y += dash_dy * DASH_SPEED
    else:
        player.x += dx
        player.y += dy

    player.x = max(0, min(WORLD_WIDTH, player.x))
    player.y = max(0, min(WORLD_HEIGHT, player.y))

def update_camera():
    global camera_x, camera_y
    camera_x = player.x - WIDTH // 2 + shake_offset_x
    camera_y = player.y - HEIGHT // 2 + shake_offset_y
    camera_x = max(0, min(WORLD_WIDTH - WIDTH, camera_x))
    camera_y = max(0, min(WORLD_HEIGHT - HEIGHT, camera_y))

def draw_world():
    for x in range(0, WORLD_WIDTH, 100):
        for y in range(0, WORLD_HEIGHT, 100):
            screen.blit("floor", (x - camera_x, y - camera_y))
    
    for enemy in enemies:
        ex = enemy.x - camera_x
        ey = enemy.y - camera_y
        original_image = enemy._orig_surf
        scaled_image = pygame.transform.scale(original_image, (40, 40))
        screen.surface.blit(scaled_image, (ex - 20, ey - 20))

    screen.blit(player.image, (
        player.x - camera_x - player.width // 2,
        player.y - camera_y - player.height // 2
    ))

def draw_health_bar_with_image():
    x, y = 20, 20
    fill_ratio = player.health / player.max_health
    fill_width = max(1, int(bar_fill_width * fill_ratio))
    image_surface = images.bar_fill
    cropped_surface = pygame.Surface((fill_width, bar_fill_height), pygame.SRCALPHA)
    cropped_surface.blit(image_surface, (0, 0), (0, 0, fill_width, bar_fill_height))
    screen.surface.blit(cropped_surface, (x + 10, y + 4))
    screen.blit("bar_frame", (x, y))
    screen.draw.text(
        f"{player.health}/{player.max_health}",
        midtop=(x + 110, y + 35),
        fontsize=22,
        color="white",
        owidth=1.5,
        ocolor="black"
    )

def draw_shotgun():
    px = player.x - camera_x
    py = player.y - camera_y
    mx, my = pygame.mouse.get_pos()

    dx = mx - px
    dy = my - py
    angle = math.degrees(math.atan2(-dy, dx))

    rotated = pygame.transform.rotate(shotgun_img, angle)

    offset_x = math.cos(math.radians(angle)) * 20
    offset_y = -math.sin(math.radians(angle)) * 20

    gun_x = px + offset_x - rotated.get_width() // 2
    gun_y = py + offset_y - rotated.get_height() // 2

    screen.surface.blit(rotated, (gun_x, gun_y))

def reset_game():
    global player, enemies, bullets, boss, game_over, survival_time, score
    global game_timer, boss_spawned, boss_attacks, start_time
    global current_music_part, boss_intro, boss_intro_timer
    global shotgun_cooldown, damage_cooldown, spawn_timer, difficulty_timer
    global enemies, flashes, particles
    global SPAWN_INTERVAL, enemy_spawn_count, enemy_health_boost, enemy_speed_boost

    player.health = player.max_health
    player.pos = [WORLD_WIDTH // 2, WORLD_HEIGHT // 2]
    
    enemies = []
    bullets = []
    boss_attacks = []
    boss = None
    game_over = False
    score = 0
    survival_time = 0

    start_time = time.time()
    game_timer = 94
    boss_spawned = False
    current_music_part = 1
    boss_intro = True
    boss_intro_timer = 0

    SPAWN_INTERVAL = 3.0
    enemy_spawn_count = 10
    enemy_health_boost = 0
    enemy_speed_boost = 0
    spawn_timer = 0
    difficulty_timer = 0

    shotgun_cooldown = 0
    damage_cooldown = 0
    flashes = []
    particles = []

    music.stop()
    music.play("music_part1")
    music.set_volume(0.4)


def on_key_down(key):
    global game_over, shop_selected_option, in_shop, current_level, in_shop
    global game_state, current_level
    global game_state, game_over

    if game_state == "menu":
        if key == keys.RETURN:
            game_state = "playing"
            music.play("music_part1")
        return

    if game_over and key == keys.R:
        reset_game()
        game_sttate = "menu"
  
    if in_shop:
        if key == keys.UP:
            shop_selected_option = (shop_selected_option - 1) % 4
        elif key == keys.DOWN:
            shop_selected_option = (shop_selected_option + 1) % 4
        elif key == keys.RETURN:
            apply_shop_option(shop_selected_option)

def on_enemy_death(enemy):
    if random.random() < 0.3:
        drops.append({"x": enemy["x"], "y": enemy["y"], "type": "heal"})
    elif random.random() < 0.2:
        drops.append({"x": enemy["x"], "y": enemy["y"], "type": "damage"})


def on_mouse_down(button, pos):
    global shotgun_cooldown, screen_shake
    if button != mouse.LEFT or shotgun_cooldown > 0:
        return
    shotgun_cooldown = SHOTGUN_COOLDOWN_TIME
    screen_shake = 5
    sounds.shotgun.play()
 
    mx, my = pygame.mouse.get_pos()
    mx += camera_x
    my += camera_y

    dx = mx - player.x
    dy = my - player.y
    base_angle = math.atan2(dy, dx)

    px = player.x + math.cos(base_angle) * 40
    py = player.y + math.sin(base_angle) * 40

    player.x -= math.cos(base_angle) * 8
    player.y -= math.sin(base_angle) * 8

    flashes.append({
        "x": px + math.cos(base_angle) * 10,
        "y": py + math.sin(base_angle) * 10,
        "radius": random.randint(10, 16),
        "color": "white",
        "life": 0.1
    })

    for i in range(-3, 4):
        spread = math.radians(i * 5)
        angle = base_angle + spread
        bullet = {
            "x": px,
            "y": py,
            "dx": math.cos(angle),
            "dy": math.sin(angle)
        }
        bullets.append(bullet)

    for i in range(8):
        px_offset = random.uniform(-5, 5)
        py_offset = random.uniform(-5, 5)
        particles.append({
            "x": px + px_offset,
            "y": py + py_offset,
            "dx": random.uniform(-1, 1),
            "dy": random.uniform(-1, 1),
            "life": random.uniform(0.3, 0.6)
        })

import pgzrun
pgzrun.go()
