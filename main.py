import pygame
import player
import map
import copy
import balance
from render import render, load_images, load_fonts, draw_game_over, compute_score
from frame import Frame
from enemy import BossEnemy
from leaderboard import leaderboard

KEYS = [
    pygame.K_w,
    pygame.K_a,
    pygame.K_s, 
    pygame.K_d, 
    pygame.K_u, 
    pygame.K_UP,
    pygame.K_DOWN,
    pygame.K_LEFT,
    pygame.K_RIGHT, 
    pygame.K_1, 
    pygame.K_2, 
    pygame.K_3, 
    pygame.K_4, 
    pygame.K_5, 
    pygame.K_6, 
    pygame.K_7, 
    pygame.K_8, 
    pygame.K_9, 
    pygame.K_0,
    ]

## KEY FEATURES:
## TURN-BASED
## UNDOS
## GRID-BASED
## 2D TOP-DOWN VIEW
## SIMPLE COMBAT SYSTEM
## INVENTORY SYSTEM

# 턴 업데이트를 진행하는 함수이다. 현재 모든 캐릭터가 동일 속도이기 때문에, 단순 순회로 충분하다. (플레이어 행동 → 적 행동 → 점수/보스 처치 판정 → 게임 상태 판정)
def turn_update(key, frame):
    # --- UNDO 기능 ---
    if key == pygame.K_u:
        Frame.undo()
        return

    # 맵은 한 층 안에서 불변이라 매 턴 deepcopy하면 순수 낭비다.
    # 모든 프레임이 같은 Map 객체를 공유하고, deepcopy 대상에서만 제외한다.
    # 이 과정에서 시간복잡도가 O(적 수)로 나타난다.
    # 매 턴 바뀌며 undo 스냅샷에 필요한 player/enemies/items만 깊은 복사를 한다.
    shared_map = frame["map"]
    new_frame = copy.deepcopy({k: v for k, v in frame.items() if k != "map"})
    new_frame["map"] = shared_map

    player = new_frame["player"]
    map = shared_map
    enemies = new_frame["enemies"]


    # 행동 전 적 스냅샷 (kill_xp 누적용). 보스 id도 따로 기억해 처치 여부 판정.
    pre_enemies = {id(e): e.exp_reward for e in enemies if e.is_alive()}
    pre_boss_ids = {id(e) for e in enemies
                    if e.is_alive() and isinstance(e, BossEnemy)}
    pre_floor = map.floor

    # --- 플레이어 행동 ---
    if key == pygame.K_w or key == pygame.K_UP:
        player.move(map, 'up', enemies)
    elif key == pygame.K_s or key == pygame.K_DOWN:
        player.move(map, 'down', enemies)
    elif key == pygame.K_a or key == pygame.K_LEFT:
        player.move(map, 'left', enemies)
    elif key == pygame.K_d or key == pygame.K_RIGHT:
        player.move(map, 'right', enemies)
    elif pygame.K_1<=key<=pygame.K_9:
        player.use_item(key - pygame.K_1)
    elif key == pygame.K_0:
        player.use_item(9)
    elif key == pygame.BUTTON_LEFT:
        player.attack(enemies)

    # --- 층 전환 후 enemies 동기화 ---
    if map.floor != pre_floor:
        enemies.clear()
        enemies.extend(map.monsters)

    # --- 적 AI 행동 (플레이어 이동 후) ---
    # 성능: 플레이어와 맨해튼 거리가 AI_ACTIVE_RADIUS 이내인 적만 update하여 AI를 작동시킨다.
    # 멀리 있는 적은 시야 밖이라 행동이 안 보이므로 BFS 비용을 아낀다.
    # 보스는 멀리서도 추적하는 설계라 거리와 무관하게 항상 작동.
    radius = balance.AI_ACTIVE_RADIUS
    for enemy in enemies:
        if not enemy.is_alive():
            continue
        if isinstance(enemy, BossEnemy) or abs(enemy.x - player.x) + abs(enemy.y - player.y) <= radius:
            enemy.update(player, map, enemies)



    # --- 점수 누적 + 보스 처치 추적 ---
    # 단, 층 전환 턴은 옛 적이 통째로 사라지므로 누적하지 않음
    if map.floor == pre_floor:
        # 행동 전 적 스냅샷과 비교해 이번 턴에 사라진 적들의 경험치 합을 kill_xp로 누적한다.
        post_ids = {id(e) for e in enemies if e.is_alive()}
        killed_xp = sum(xp for eid, xp in pre_enemies.items() if eid not in post_ids)
        new_frame["kill_xp"] = new_frame.get("kill_xp", 0) + killed_xp

        # 이번 턴에 사라진 적 중 보스가 있으면 처치 완료(한번 참이면 계속 참)
        if pre_boss_ids - post_ids:
            player.boss_defeated = True

    # --- 게임 상태 판정 ---
    # 승리: player.move가 "보스 처치 후 출구 도달"을 감지해 won 플래그를 세움
    # 패배: 적 AI 행동까지 끝난 뒤 플레이어 HP가 0
    if getattr(player, "won", False):
        new_frame["status"] = "won"
    elif not player.is_alive():
        new_frame["status"] = "dead"
    else:
        new_frame["status"] = "playing"

    # Frame 클래스를 생성하면 자동으로 frame 스택에 쌓인다. 새 프레임을 만들어 업데이트된 상태를 반영한다.
    Frame(new_frame)

    # 층이 바뀐 턴이면, 이전 층 프레임들은 공유 맵이 이미 변형돼 undo 불가.
    # 새 층 프레임만 남기고 undo 스택을 비운다(이 프레임이 새 바닥).
    if map.floor != pre_floor:
        Frame.reset_history()


