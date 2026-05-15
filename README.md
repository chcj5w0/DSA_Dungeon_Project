# Dungeon Crawler RPG — DS&A Team Project

Python으로 구현한 던전 크롤러 RPG 게임. GIST 자료구조및알고리즘 수업 팀 프로젝트.

## 주요 기능 (DS&A 7가지 요소)

| 기능 | 설명 |
|------|------|
| **1. Dungeon Map** | 절차적으로 생성된 던전 맵 (방 + 복도 연결) |
| **2. Undo System** | 플레이어 행동 되돌리기 (U키, 최대 30회) |
| **3. Turn Management** | 턴 기반 전투 및 적 행동 관리 |
| **4. Item Inventories** | 아이템 수집 및 인벤토리 관리 (I키) |
| **5. Enemy AI** | 플레이어 감지 및 추적 AI |
| **6. Leaderboard** | 점수 기록 및 순위표 |

## 점수 계산식

```
점수 = 킬XP×10 + 골드아이템×500 + Undo잔여×90 + max(0, 3000 - 경과초)×10
```

## 조작법

| 키 | 동작 |
|----|------|
| `WASD` | 이동 |
| `Space` | NPC 근접공격 / 밀기 |
| `F` | 원거리 공격 |
| `U` | Undo (이전 상태로 되돌리기) |
| `V` / `A` | 포제션 |
| `I` | 인벤토리 열기 |
| `R` | 새 게임 (리더보드 화면에서) |
| `ESC` | 종료 |

## HUD 정보

- 층 / 시간 / 레벨 / XP
- HP 바 (빨강)
- ATK / DEF / 화살 수
- Undo 잔여 횟수 바 (초록)
- 현재 점수 / 예상 점수
- 인벤토리 목록

## 구현 현황

| 파일 | 상태 | 비고 |
|------|------|------|
| `frame.py` | 완료 | Stack 기반 Undo (최대 30회) |
| `map.py` | 완료 | 절차적 생성 (방 배치 + L자 복도 + 시작/도착 거리 보장). `_spawn_entities`는 빈 구현 |
| `main.py` | 완료 | 게임 루프, 키 입력, 카메라 추적 렌더링. 적 AI 호출 / 아이템 획득 자리는 TODO |
| `player.py` | 부분 완료 | 이동·근접 공격 구현. HP 사망 처리·XP/레벨·원거리(F)·포제션(V/A)·인벤토리 미구현 |
| `enemy.py` | 미구현 | 빈 파일 — `Enemy` 클래스 없음 |
| Item / Inventory | 미구현 | 클래스 없음, `I`키 핸들러 자리만 존재 |
| 층 이동 (stair) | 미구현 | `TILE_END` 진입 시 다음 층 전환 처리 없음 |
| HUD | 미구현 | HP바·Undo바·점수·인벤토리 표시 없음 |
| Leaderboard | 미구현 | 점수 계산, 저장/로드, 게임오버 화면 없음 |

## 다음 작업 (우선순위 순)

1. **`Enemy` 클래스 + `Map._spawn_entities`** — 적이 화면에 등장. 추적 AI(BFS 등)는 DS&A 점수에도 직결
2. **`Item` 클래스 + `Player.inventory` + 인벤토리 UI** — DS&A 7요소 중 하나
3. **HUD** — HP/Undo 바, 층/점수 텍스트
4. **층 이동** — `TILE_END` 위에서 다음 층(`Map(floor+1)`)으로 전환
5. **Player 완성** — 사망 처리, XP/레벨, 원거리(F), 포제션(V/A)
6. **리더보드** — 점수 계산식 적용, JSON 저장/로드, 게임오버/리더보드 화면

## 알려진 이슈

- `main.py`의 턴마다 `copy.deepcopy(frame)` 호출 — 맵까지 전체 복사돼 큰 맵에서 비용이 큼. Map을 immutable로 분리하거나 Undo 대상 상태만 복사하는 식으로 최적화 여지 있음.

## 파일 구조

```
DSA/
├── main.py       # 게임 루프, 렌더링, 입력 처리
├── map.py        # 던전 맵 생성 및 구조 (Map, Room)
├── player.py     # 플레이어 상태, 이동, 공격
├── enemy.py      # (미구현) Enemy 클래스
├── frame.py      # Undo용 Stack 프레임
├── render.py     # (미사용) 렌더링은 현재 main.py 내부에 있음
├── assets/       # 스프라이트 이미지 (Player, Enemy, Tiles)
├── map/          # 맵 관련 리소스
├── MAP.md        # 던전 맵 설계 문서
└── DSA Project.pdf  # 프로젝트 발표 슬라이드
```

## 실행

```bash
python main.py
```

> pygame 라이브러리 필요: `pip install pygame`
