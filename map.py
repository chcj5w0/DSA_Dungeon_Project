import random
from enemy import MeleeEnemy, RangedEnemy, FastEnemy, BossEnemy

BOSS_FLOOR = 5  # 이 층(이상)에서 보스 스폰

# 타일 값
TILE_FLOOR = 0
TILE_WALL = 1
TILE_DOOR = 2
TILE_START = 3
TILE_END = 4
TILE_RUBBLE = 5  # 돌조각: 통행 가능, 시각적 장식용
TILE_HINT = 6    # 도착점 근처 힌트 타일: 통행 가능

class Room:

    SHAPES = ('rect', 'l_shape', 'circle', 'cave')

    def __init__(self, x, y, w, h, shape='rect'):
        self.x = x  # 좌상단
        self.y = y
        self.w = w
        self.h = h
        self.shape = shape
        # L자 방의 잘려나간 사분면 (0=좌상, 1=우상, 2=좌하, 3=우하)
        self.cut_quadrant = random.randint(0, 3) if shape == 'l_shape' else None
        # 동굴형은 CA로 미리 마스크를 만들어 둔다 (True=바닥)
        self.mask = self._generate_cave_mask() if shape == 'cave' else None

    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def overlaps(self, other):  # AABB 충돌 검사 (2타일 여백 포함)
        return (self.x - 2 < other.x + other.w and
                self.x + self.w + 2 > other.x and
                self.y - 2 < other.y + other.h and
                self.y + self.h + 2 > other.y)

    def contains_floor(self, x, y):
        """방의 실제 바닥(모양 고려) 포함 여부."""
        if not (self.x <= x < self.x + self.w and self.y <= y < self.y + self.h):
            return False
        if self.shape == 'rect':
            return True
        if self.shape == 'circle':
            cx, cy = self.center()
            rx, ry = self.w / 2 - 0.5, self.h / 2 - 0.5
            return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.05
        if self.shape == 'l_shape':
            # 한 사분면을 잘라낸다. 잘린 영역은 방 면적의 약 1/4
            cw, ch = self.w // 2, self.h // 2
            q = self.cut_quadrant
            qx0 = self.x if q in (0, 2) else self.x + self.w - cw
            qy0 = self.y if q in (0, 1) else self.y + self.h - ch
            in_cut = (qx0 <= x < qx0 + cw) and (qy0 <= y < qy0 + ch)
            return not in_cut
        if self.shape == 'cave':
            return self.mask[y - self.y][x - self.x]
        return True

    # --- 동굴형 (cellular automata) ---

    def _generate_cave_mask(self):
        """방 영역에 CA 규칙을 돌려 자연스러운 동굴 모양 마스크 생성."""
        w, h = self.w, self.h
        # 1) 초기 노이즈 — 가장자리는 강제 벽, 안쪽은 ~52% 바닥
        grid = [[(random.random() < 0.52) for _ in range(w)] for _ in range(h)]
        for i in range(w):
            grid[0][i] = False
            grid[h - 1][i] = False
        for j in range(h):
            grid[j][0] = False
            grid[j][w - 1] = False

        # 2) CA 반복 — 8-이웃 중 바닥이 5개 이상이면 바닥
        for _ in range(5):
            new = [row[:] for row in grid]
            for j in range(1, h - 1):
                for i in range(1, w - 1):
                    n = 0
                    for dj in (-1, 0, 1):
                        for di in (-1, 0, 1):
                            if di == 0 and dj == 0:
                                continue
                            if grid[j + dj][i + di]:
                                n += 1
                    new[j][i] = (n >= 5) if grid[j][i] else (n >= 6)
            grid = new

        # 3) 가장 큰 연결 컴포넌트만 남기기 (단절된 섬 제거)
        seen = [[False] * w for _ in range(h)]
        best = []
        for sj in range(h):
            for si in range(w):
                if not grid[sj][si] or seen[sj][si]:
                    continue
                comp = []
                stack = [(si, sj)]
                seen[sj][si] = True
                while stack:
                    ci, cj = stack.pop()
                    comp.append((ci, cj))
                    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ni, nj = ci + di, cj + dj
                        if 0 <= ni < w and 0 <= nj < h and grid[nj][ni] and not seen[nj][ni]:
                            seen[nj][ni] = True
                            stack.append((ni, nj))
                if len(comp) > len(best):
                    best = comp

        mask = [[False] * w for _ in range(h)]
        for ci, cj in best:
            mask[cj][ci] = True

        # 4) 너무 비면(=거의 다 벽) fallback: 중심 부근만 바닥으로 채워 안전망
        if sum(sum(row) for row in mask) < 4:
            cx, cy = w // 2, h // 2
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    if 0 <= cx + di < w and 0 <= cy + dj < h:
                        mask[cy + dj][cx + di] = True
        return mask

