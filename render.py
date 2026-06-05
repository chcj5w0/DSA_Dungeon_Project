import pygame
import balance
from frame import Frame


TILE_SIZE = 64

# --- 화면 / HUD 레이아웃 ---
SCREEN_W = 1600
SCREEN_H = 1200
HUD_W    = 320
GAME_W   = SCREEN_W - HUD_W  # 게임 viewport 폭


# HUD 색상
HUD_BG       = ( 20,  20,  30)
HUD_PANEL    = ( 30,  30,  42)
HUD_TEXT     = (235, 235, 235)
HUD_DIM      = (160, 160, 170)
HP_BAR_BG    = ( 70,  20,  20)
HP_BAR_FG    = (220,  60,  60)
UNDO_BAR_BG  = ( 20,  60,  20)
UNDO_BAR_FG  = ( 80, 210, 100)
XP_BAR_BG    = ( 30,  30,  70)
XP_BAR_FG    = (110, 140, 240)

UNDO_MAX = 30  # frame.py의 스택 한도와 일치

# 점수 공식 (단일 출처: balance.py)
SCORE_PER_XP       = balance.SCORE_PER_XP
SCORE_PER_GOLD     = balance.SCORE_PER_GOLD
SCORE_UNDO_PENALTY = balance.SCORE_UNDO_PENALTY
SCORE_TIME_PENALTY = balance.SCORE_TIME_PENALTY
    
TILE_COLORS = {
    0: (100, 100, 120),
    1: ( 40,  40,  60),
    2: (150, 150, 180),
    3: (  0, 200, 100),
    4: (200, 100,   0),
    5: ( 75,  70,  60),  # rubble: 어두운 갈색조
    6: (180, 160,  80),  # hint: 따뜻한 색조
}
PLAYER_COLOR = (100, 180, 255)
ENEMY_COLOR  = (220,  60,  60)
ITEM_COLOR   = (255, 220,  50)

IMAGES = {}
FONTS  = {}


