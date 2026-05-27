import random
from collections import deque


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

def _pythagorean_dist(x0, y0, x1, y1):
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


class Enemy():

    NAME = "enemy"
    MAX_HEALTH = 20
    ATTACK = 5
    XP = 20
    SIGHT = 6
    SPRITE_KEY = "enemy"
    DROP_RATE = 0.30
    SIZE = 1  # n×n 타일 점유. 좌상단이 (x, y)

    def __init__(self, x, y, lvl=1, exp_reward=None):
        self.x = x
        self.y = y
        self.health = int(self.MAX_HEALTH*(0.5+lvl*0.5))
        self.attack_power = int(self.ATTACK*(0.5+lvl*0.5))
        self.exp_reward = self.XP*lvl if exp_reward is None else exp_reward

    # --- 점유 영역 ---

    def occupied_tiles(self, x=None, y=None):
        """좌상단 (x, y) 기준 SIZE×SIZE 점유 좌표 목록. x/y 생략 시 현재 위치."""
        x = self.x if x is None else x
        y = self.y if y is None else y
        return [(x + dx, y + dy) for dy in range(self.SIZE) for dx in range(self.SIZE)]

    def _closest_own_tile(self, tx, ty):
        """점유 칸 중 (tx, ty)와 맨해튼 거리 최소인 칸."""
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
        # 점유 칸 중 가장 가까운 칸을 기준으로 거리/시야 판정
        ox, oy = self._closest_own_tile(player.x, player.y)
        if _pythagorean_dist(ox, oy, player.x, player.y) > self.SIGHT:
            return False
        line = _bresenham(ox, oy, player.x, player.y)
        for x, y in line[1:-1]:
            if not game_map.is_walkable(x, y):
                return False
        return True

    # --- 이동 유틸 ---

    def _blocked(self, x, y, game_map, enemies, player):
        """좌상단 (x, y)에 SIZE×SIZE로 놓일 수 있는지 검사."""
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
        """target 칸으로 가는 BFS 한 칸 이동 좌표. SIZE>1인 경우 target도 점유 검사."""
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
                if self._blocked(nx, ny, game_map, enemies, player):
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
        if nxt is not None:
            self.x, self.y = nxt

    def _step_away(self, from_xy, game_map, enemies, player):
        fx, fy = from_xy
        ox, oy = self._closest_own_tile(fx, fy)
        best = None
        best_dist = _pythagorean_dist(ox, oy, fx, fy)
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
        """점유 칸 중 하나라도 플레이어와 맨해튼 1이면 인접."""
        for tx, ty in self.occupied_tiles():
            if abs(tx - player.x) + abs(ty - player.y) == 1:
                return True
        return False

    def attack(self, player):
        dmg = max(1, self.attack_power - player.defense)
        player.take_damage(dmg)

    # --- 턴 인터페이스 ---

    def update(self, player, game_map, enemies):
        raise NotImplementedError

    # 하위 호환: 기존 코드에서 update(player, game_map)만 호출하던 경우 대비
    def move(self):
        pass


class MeleeEnemy(Enemy):
    NAME = "melee"
    MAX_HEALTH = 20
    ATTACK = 6
    XP = 10
    SIGHT = 6
    SPRITE_KEY = "enemy_melee"
    DROP_RATE = 0.3

    def update(self, player, game_map, enemies):
        if self.can_see(player, game_map):
            if self._adjacent_to(player):
                self.attack(player)
            else:
                if self.health < self.MAX_HEALTH // 5:
                    self._step_away((player.x, player.y), game_map, enemies, player)
                else:
                    self._step_toward((player.x, player.y), game_map, enemies, player)
        else:
            self._random_step(game_map, enemies, player)


class RangedEnemy(Enemy):
    NAME = "ranged"
    MAX_HEALTH = 12
    ATTACK = 5
    XP = 15
    SIGHT = 8
    MIN_DIST = 2
    MAX_DIST = 4
    SPRITE_KEY = "enemy_ranged"
    DROP_RATE = 0.3

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
    NAME = "fast"
    MAX_HEALTH = 10
    ATTACK = 4
    XP = 12
    SIGHT = 7
    STEPS_PER_TURN = 2
    SPRITE_KEY = "enemy_fast"
    DROP_RATE = 0.3

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
    NAME = "boss"
    MAX_HEALTH = 80
    ATTACK = 14
    XP = 100
    SIGHT = 999  # 시야 무관 추적
    SIZE = 2
    SPRITE_KEY = "enemy_boss"
    DROP_RATE = 1.0

    def can_see(self, player, game_map):
        return True

    def _bfs_target_for_player(self, player, game_map, enemies):
        """플레이어와 인접한 빈 칸 중 보스가 들어갈 수 있는 좌상단 좌표."""
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

