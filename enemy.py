# 적(Enemy) AI 모듈.
#
# 적은 두 알고리즘으로 움직인다.
#   - 추적: BFS(`_bfs_next_step`)로 플레이어까지 최단 경로의 '다음 한 칸'을 구한다.
#           격자는 칸 이동 비용이 모두 1인 무가중치 그래프라 BFS가 최단을 보장한다(O(V+E)).
#   - 시야: Bresenham 직선(`_bresenham`)으로 적-플레이어 사이 칸을 훑어 벽이 가로막는지 본다.
# 종류별 `update()`는 "보이면 추격/공격/후퇴, 안 보이면 무작위 배회"의 간단한 상태기계다.

import random
from collections import deque
import balance

# [Bresenham 알고리즘] 정수 연산만을 이용해 두 좌표 사이의 직선 경로를 구하는 알고리즘.
# float 연산이나 삼각함수가 없어 연산 속도가 매우 빠르며, 시야 차단 검사에 최적이다.
# 시간복잡도: O(max(dx, dy))
def _bresenham(x0, y0, x1, y1):
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            return points
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

# 유클리드 거리
def _pythagorean_dist(x0, y0, x1, y1):
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


class Enemy():
    # 모든 적의 공통 베이스. 위치·체력·시야와 BFS 추적/회피 유틸을 제공하고,
    # 구체 행동은 하위 클래스 `update()`가 정의한다. SIZE로 n×n 점유를 지원해
    # 2×2 보스도 같은 코드를 공유한다.

    NAME = "enemy"
    MAX_HEALTH = balance.ENEMY_STATS["Enemy"]["hp"]
    ATTACK = balance.ENEMY_STATS["Enemy"]["atk"]
    XP = balance.ENEMY_STATS["Enemy"]["xp"]
    SIGHT = balance.ENEMY_STATS["Enemy"]["sight"]
    SPRITE_KEY = "enemy"
    DROP_RATE = balance.ENEMY_STATS["Enemy"]["drop"]
    SIZE = 1  # n×n 타일 점유. 좌상단이 (x, y)

    def __init__(self, x, y, lvl=1, exp_reward=None):
        self.x = x
        self.y = y
        # 레벨 보정된 최대 체력을 인스턴스에 저장(후퇴 임계값 계산에 사용).
        self.max_health = balance.scaled_stat(self.MAX_HEALTH, lvl)
        self.health = self.max_health
        self.attack_power = balance.scaled_stat(self.ATTACK, lvl)
        self.exp_reward = (self.XP * lvl * balance.ENEMY_XP_PER_LVL
                           if exp_reward is None else exp_reward)

    # --- 점유 영역 ---

    # 대형 몬스터(Boss, SIZE=2) 대응을 위한 다중 타일 배열 생성 함수.
    # 시간복잡도: O(SIZE^2) - 일반 적은 O(1)이며, 2x2 보스여도 4칸만 계산하므로 상수 시간에 가깝다
    def occupied_tiles(self, x=None, y=None):
        # 좌상단 (x, y) 기준 SIZE×SIZE 점유 좌표 목록. x/y 생략 시 현재 위치.
        x = self.x if x is None else x
        y = self.y if y is None else y
        return [(x + dx, y + dy) for dy in range(self.SIZE) for dx in range(self.SIZE)]

    # 대형 몬스터가 플레이어를 조준할 때, 자신의 덩치 중 플레이어와 가장 인접한 타일을 찾는 헬퍼 함수.
    # 맨해튼 거리를 기준으로 최적의 타일을 계산한다. 시간복잡도: O(SIZE^2)
    def _closest_own_tile(self, tx, ty):
        # 점유 칸 중 (tx, ty)와 맨해튼 거리 최소인 칸.
        best = (self.x, self.y)
        best_d = abs(self.x - tx) + abs(self.y - ty)
        for ox, oy in self.occupied_tiles():
            d = abs(ox - tx) + abs(oy - ty)
            if d < best_d:
                best_d = d
                best = (ox, oy)
        return best

    # --- 상태 ---

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health -= amount

    # --- 인지 ---

    def can_see(self, player, game_map):
        # 2단계 시야 판정.
        # 1) 거리 게이트: 가장 가까운 점유 칸 기준 유클리드 거리가 SIGHT를 넘으면 안 보임.
        ox, oy = self._closest_own_tile(player.x, player.y)
        if _pythagorean_dist(ox, oy, player.x, player.y) > self.SIGHT:
            return False
        
        # 2) 직선 판정: Bresenham으로 둘 사이 칸을 그어, 중간에 벽이 있으면 시야가 막힘.
        line = _bresenham(ox, oy, player.x, player.y)
        for x, y in line[1:-1]:  # 양 끝(자신·플레이어)은 빼고 사이 칸만 검사
            if not game_map.is_walkable(x, y):
                return False # 시야 차단됨
        return True

    # --- 이동 유틸 ---

    # 이동하려는 좌표에 벽이나 플레이어, 타 적군이 존재하는지 검사한다.
    # 대형 보스의 경우 자신이 차지할 전 범위(SIZE*SIZE)를 순회하며 충돌을 검사한다.
    # 시간복잡도: O(SIZE^2 * 적 수)
    def _blocked(self, x, y, game_map, enemies, player):
        # 좌상단 (x, y)에 SIZE×SIZE로 놓일 수 있는지 검사.
        for tx, ty in self.occupied_tiles(x, y):
            if not game_map.is_walkable(tx, ty):
                return True
            if tx == player.x and ty == player.y:
                return True
            for e in enemies:
                if e is self or not e.is_alive():
                    continue
                for ex, ey in e.occupied_tiles():
                    if tx == ex and ty == ey:
                        return True
        return False

    def _bfs_next_step(self, target, game_map, enemies, player):
        # target까지 BFS로 최단 경로를 찾아 '다음 한 칸'만 돌려준다.
        # 무가중치 격자라 BFS가 최단을 보장한다(O(V+E)≈탐색 칸 수). 실제로는 시야 안에서만
        # 호출돼 탐색 범위가 시야 반경으로 제한된다. SIZE>1(보스)이면 목적지 도달만 따로 허용
        start = (self.x, self.y)
        if start == target:
            return None
        parent = {start: None}
        q = deque([start])
        found = False
        while q:
            cx, cy = q.popleft()
            if (cx, cy) == target:
                found = True
                break
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in parent:
                    continue
                # target 칸은 보통 플레이어가 점유해 _blocked이지만, 경로의 '목적지'로는
                # 도달 가능해야 한다. 목적지는 큐에서 꺼내는 즉시 break하므로(통과·확장 안 함)
                # 다른 막힌 칸으로 새어나가지 않는다. 이게 빠져 추적이 멈추던 버그였다.
                if (nx, ny) != target and self._blocked(nx, ny, game_map, enemies, player):
                    continue
                parent[(nx, ny)] = (cx, cy)
                q.append((nx, ny))
        if not found:
            return None
        cur = target
        while parent[cur] != start:
            cur = parent[cur]
        return cur

    def _random_step(self, game_map, enemies, player):
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = self.x + dx, self.y + dy
            if not self._blocked(nx, ny, game_map, enemies, player):
                self.x, self.y = nx, ny
                return

    def _step_toward(self, target, game_map, enemies, player):
        nxt = self._bfs_next_step(target, game_map, enemies, player)
        # 다음 칸이 목적지(플레이어 위치 등 막힌 칸)면 올라서지 않고 멈춘다.
        # 추적 호출 전에 인접 시 공격하므로, 정상 경로에선 nxt가 막힌 칸이 될 일이 없다.
        if nxt is not None and not self._blocked(nxt[0], nxt[1], game_map, enemies, player):
            self.x, self.y = nxt

    # 그리디한 방식으로 플레이어로부터 멀어져 도망친다.
    def _step_away(self, from_xy, game_map, enemies, player):
        fx, fy = from_xy
        ox, oy = self._closest_own_tile(fx, fy)
        best = None
        # 후보 칸과 동일한 척도(맨해튼)로 비교한다. 예전엔 유클리드로 초기화해 척도가 섞였다.
        best_dist = abs(ox - fx) + abs(oy - fy)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = self.x + dx, self.y + dy
            if self._blocked(nx, ny, game_map, enemies, player):
                continue
            # 이동 후 점유 칸 중 가장 가까운 칸의 거리
            cand_best = min(abs(tx - fx) + abs(ty - fy)
                            for tx, ty in self.occupied_tiles(nx, ny))
            if cand_best > best_dist:
                best_dist = cand_best
                best = (nx, ny)
        if best is not None:
            self.x, self.y = best

    # --- 공격 ---

    def _adjacent_to(self, player):
        # 점유 칸 중 하나라도 플레이어와 맨해튼 1이면 인접.
        for tx, ty in self.occupied_tiles():
            if abs(tx - player.x) + abs(ty - player.y) == 1:
                return True
        return False

    def attack(self, player):
        dmg = balance.damage(self.attack_power, player.defense)
        player.take_damage(dmg)

    # --- 턴 인터페이스 ---

    def update(self, player, game_map, enemies):
        raise NotImplementedError


