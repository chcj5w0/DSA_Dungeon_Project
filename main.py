import pygame
import player
import map
import copy
from frame import Frame

KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_i, pygame.K_u, pygame.BUTTON_LEFT]

## KEY FEATURES:
## TURN-BASED
## UNDOS
## GRID-BASED
## 2D TOP-DOWN VIEW
## SIMPLE COMBAT SYSTEM
## INVENTORY SYSTEM

def turn_update(key, frame):
    # --- UNDO 기능 ---
    if key == pygame.K_u:
        Frame.undo()
        return

    new_frame = copy.deepcopy(frame)
    player = new_frame["player"]
    map = new_frame["map"]
    enemies = new_frame["enemies"]
    items = new_frame["items"]

    # --- 플레이어 행동 ---
    if key == pygame.K_w:
        player.move(map, 'up')
    elif key == pygame.K_s:
        player.move(map, 'down')
    elif key == pygame.K_a:
        player.move(map, 'left')
    elif key == pygame.K_d:
        player.move(map, 'right')
    elif key == pygame.K_i:
        # TODO: 인벤토리 열기
        pass
    elif key == pygame.BUTTON_LEFT:
        player.attack(enemies)

    # --- 적 AI 행동 (플레이어 이동 후) ---
    for _ in enemies:
        # TODO: enemy.act(player, map)
        pass

    # --- 아이템 자동 획득 ---
    for item in items[:]:
        if item.x == player.x and item.y == player.y:
            # TODO: player.inventory.add(item)
            items.remove(item)

    Frame(new_frame)

TILE_SIZE = 64

TILE_COLORS = {
    0: (100, 100, 120),   # 바닥
    1: ( 40,  40,  60),   # 벽
    2: (150, 150, 180),   # 문
    3: (  0, 200, 100),   # 시작
    4: (200, 100,   0),   # 도착
}
PLAYER_COLOR = (100, 180, 255)
ENEMY_COLOR  = (220,  60,  60)
ITEM_COLOR   = (255, 220,  50)

IMAGES = {}  # pygame.init() 후 load_images()로 채움

def load_images():
    IMAGES["player"] = pygame.transform.scale(
        pygame.image.load("assets/Player/Player_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["enemy"] = pygame.transform.scale(
        pygame.image.load("assets/Player/Enemy_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["floor"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/floor_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["wall"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/wall_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))

def render(screen, frame):
    
    screen.fill((0, 0, 0))

    _map    = frame["map"]
    _player = frame["player"]
    enemies = frame["enemies"]
    items   = frame["items"]

    # viewport 계산 (플레이어 중심)
    viewport_w = screen.get_width() // TILE_SIZE
    viewport_h = screen.get_height() // TILE_SIZE
    viewport_x = max(0, min(_map.MAP_W - viewport_w, _player.x - viewport_w // 2))
    viewport_y = max(0, min(_map.MAP_H - viewport_h, _player.y - viewport_h // 2))

    # 맵 타일
    for y in range(viewport_y, viewport_y + viewport_h):
        for x in range(viewport_x, viewport_x + viewport_w):
            tile = _map.get_tile(x, y)
            color = TILE_COLORS.get(tile, (0, 0, 0))
            if tile == 0:
                screen.blit(IMAGES["floor"], ((x - viewport_x) * TILE_SIZE, (y - viewport_y) * TILE_SIZE))
            elif tile == 1:
                screen.blit(IMAGES["wall"], ((x - viewport_x) * TILE_SIZE, (y - viewport_y) * TILE_SIZE))
            else:
                pygame.draw.rect(screen, color,
                             ((x - viewport_x) * TILE_SIZE, (y - viewport_y) * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # 아이템
    for item in items:
        pygame.draw.rect(screen, ITEM_COLOR,
                         ((item.x - viewport_x) * TILE_SIZE, (item.y - viewport_y) * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # 적
    for enemy in enemies:
        screen.blit(IMAGES["enemy"], ((enemy.x - viewport_x) * TILE_SIZE, (enemy.y - viewport_y) * TILE_SIZE))
        #pygame.draw.rect(screen, ENEMY_COLOR,
        #                 ((enemy.x - viewport_x) * TILE_SIZE, (enemy.y - viewport_y) * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # player - mostly the center of the viewport
    screen.blit(IMAGES["player"], ((_player.x - viewport_x) * TILE_SIZE, (_player.y - viewport_y) * TILE_SIZE))
    #pygame.draw.rect(screen, PLAYER_COLOR,
    #                 ((_player.x - viewport_x) * TILE_SIZE, (_player.y - viewport_y) * TILE_SIZE, TILE_SIZE, TILE_SIZE))

# --- 게임 시작 --- 

def main():
    pygame.init()

    screen = pygame.display.set_mode((1600, 1200))
    pygame.display.set_caption("DSA Project")
    load_images()

    _map = map.Map(floor=1)
    _player = player.Player(*_map.start)

    f = {"player": _player, "map": _map, "enemies": _map.monsters, "items": _map.items}
    Frame(f)
    
    
    running = True
    while running:
        curr_frame = Frame.frame[-1]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in KEYS:
                    turn_update(event.key, curr_frame)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                turn_update(event.button, curr_frame)
        render(screen, curr_frame)
        pygame.display.update()
    pygame.quit()



if __name__ == "__main__":
    main()
    