class Map:
    
    MAP_W = 80
    MAP_H = 50
    ROOM_MIN = 4
    ROOM_MAX = 10
    ROOM_COUNT = 12
    MIN_DIST = 30  # 시작/도착 방 최소 맨해튼 거리
    
    def __init__(self, floor=1):
        self.floor = floor
        self.map = []         # list[list[int]]
        self.rooms = []       # list[Room]
        self.start = None     # (x, y) 플레이어 스폰
        self.end = None       # (x, y) 계단/출구
        self.monsters = []    # 추후 Enemy 클래스로 교체

        self._generate()

    # --- 외부 인터페이스 ---

    def get_tile(self, x, y):
        if self.in_bounds(x, y):
            return self.map[y][x]
        return None

    def set_tile(self, x, y, tile):
        if self.in_bounds(x, y):
            self.map[y][x] = tile

    def in_bounds(self, x, y):
        return 0 <= x < self.MAP_W and 0 <= y < self.MAP_H

    def is_walkable(self, x, y):
        return self.get_tile(x, y) in [TILE_FLOOR, TILE_DOOR, TILE_START, TILE_END, TILE_RUBBLE, TILE_HINT]
    
    def is_end(self, x, y):
        return self.get_tile(x, y)==TILE_END
    
    # --- 디버그용 맵 출력 ---
    def print_map(self):
        tile_repr = {TILE_FLOOR: '.', TILE_WALL: '#', TILE_DOOR: '+',
                     TILE_START: 'S', TILE_END: 'E',
                     TILE_RUBBLE: ',', TILE_HINT: '*'}
        for row in self.map:
            print(''.join(tile_repr.get(tile, '?') for tile in row))

    # --- 생성 ---

    def _generate(self):
        while True:
            self._init_grid()
            self._place_rooms()
            self._connect_rooms()
            if self._place_start_end():
                break  # 거리 조건 충족 시 탈출, 아니면 재생성
        self._scatter_noise()
        self.monsters = []
        self._spawn_entities(self.monsters)

    def _scatter_noise(self):
        """맵 전체에 장식용 노이즈 추가: 바닥 돌조각 + 도착 힌트 + 벽 가장자리 랜모니.
        도착점 근처일수록 힌트 타일 확률이 높아진다."""
        ex, ey = self.end
        hint_radius = 28
        rubble_rate = 0.03   # 일반 돌조각 비율 (전역)
        hint_max = 0.18      # 도착점 바로 위에서의 힌트 최대 비율
        hint_floor = 0.03    # 반경 끝에서도 유지되는 최소 힌트 비율
        # 1) 바닥 일부를 돌조각/힌트로 — 통행 가능, 시각만 변경
        for y in range(self.MAP_H):
            for x in range(self.MAP_W):
                if self.map[y][x] != TILE_FLOOR:
                    continue
                d = max(abs(x - ex), abs(y - ey))
                # 힌트: 도착점 근처에서만, 거리 비례로 확률 상승 (가장자리도 floor 유지)
                if d <= hint_radius:
                    t = 1.0 - d / hint_radius
                    hint_rate = hint_floor + (hint_max - hint_floor) * t
                    if random.random() < hint_rate:
                        self.map[y][x] = TILE_HINT
                        continue
                # 일반 돌조각: 전역 균등
                if random.random() < rubble_rate:
                    self.map[y][x] = TILE_RUBBLE
        # 2) 벽 → 바닥 랜모니: 바닥과 인접한 벽 일부를 깎아 가장자리에 요철
        carved = []
        for y in range(1, self.MAP_H - 1):
            for x in range(1, self.MAP_W - 1):
                if self.map[y][x] != TILE_WALL:
                    continue
                # 인접 8칸 중 바닥(또는 rubble)이 있는지
                touches_floor = False
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        if self.map[y + dy][x + dx] in (TILE_FLOOR, TILE_RUBBLE, TILE_HINT):
                            touches_floor = True
                            break
                    if touches_floor:
                        break
                if touches_floor and random.random() < 0.06:
                    carved.append((x, y))
        for x, y in carved:
            self.map[y][x] = TILE_FLOOR

    def _init_grid(self):
        self.map = [[TILE_WALL] * self.MAP_W for _ in range(self.MAP_H)]
        self.rooms = []

    def _place_rooms(self):
        # 모양별 가중치: 직사각형 위주, 나머지는 가끔
        shape_weights = [('rect', 0.45), ('l_shape', 0.2), ('circle', 0.1), ('cave', 0.25)]
        for _ in range(self.ROOM_COUNT):
            w = random.randint(self.ROOM_MIN, self.ROOM_MAX)
            h = random.randint(self.ROOM_MIN, self.ROOM_MAX)
            x = random.randint(1, self.MAP_W - w - 1)
            y = random.randint(1, self.MAP_H - h - 1)
            r = random.random()
            cum = 0
            shape = 'rect'
            for s, p in shape_weights:
                cum += p
                if r < cum:
                    shape = s
                    break
            # 비정형은 너무 작으면 형태가 안 살아남 → 최소 크기 보장
            if shape in ('circle', 'l_shape', 'cave') and (w < 6 or h < 6):
                shape = 'rect'
            room = Room(x, y, w, h, shape)
            if any(room.overlaps(r2) for r2 in self.rooms):
                continue
            self.rooms.append(room)
            self._carve_room(room)

    def _carve_room(self, room):
        for ry in range(room.y, room.y + room.h):
            for rx in range(room.x, room.x + room.w):
                if room.contains_floor(rx, ry):
                    self.map[ry][rx] = TILE_FLOOR

    def _room_anchor(self, room):
        """복도가 시작/도착할 방 내부 점 — center가 잘린 영역이면 가장 가까운 바닥 칸으로 보정."""
        cx, cy = room.center()
        if room.contains_floor(cx, cy):
            return (cx, cy)
        best, best_d = (cx, cy), 10 ** 9
        for ry in range(room.y, room.y + room.h):
            for rx in range(room.x, room.x + room.w):
                if room.contains_floor(rx, ry):
                    d = abs(rx - cx) + abs(ry - cy)
                    if d < best_d:
                        best_d = d
                        best = (rx, ry)
        return best

    def _connect_rooms(self):
        # 최근접 미연결 방으로 차례차례 잇기 (Prim 비슷). 평균 복도 길이가 짧아진다.
        if not self.rooms:
            return
        anchors = [self._room_anchor(r) for r in self.rooms]
        connected = {0}
        while len(connected) < len(self.rooms):
            best = None
            best_d = 10 ** 9
            for i in connected:
                for j in range(len(self.rooms)):
                    if j in connected:
                        continue
                    ax, ay = anchors[i]
                    bx, by = anchors[j]
                    d = abs(ax - bx) + abs(ay - by)
                    if d < best_d:
                        best_d = d
                        best = (i, j)
            i, j = best
            self._carve_corridor(anchors[i], anchors[j])
            connected.add(j)
        # 가끔 추가 루프 1~2개 — 막다른 길 줄이고 다양성 ↑
        extra = random.randint(1, 2)
        for _ in range(extra):
            i, j = random.sample(range(len(self.rooms)), 2)
            self._carve_corridor(anchors[i], anchors[j])

    def _carve_corridor(self, a, b):
        # Drunken walk: 70% 확률로 목표 방향, 30%는 옆길 일탈.
        # 매 스텝 현재 칸을 바닥으로 깎고, 가끔 인접 칸도 깎아 폭에 변화를 줌.
        x, y = a
        x2, y2 = b
        self.map[y][x] = TILE_FLOOR
        max_steps = (abs(x2 - x) + abs(y2 - y)) * 4 + 50  # 무한 루프 방지
        for _ in range(max_steps):
            if (x, y) == (x2, y2):
                break
            # 방향 후보: 목표 쪽 두 축 + 일탈 두 축
            toward = []
            if x < x2: toward.append((1, 0))
            elif x > x2: toward.append((-1, 0))
            if y < y2: toward.append((0, 1))
            elif y > y2: toward.append((0, -1))
            sideways = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            if random.random() < 0.7 and toward:
                dx, dy = random.choice(toward)
            else:
                dx, dy = random.choice(sideways)
            nx, ny = x + dx, y + dy
            # 맵 경계 안쪽으로만 (가장자리 1칸은 항상 벽 유지)
            if not (1 <= nx < self.MAP_W - 1 and 1 <= ny < self.MAP_H - 1):
                continue
            x, y = nx, ny
            self.map[y][x] = TILE_FLOOR
            # 가끔 옆 칸도 깎아서 통로 폭/형태에 변화
            if random.random() < 0.25:
                ex, ey = x + random.choice([-1, 1]), y
                if 1 <= ex < self.MAP_W - 1:
                    self.map[ey][ex] = TILE_FLOOR
            if random.random() < 0.25:
                ex, ey = x, y + random.choice([-1, 1])
                if 1 <= ey < self.MAP_H - 1:
                    self.map[ey][ex] = TILE_FLOOR

    def _place_start_end(self):
        if len(self.rooms) < 2:
            return False
        # 맨해튼 거리가 가장 먼 두 방 선택
        best_dist = 0
        start_room, end_room = self.rooms[0], self.rooms[-1]
        for i in range(len(self.rooms)):
            for j in range(i + 1, len(self.rooms)):
                cx1, cy1 = self.rooms[i].center()
                cx2, cy2 = self.rooms[j].center()
                dist = abs(cx1 - cx2) + abs(cy1 - cy2)
                if dist > best_dist:
                    best_dist = dist
                    start_room, end_room = self.rooms[i], self.rooms[j]
        if best_dist < self.MIN_DIST:
            return False
        self._start_room = start_room
        self._end_room = end_room
        self.start = self._room_anchor(start_room)
        self.end = self._room_anchor(end_room)
        self.set_tile(*self.start, TILE_START)
        self.set_tile(*self.end, TILE_END)
        return True

    def _can_place(self, x, y, size, occupied):
        """좌상단 (x, y)에 size×size 점유 가능 여부 — 경계/벽/이미 점유된 칸 검사."""
        for dy in range(size):
            for dx in range(size):
                tx, ty = x + dx, y + dy
                if not self.in_bounds(tx, ty):
                    return False
                if not self.is_walkable(tx, ty):
                    return False
                if (tx, ty) in occupied:
                    return False
                if (tx, ty) == self.start or (tx, ty) == self.end:
                    return False
        return True

    def _spawn_entities(self, enemies):
        enemy_types = [MeleeEnemy, RangedEnemy, FastEnemy]

        # 마지막 층에는 도착 방 근처에 보스 1마리
        if self.floor >= BOSS_FLOOR:
            self._spawn_boss(enemies)

        for room in self.rooms:
            if room is self._start_room or room is self._end_room:
                continue

            count = random.randint(2, 5)
            occupied = set()
            for _ in range(count):
                if len(occupied) >= room.w * room.h:
                    break

                placed = False
                for _ in range(20):  # 후보 시도 횟수 제한
                    ex = random.randint(room.x, room.x + room.w - 1)
                    ey = random.randint(room.y, room.y + room.h - 1)
                    if not self._can_place(ex, ey, 1, occupied):
                        continue
                    occupied.add((ex, ey))
                    placed = True
                    break

                if placed:
                    enemy_class = random.choice(enemy_types)
                    enemies.append(enemy_class(ex, ey, self.floor))

    def _spawn_boss(self, enemies):
        """도착 방 안에 BossEnemy(2×2) 한 마리 배치."""
        room = self._end_room
        candidates = []
        for y in range(room.y, room.y + room.h - 1):
            for x in range(room.x, room.x + room.w - 1):
                if self._can_place(x, y, BossEnemy.SIZE, set()):
                    candidates.append((x, y))
        if not candidates:
            return  # 보스 자리 없으면 스킵 (방이 너무 작은 경우)
        bx, by = random.choice(candidates)
        enemies.append(BossEnemy(bx, by))

    def load_next_floor(self):
        if self.floor >= BOSS_FLOOR:
            #TODO: 클리어 처리
            pass
        self.floor += 1
        self._generate()


if __name__ == "__main__":
    m = Map()
    m.print_map()