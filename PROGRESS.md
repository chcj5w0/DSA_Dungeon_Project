# Dungeon Crawler RPG — 진행상황

> 작성일: 2026-05-25
> 마지막 커밋: `83f75eb` (test commit) — 이후 다수 변경 미커밋

## DS&A 7가지 요소 진행 현황

| # | 요소 | 자료구조/알고리즘 | 상태 | 위치 |
|---|------|--------------------|------|------|
| 1 | Dungeon Map | 절차적 생성, AABB 충돌, L자 복도 | ✅ 완료 | [map.py](map.py) |
| 2 | Undo System | Stack (최대 30 프레임) | ✅ 완료 | [frame.py](frame.py) |
| 3 | Turn Management | 키 입력 → 플레이어 → 적 AI → 아이템 픽업 | ✅ 완료 | [main.py:52-111](main.py#L52-L111) |
| 4 | Item Inventories | List 인벤토리 (10칸), 1~0 키로 사용 | ✅ 동작 / UI 일부 | [player.py](player.py), [item.py](item.py) |
| 5 | Enemy AI | BFS 추적 + Bresenham 시야 + 도주 | ✅ 완료 (4종) | [enemy.py](enemy.py) |
| 6 | Leaderboard | 점수 계산 + JSON 저장/로드 | ⚠️ 점수 계산만, 저장/게임오버 화면 미구현 | [render.py:85-92](render.py#L85-L92) |

---

## 파일별 상태

| 파일 | LOC | 상태 | 비고 |
|------|----:|------|------|
| [frame.py](frame.py) | 24 | ✅ | Stack 기반 Undo, 30 프레임 제한 |
| [map.py](map.py) | 215 | ✅ | 방 + L자 복도 + 시작/도착 거리 ≥30 보장, `_spawn_entities` / `_spawn_boss` 완성, `load_next_floor()` 구현 |
| [player.py](player.py) | 108 | ✅ 거의 완료 | HP·ATK·XP·LV·인벤토리·`use_item`·`take_damage`·층 이동 트리거. `die()`는 빈 함수 |
| [enemy.py](enemy.py) | 288 | ✅ | `Enemy` 부모 + Melee/Ranged/Fast/Boss(2×2) 4종 |
| [item.py](item.py) | 58 | ✅ | `Weapon` / `Potion` 랜덤 생성 (`generate_random_item`) |
| [main.py](main.py) | 191 | ✅ | 게임 루프, 키 입력, 카메라, 점수 누적, 아이템 자동 픽업 |
| [render.py](render.py) | 224 | ✅ | 맵·적·플레이어 + HUD (HP/Undo/XP 바, 점수, 인벤토리) |
| [enemy_boss.py](enemy_boss.py) | 18 | ⚠️ 중복 | `enemy.py`의 `BossEnemy`와 중복 — 삭제 필요 |
| [animation.py](animation.py) | 6 | ⚠️ 스켈레톤 | `symtable` import만 있고 미사용 |

---

## 메모리 대비 새로 추가된 것 (지난 10일)

- **`render.py` 완성** — 빈 파일 → 224줄. HUD (Floor/Time/Lv/XP/HP/ATK/DEF/Arrows/Undo/Score/Inventory) 전부 구현
- **`player.use_item`** — 1~0 키로 인벤토리 슬롯 사용 (포션 회복 / 무기 장착)
- **`main.py` 아이템 자동 픽업** — 플레이어 좌표와 동일한 아이템 인벤토리 추가
- **점수 공식 적용** — `_compute_score()`가 README 공식대로 계산해서 HUD에 표시
- **층 이동 동작** — `player.move` 안에서 `TILE_END` 진입 시 `Map.load_next_floor()` 호출

---

## 남은 작업 (우선순위)

1. **게임오버 / 클리어 화면** — `player.die()`가 빈 함수, 보스 처치 후 처리 없음
2. **리더보드 저장** — 현재는 화면 표시만, JSON 저장/로드 + 리더보드 화면 필요
3. **인벤토리 UI (I키)** — HUD 사이드바에 목록은 보이지만 별도 인벤토리 화면(I키) 미구현
4. **원거리(F) / 포제션(V/A)** — `KEYS`에 없음, README에는 기재됨
5. **코드 정리**
   - `enemy_boss.py` 삭제 (`enemy.BossEnemy`와 중복)
   - `animation.py`에서 `import symtable` 제거 또는 파일 자체 삭제
   - `main.py`의 `[DEBUG]` 코드 (`K_b`, `K_t`, `floor=5` 시작) 정식 빌드 전 제거
   - `main.py`에 남아 있는 사용되지 않는 `TILE_COLORS` / `load_images` 중복 (render.py에 동일 정의)

---

## 알려진 이슈

- 매 턴 `copy.deepcopy(frame)` 호출 — 맵까지 통째로 복사돼 큰 맵에서 비용 큼. Map immutable 분리 검토 여지
- `render()` 안에서 매 프레임 `load_images()` 호출 — `main.load_images()`와 별개로 매번 디스크 로드. 시작 시 1회만 호출하도록 정리 필요