# 화면 상수·타일색·load_images()는 render.py로 일원화(단일 출처).
# main은 [main.py:6]에서 render의 load_images를 import해 main()에서 호출한다.

# --- 게임 시작 ---

LEADERBOARD_FILE = "leaderboard.json"
MAX_NAME_LEN = 16
LEADERBOARD_TOP_N = 10

# 한 판을 진행하는 함수. 게임 루프를 돌며 이벤트 처리, 턴 업데이트, 렌더링을 담당한다.
# 게임 종료 시 게임 상태와 최종 프레임, 소요 시간을 반환한다.
def run_one_game(screen):
    # 한 판을 끝까지 진행. 종료 시 (status, frame, elapsed_sec) 반환.
    # status는 'won' / 'dead' / 'quit' 중 하나.
    # 새 판: 클래스 변수인 Frame 스택/undo 카운터를 초기화해야 이전 판이 안 섞인다.
    Frame.reset()

    # 맵과 플레이어 초기화, 초기화된 새로운 프레임을 생성한다.
    _map = map.Map(floor=1)
    _player = player.Player(*_map.start)
    f = {"player": _player, "map": _map,
         "enemies": _map.monsters, "items": [],
         "kill_xp": 0, "gold": 0, "status": "playing"}
    Frame(f)

    start_ticks = pygame.time.get_ticks()

    # 게임 루프
    while True:
        curr_frame = Frame.frame[-1]

        # 종료 상태면 한 판 종료
        status = curr_frame.get("status", "playing")
        if status in ("won", "dead"):
            elapsed_sec = (pygame.time.get_ticks() - start_ticks) / 1000.0
            return status, curr_frame, elapsed_sec

        # 키 이벤트 처리: 방향키/WSAD → 이동, 1-0 → 아이템 사용, U → undo, ESC → 종료
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", curr_frame, 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit", curr_frame, 0
                elif event.key in KEYS:
                    turn_update(event.key, curr_frame)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                turn_update(event.button, curr_frame)

        elapsed_sec = (pygame.time.get_ticks() - start_ticks) / 1000.0
        
        # 게임 렌더링
        render(screen, curr_frame, elapsed_sec)
        pygame.display.update()

#--- 게임 종료 후 결과 화면 ---
def game_over_screen(screen, status, frame, elapsed_sec):
    # 결과 화면: 이름 입력 → 리더보드 저장 → TOP 표시 → R/ESC/Q 대기.
    # 'restart' 또는 'quit' 반환.
    
    # 승리여부 및 점수 계산
    won = (status == "won")
    score = compute_score(frame, elapsed_sec)

    # 리더보드 로드 및 이름 입력 준비
    board = leaderboard()
    board.load_leaderboard(LEADERBOARD_FILE)

    name = ""
    name_done = False
    saved_name = ""
    clock = pygame.time.Clock()

    # 게임오버 루프: 이름 입력과 결과 표시를 담당한다. 이름 입력이 끝나면 리더보드 저장 및 TOP N 표시로 넘어간다.
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type != pygame.KEYDOWN:
                continue

            if not name_done:
                # --- 이름 입력 모드 ---
                if event.key == pygame.K_RETURN:
                    saved_name = name.strip() or "Player"
                    # 클리어 여부(won)와 소요 시간(elapsed_sec)도 함께 기록
                    board.add_score(saved_name, score,
                                    cleared=won, time=elapsed_sec)
                    name = saved_name
                    name_done = True
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode and event.unicode.isprintable() \
                        and len(name) < MAX_NAME_LEN:
                    name += event.unicode
            else:
                # --- 저장 후: 재시작 / 종료 ---
                if event.key == pygame.K_r:
                    return "restart"
                elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return "quit"

        top = board.get_leaderboard()[:LEADERBOARD_TOP_N]
        draw_game_over(screen, won, score, name, top, name_done)
        pygame.display.update()
        clock.tick(30)


def main():
    # 게임 초기화: pygame 시작, 화면 설정, 리소스 로드.
    pygame.init()
    screen = pygame.display.set_mode((1600, 1200))
    pygame.display.set_caption("DSA Project")
    load_images()
    load_fonts()

    # 메인 루프: 한 판 진행 → 결과 화면 → 재시작/종료 선택. 게임 종료 시 pygame 종료.
    while True:
        status, frame, elapsed_sec = run_one_game(screen)
        if status == "quit":
            break
        if game_over_screen(screen, status, frame, elapsed_sec) == "quit":
            break

    pygame.quit()


if __name__ == "__main__":
    main()