class MeleeEnemy(Enemy):
    # 근접형: 보이면 추격해 인접 시 공격. 체력이 max/RETREAT_HP_DIVISOR 밑이면 후퇴한다.
    NAME = "melee"
    MAX_HEALTH = balance.ENEMY_STATS["Melee"]["hp"]
    ATTACK = balance.ENEMY_STATS["Melee"]["atk"]
    XP = balance.ENEMY_STATS["Melee"]["xp"]
    SIGHT = balance.ENEMY_STATS["Melee"]["sight"]
    SPRITE_KEY = "enemy_melee"
    DROP_RATE = balance.ENEMY_STATS["Melee"]["drop"]

    def update(self, player, game_map, enemies):
        if self.can_see(player, game_map):
            if self._adjacent_to(player):
                self.attack(player)
            else:
                if self.health < self.max_health // balance.RETREAT_HP_DIVISOR:
                    self._step_away((player.x, player.y), game_map, enemies, player)
                else:
                    self._step_toward((player.x, player.y), game_map, enemies, player)
        else:
            self._random_step(game_map, enemies, player)


class RangedEnemy(Enemy):
    # 원거리형: 사거리(MIN_DIST~MAX_DIST)를 유지. 너무 가까우면 후퇴, 멀면 접근, 적당하면 사격.
    NAME = "ranged"
    MAX_HEALTH = balance.ENEMY_STATS["Ranged"]["hp"]
    ATTACK = balance.ENEMY_STATS["Ranged"]["atk"]
    XP = balance.ENEMY_STATS["Ranged"]["xp"]
    SIGHT = balance.ENEMY_STATS["Ranged"]["sight"]
    MIN_DIST = balance.ENEMY_STATS["Ranged"]["min_dist"]
    MAX_DIST = balance.ENEMY_STATS["Ranged"]["max_dist"]
    SPRITE_KEY = "enemy_ranged"
    DROP_RATE = balance.ENEMY_STATS["Ranged"]["drop"]

    def update(self, player, game_map, enemies):
        if self.can_see(player, game_map):
            dist = _pythagorean_dist(self.x, self.y, player.x, player.y)
            if dist < self.MIN_DIST and random.random() < 0.5:
                self._step_away((player.x, player.y), game_map, enemies, player)
            elif dist > self.MAX_DIST:
                self._step_toward((player.x, player.y), game_map, enemies, player)
            else:
                self.attack(player)
        else:
            self._random_step(game_map, enemies, player)


