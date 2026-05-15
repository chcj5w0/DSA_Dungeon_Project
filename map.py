import pygame
import random

# 타일 값
TILE_FLOOR = 0
TILE_WALL = 1
TILE_DOOR = 2
TILE_START = 3
TILE_END = 4    

class Room:
    
    def __init__(self, x, y, w, h):
        self.x = x  # 좌상단
        self.y = y
        self.w = w
        self.h = h

    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def overlaps(self, other):  # AABB 충돌 검사 (2타일 여백 포함)
        return (self.x - 2 < other.x + other.w and
                self.x + self.w + 2 > other.x and
                self.y - 2 < other.y + other.h and
                self.y + self.h + 2 > other.y)

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
        self.items = []

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
        return self.get_tile(x, y) in [TILE_FLOOR, TILE_DOOR, TILE_START, TILE_END]
    
    # --- 디버그용 맵 출력 ---
    def print_map(self):
        tile_repr = {TILE_FLOOR: '.', TILE_WALL: '#', TILE_DOOR: '+',
                     TILE_START: 'S', TILE_END: 'E'}
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
        self._spawn_entities()

    def _init_grid(self):
        self.map = [[TILE_WALL] * self.MAP_W for _ in range(self.MAP_H)]
        self.rooms = []

    def _place_rooms(self):
        for _ in range(self.ROOM_COUNT):
            w = random.randint(self.ROOM_MIN, self.ROOM_MAX)
            h = random.randint(self.ROOM_MIN, self.ROOM_MAX)
            x = random.randint(1, self.MAP_W - w - 1)
            y = random.randint(1, self.MAP_H - h - 1)
            room = Room(x, y, w, h)
            if any(room.overlaps(r) for r in self.rooms):
                continue
            self.rooms.append(room)
            self._carve_room(room)

    def _carve_room(self, room):
        for ry in range(room.y, room.y + room.h):
            for rx in range(room.x, room.x + room.w):
                self.map[ry][rx] = TILE_FLOOR

    def _connect_rooms(self):
        # 순차 연결 → 모든 방이 하나의 연결 그래프에 속함
        for i in range(len(self.rooms) - 1):
            self._carve_corridor(self.rooms[i].center(), self.rooms[i + 1].center())

    def _carve_corridor(self, a, b):
        # L자 복도: 가로 먼저 → 세로
        x1, y1 = a
        x2, y2 = b
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.map[y1][x] = TILE_FLOOR
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.map[y][x2] = TILE_FLOOR

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
        self.start = start_room.center()
        self.end = end_room.center()
        self.set_tile(*self.start, TILE_START)
        self.set_tile(*self.end, TILE_END)
        return True

    def _spawn_entities(self):
        self.monsters = []
        self.items = []
        for room in self.rooms:
            if room is self._start_room or room is self._end_room:
                continue
            # TODO: Enemy/Item 클래스 완성 후 구현
            pass

        
if __name__ == "__main__":
    m = Map()
    m.print_map()