def load_images():
    IMAGES["player"] = pygame.transform.scale(
        pygame.image.load("assets/Player/Player_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["floor"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/floor_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["floor_alt"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/floor_2.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["rubble"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/floor_3.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["hint"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/hint.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    IMAGES["wall"] = pygame.transform.scale(
        pygame.image.load("assets/Tiles/wall_0.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
    for key, fname in (
        ("enemy_melee",  "MeleeEnemy_0.png"),
        ("enemy_ranged", "RangedEnemy_0.png"),
        ("enemy_fast",   "FastEnemy_0.png"),
    ):
        IMAGES[key] = pygame.transform.scale(
            pygame.image.load(f"assets/Enemies/{fname}").convert_alpha(),
            (TILE_SIZE, TILE_SIZE))
    IMAGES["enemy_boss"] = pygame.transform.scale(
        pygame.image.load("assets/Enemies/BossEnemy_0.png").convert_alpha(),
        (TILE_SIZE * 2, TILE_SIZE * 2))


def load_fonts():
    FONTS["small"]  = pygame.font.SysFont(None, 22)
    FONTS["body"]   = pygame.font.SysFont(None, 26)
    FONTS["header"] = pygame.font.SysFont(None, 32)


def _format_time(elapsed_sec):
    m, s = divmod(int(elapsed_sec), 60)
    return f"{m:02d}:{s:02d}"


def _undo_left():
    # 스택에는 현재 프레임도 포함되어 있으므로 되돌릴 수 있는 칸 수는 len-1
    return max(0, len(Frame.frame) - 1)


def compute_score(frame, elapsed_sec):
    kill_xp = frame.get("kill_xp", 0)
    gold    = frame.get("gold", 0)
    return max(0, int(kill_xp * SCORE_PER_XP
                    + gold    * SCORE_PER_GOLD
                    - Frame.undo_count * SCORE_UNDO_PENALTY
                    - elapsed_sec * SCORE_TIME_PENALTY))


# 기존 HUD 코드와의 호환용 별칭
_compute_score = compute_score


def _draw_bar(screen, x, y, w, h, ratio, bg, fg):
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(screen, bg, (x, y, w, h))
    pygame.draw.rect(screen, fg, (x, y, int(w * ratio), h))
    pygame.draw.rect(screen, HUD_DIM, (x, y, w, h), 1)


def _draw_text(screen, text, x, y, font_key="body", color=HUD_TEXT):
    surf = FONTS[font_key].render(text, True, color)
    screen.blit(surf, (x, y))
    return surf.get_height()


def draw_hud(screen, frame, elapsed_sec):
    p = frame["player"]
    m = frame["map"]

    # 패널 배경
    pygame.draw.rect(screen, HUD_BG, (GAME_W, 0, HUD_W, SCREEN_H))
    pygame.draw.line(screen, HUD_DIM, (GAME_W, 0), (GAME_W, SCREEN_H), 2)

    pad_x = GAME_W + 16
    inner_w = HUD_W - 32
    y = 16

    # --- Floor / Time ---
    _draw_text(screen, f"Floor {m.floor}",         pad_x, y, "header"); y += 36
    _draw_text(screen, f"Time  {_format_time(elapsed_sec)}", pad_x, y, "body"); y += 28
    y += 8

    # --- Level / XP ---
    _draw_text(screen, f"Lv {p.lvl}",  pad_x, y, "body"); y += 26
    _draw_text(screen, f"XP {p.exp} / {p.exp_to_next_lvl}", pad_x, y, "small", HUD_DIM); y += 18
    _draw_bar(screen, pad_x, y, inner_w, 8,
              p.exp / p.exp_to_next_lvl if p.exp_to_next_lvl else 0,
              XP_BAR_BG, XP_BAR_FG)
    y += 18

    # --- HP ---
    _draw_text(screen, f"HP {p.health} / {p.max_health}", pad_x, y, "body"); y += 26
    _draw_bar(screen, pad_x, y, inner_w, 18,
              p.health / p.max_health if p.max_health else 0,
              HP_BAR_BG, HP_BAR_FG)
    y += 30

    # --- Stats ---
    _draw_text(screen, f"ATK {p.get_attack_power()}", pad_x, y, "body"); y += 24
    _draw_text(screen, f"DEF {p.defense}",            pad_x, y, "body"); y += 24
    arrows = getattr(p, "arrows", 0)
    _draw_text(screen, f"ARW {arrows}",               pad_x, y, "body"); y += 28

    # --- Undo bar ---
    undo_left = _undo_left()
    _draw_text(screen, f"Undo {undo_left} / {UNDO_MAX - 1}", pad_x, y, "body"); y += 26
    _draw_bar(screen, pad_x, y, inner_w, 14,
              undo_left / (UNDO_MAX - 1) if UNDO_MAX > 1 else 0,
              UNDO_BAR_BG, UNDO_BAR_FG)
    y += 26

    # --- Score ---
    score = _compute_score(frame, elapsed_sec)
    _draw_text(screen, f"Score {score}", pad_x, y, "header"); y += 36

    # --- Inventory ---
    _draw_text(screen, "Inventory", pad_x, y, "body", HUD_DIM); y += 24
    if not p.inventory:
        _draw_text(screen, "(empty)", pad_x + 8, y, "small", HUD_DIM); y += 20
    else:
        for i, it in enumerate(p.inventory):
            if y > SCREEN_H - 24:
                break
            label = f"{(i + 1) % 10}. {it}"
            _draw_text(screen, label, pad_x + 8, y, "small"); y += 20


def draw_game_over(screen, won, score, name, leaderboard_top, name_done):
    """게임 종료 화면. won=True면 승리, False면 패배.
    name: 입력 중인 이름,
    leaderboard_top: [(이름, {"score","cleared","time"}), ...] 정렬된 상위 목록,
    name_done: 이름 입력이 끝났는지(끝나면 조작 안내 표시)."""
    screen.fill((12, 12, 20))

    cx = SCREEN_W // 2

    title = "VICTORY!" if won else "GAME OVER"
    title_color = (110, 220, 130) if won else (220, 80, 80)
    title_surf = FONTS["header"].render(title, True, title_color)
    # header 폰트를 키워서 중앙 상단에 크게
    big = pygame.transform.scale2x(title_surf)
    screen.blit(big, (cx - big.get_width() // 2, 120))

    score_surf = FONTS["header"].render(f"Score : {score}", True, HUD_TEXT)
    screen.blit(score_surf, (cx - score_surf.get_width() // 2, 240))

    # --- 이름 입력 ---
    if not name_done:
        prompt = FONTS["body"].render("Enter your name, then press ENTER:", True, HUD_DIM)
        screen.blit(prompt, (cx - prompt.get_width() // 2, 310))
        caret = name + ("_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " ")
        name_surf = FONTS["header"].render(caret, True, (255, 230, 120))
        screen.blit(name_surf, (cx - name_surf.get_width() // 2, 345))
    else:
        hint = FONTS["body"].render("R : Restart      ESC / Q : Quit", True, HUD_DIM)
        screen.blit(hint, (cx - hint.get_width() // 2, 320))

    # --- 리더보드 TOP ---
    head = FONTS["header"].render("— Leaderboard —", True, HUD_TEXT)
    screen.blit(head, (cx - head.get_width() // 2, 420))

    left = cx - 260  # 표 좌측 기준 x

    # 컬럼 헤더 (클리어 우선 → 점수 → 시간 순으로 정렬됨)
    header_line = f"{'#':>2}  {'NAME':<16} {'RESULT':<7} {'SCORE':>7}  {'TIME':>6}"
    hsurf = FONTS["small"].render(header_line, True, HUD_DIM)
    screen.blit(hsurf, (left, 462))

    y = 488
    for i, (nm, rec) in enumerate(leaderboard_top, 1):
        sc      = rec.get("score", 0)
        cleared = rec.get("cleared", False)
        t       = rec.get("time", 0.0)
        result  = "CLEAR" if cleared else "  —  "
        line = f"{i:>2}  {nm:<16} {result:<7} {sc:>7}  {_format_time(t):>6}"
        # 방금 등록한 본인은 강조, 클리어 기록은 초록빛으로 구분
        if name_done and nm == name:
            color = (255, 230, 120)
        elif cleared:
            color = (130, 220, 150)
        else:
            color = HUD_TEXT
        surf = FONTS["body"].render(line, True, color)
        screen.blit(surf, (left, y))
        y += 32


def render(screen, frame, elapsed_sec=0):
    # 이미지는 한 번만 로드한다. 매 프레임 load_images()를 부르면 디스크에서
    # PNG를 다시 읽고 scale까지 해서(초당 수백 회) 큰 병목이 된다.
    # main()이 시작 시 한 번 채우지만, 미채움 상태로 호출돼도 안전하게 1회 로드.
    if not IMAGES:
        load_images()
    screen.fill((0, 0, 0))

    _map    = frame["map"]
    _player = frame["player"]
    enemies = frame["enemies"]
    items   = frame["items"]

    # viewport 계산 (게임 영역 폭만 사용)
    viewport_w = GAME_W // TILE_SIZE
    viewport_h = SCREEN_H // TILE_SIZE
    viewport_x = max(0, min(_map.MAP_W - viewport_w, _player.x - viewport_w // 2))
    viewport_y = max(0, min(_map.MAP_H - viewport_h, _player.y - viewport_h // 2))

    # 맵 타일
    for y in range(viewport_y, viewport_y + viewport_h):
        for x in range(viewport_x, viewport_x + viewport_w):
            tile = _map.get_tile(x, y)
            color = TILE_COLORS.get(tile, (0, 0, 0))
            sx = (x - viewport_x) * TILE_SIZE
            sy = (y - viewport_y) * TILE_SIZE
            if tile == 0:
                # 바닥 바리에이션: 좌표 해시로 floor_0 / floor_alt 안정 선택
                alt = ((x * 73856093) ^ (y * 19349663)) & 0xFF
                img = IMAGES["floor_alt"] if alt < 64 else IMAGES["floor"]
                screen.blit(img, (sx, sy))
            elif tile == 1:
                screen.blit(IMAGES["wall"], (sx, sy))
            elif tile == 5:
                screen.blit(IMAGES["rubble"], (sx, sy))
            elif tile == 6:
                screen.blit(IMAGES["hint"], (sx, sy))
            else:
                pygame.draw.rect(screen, color, (sx, sy, TILE_SIZE, TILE_SIZE))

    # 아이템
    for item in items:
        pygame.draw.rect(screen, ITEM_COLOR,
                         ((item.x - viewport_x) * TILE_SIZE,
                          (item.y - viewport_y) * TILE_SIZE,
                          TILE_SIZE, TILE_SIZE))

    # 적
    for enemy in enemies:
        img = IMAGES.get(enemy.SPRITE_KEY)
        if img is None:
            pygame.draw.rect(screen, ENEMY_COLOR,
                             ((enemy.x - viewport_x) * TILE_SIZE,
                              (enemy.y - viewport_y) * TILE_SIZE,
                              TILE_SIZE * enemy.SIZE, TILE_SIZE * enemy.SIZE))
        else:
            screen.blit(img, ((enemy.x - viewport_x) * TILE_SIZE,
                              (enemy.y - viewport_y) * TILE_SIZE))

    # 플레이어
    screen.blit(IMAGES["player"],
                ((_player.x - viewport_x) * TILE_SIZE,
                 (_player.y - viewport_y) * TILE_SIZE))

    # HUD
    draw_hud(screen, frame, elapsed_sec)