class FastEnemy(Enemy):
    # 속도형: 한 턴에 STEPS_PER_TURN번(=2) 추격/공격. 힙 스케줄링 대신 '루프 2회'로 단순화했다.
    NAME = "fast"
    MAX_HEALTH = balance.ENEMY_STATS["Fast"]["hp"]
    ATTACK = balance.ENEMY_STATS["Fast"]["atk"]
    XP = balance.ENEMY_STATS["Fast"]["xp"]
    SIGHT = balance.ENEMY_STATS["Fast"]["sight"]
    STEPS_PER_TURN = balance.ENEMY_STATS["Fast"]["steps_per_turn"]
    SPRITE_KEY = "enemy_fast"
    DROP_RATE = balance.ENEMY_STATS["Fast"]["drop"]

    def update(self, player, game_map, enemies):
        for _ in range(self.STEPS_PER_TURN):
            if self.can_see(player, game_map):
                if self._adjacent_to(player):
                    self.attack(player)
                    return
                self._step_toward((player.x, player.y), game_map, enemies, player)
            else:
                self._random_step(game_map, enemies, player)


class BossEnemy(Enemy):
    # 보스: 2×2 점유. 시야와 무관하게 항상 추적(can_see=True)하고,
    # 플레이어와 인접한 빈 칸을 BFS 목표로 삼는다.
    NAME = "boss"
    MAX_HEALTH = balance.ENEMY_STATS["Boss"]["hp"]
    ATTACK = balance.ENEMY_STATS["Boss"]["atk"]
    XP = balance.ENEMY_STATS["Boss"]["xp"]
    SIGHT = balance.ENEMY_STATS["Boss"]["sight"]  # 시야 무관 추적
    SIZE = balance.ENEMY_STATS["Boss"]["size"]
    SPRITE_KEY = "enemy_boss"
    DROP_RATE = balance.ENEMY_STATS["Boss"]["drop"]

    def can_see(self, player, game_map):
        return True

    def _bfs_target_for_player(self, player, game_map, enemies):
        # 플레이어와 인접한 빈 칸 중 보스가 들어갈 수 있는 좌상단 좌표.
        candidates = []
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            ax, ay = player.x + dx, player.y + dy
            # 그 칸이 보스 점유 영역 중 어느 위치가 되어도 OK — 4가지 좌상단 후보
            for ox in range(self.SIZE):
                for oy in range(self.SIZE):
                    tlx, tly = ax - ox, ay - oy
                    if not self._blocked(tlx, tly, game_map, enemies, player):
                        candidates.append((tlx, tly))
        if not candidates:
            return None
        # 현재 위치에서 맨해튼 거리 최소
        candidates.sort(key=lambda p: abs(p[0] - self.x) + abs(p[1] - self.y))
        return candidates[0]

    def update(self, player, game_map, enemies):
        if self._adjacent_to(player):
            self.attack(player)
            return
        target = self._bfs_target_for_player(player, game_map, enemies)
        if target is not None:
            self._step_toward(target, game_map, enemies, player)

