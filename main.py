import pygame
import player
import map
import copy
from render import render, load_images, load_fonts
from frame import Frame

KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_u, pygame.BUTTON_LEFT, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0]

# [DEBUG] 테스트용 키 — 정식 빌드 시 제거
DEBUG_KEYS = [pygame.K_b, pygame.K_t]

## KEY FEATURES:
## TURN-BASED
## UNDOS
## GRID-BASED
## 2D TOP-DOWN VIEW
## SIMPLE COMBAT SYSTEM
## INVENTORY SYSTEM

# [DEBUG] ---------------------------------------------
def _debug_dump(frame):
    p = frame["player"]
    enemies = frame["enemies"]
    print(f"[DEBUG] floor={frame['map'].floor} "
          f"player=({p.x},{p.y}) hp={p.health}/{p.max_health} "
          f"atk={p.get_attack_power()} def={p.defense} "
          f"lvl={p.lvl} exp={p.exp}/{p.exp_to_next_lvl}")
    print(f"[DEBUG] enemies({len(enemies)}):")
    for i, e in enumerate(enemies):
        tiles = e.occupied_tiles()
        print(f"  [{i}] {e.NAME:6} pos=({e.x},{e.y}) size={e.SIZE} "
              f"hp={e.health}/{e.MAX_HEALTH} alive={e.is_alive()} "
              f"tiles={tiles}")

def _debug_teleport_boss(player, enemies, game_map):
    from enemy import BossEnemy
    boss = next((e for e in enemies if isinstance(e, BossEnemy)), None)
    if boss is None:
        print("[DEBUG] 보스 없음 — floor>=BOSS_FLOOR인지 확인")
        return
    # 플레이어 우측에 2×2 들어갈 자리 찾기
    for dx, dy in ((2, 0), (-3, 0), (0, 2), (0, -3), (2, -1), (-3, -1)):
        tlx, tly = player.x + dx, player.y + dy
        if not boss._blocked(tlx, tly, game_map, enemies, player):
            boss.x, boss.y = tlx, tly
            print(f"[DEBUG] 보스 텔레포트 → ({tlx},{tly})")
            return
    print("[DEBUG] 보스 텔레포트 실패 — 주변에 2×2 자리 없음")
# ----------------------------------------------------

def turn_update(key, frame):
    # --- UNDO 기능 ---
    if key == pygame.K_u:
        Frame.undo()
        return

    # [DEBUG] 적 상태 덤프 — 턴 소비 없음
    if key == pygame.K_b:
        _debug_dump(frame)
        return

    new_frame = copy.deepcopy(frame)
    player = new_frame["player"]
    map = new_frame["map"]
    enemies = new_frame["enemies"]
    items = new_frame["items"]

    # [DEBUG] 보스를 플레이어 우측에 텔레포트
    if key == pygame.K_t:
        _debug_teleport_boss(player, enemies, map)
        Frame(new_frame)
        return

    # 행동 전 적 스냅샷 (kill_xp 누적용)
    pre_enemies = {id(e): e.exp_reward for e in enemies if e.is_alive()}
    pre_floor = map.floor

    # --- 플레이어 행동 ---
    if key == pygame.K_w:
        player.move(map, 'up', enemies)
    elif key == pygame.K_s:
        player.move(map, 'down', enemies)
    elif key == pygame.K_a:
        player.move(map, 'left', enemies)
    elif key == pygame.K_d:
        player.move(map, 'right', enemies)
    elif pygame.K_1<=key<=pygame.K_9:
        player.use_item(key - pygame.K_1)
    elif key == pygame.K_0:
        player.use_item(9)
    elif key == pygame.BUTTON_LEFT:
        player.attack(enemies)

    # --- 층 전환 후 enemies/items 동기화 ---
    if map.floor != pre_floor:
        enemies.clear()
        enemies.extend(map.monsters)
        items.clear()

    # --- 적 AI 행동 (플레이어 이동 후) ---
    for enemy in enemies:
        if enemy.is_alive():
            enemy.update(player, map, enemies)

    # --- 아이템 자동 획득 ---
    for item in items[:]:
        if item.x == player.x and item.y == player.y:
            if len(player.inventory) < player.inventory_size:
                player.inventory.append(item)
            items.remove(item)

    # --- 점수 누적: 이번 턴에 사라진(=죽은) 적의 XP를 합산 ---
    # 단, 층 전환 턴은 옛 적이 통째로 사라지므로 누적하지 않음
    if map.floor == pre_floor:
        post_ids = {id(e) for e in enemies if e.is_alive()}
        killed_xp = sum(xp for eid, xp in pre_enemies.items() if eid not in post_ids)
        new_frame["kill_xp"] = new_frame.get("kill_xp", 0) + killed_xp

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
    IMAGES["floor"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/floor_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["wall"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/wall_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    # 적: 16×16 원본 → 64×64 (4배)
    for key, fname in (
        ("enemy_melee",  "MeleeEnemy_0.png"),
        ("enemy_ranged", "RangedEnemy_0.png"),
        ("enemy_fast",   "FastEnemy_0.png"),
    ):
        IMAGES[key] = pygame.transform.scale(
            pygame.image.load(f"assets/Enemies/{fname}").convert_alpha(),
            (TILE_SIZE, TILE_SIZE))
    # 보스: 32×32 원본 → 128×128 (4배, 2×2 타일 점유)
    IMAGES["enemy_boss"] = pygame.transform.scale(
        pygame.image.load("assets/Enemies/BossEnemy_0.png").convert_alpha(),
        (TILE_SIZE * 2, TILE_SIZE * 2))

# --- 게임 시작 --- 

def main():
    pygame.init()

    screen = pygame.display.set_mode((1600, 1200))
    pygame.display.set_caption("DSA Project")
    load_images()
    load_fonts()

    # [DEBUG] 보스 테스트용 — 마지막 층부터 시작. 정식 빌드 시 floor=1로 되돌릴 것
    _map = map.Map(floor=1)
    _player = player.Player(*_map.start)

    f = {"player": _player, "map": _map,
         "enemies": _map.monsters, "items": [],
         "kill_xp": 0, "gold": 0}
    Frame(f)

    start_ticks = pygame.time.get_ticks()

    running = True
    while running:
        curr_frame = Frame.frame[-1]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in KEYS or event.key in DEBUG_KEYS:
                    turn_update(event.key, curr_frame)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                turn_update(event.button, curr_frame)
        elapsed_sec = (pygame.time.get_ticks() - start_ticks) / 1000.0
        render(screen, curr_frame, elapsed_sec)
        pygame.display.update()
    pygame.quit()



if __name__ == "__main__":
    main()
    