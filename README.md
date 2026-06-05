# Dungeon Crawler RPG — DS&A Team Project

Python + pygame으로 구현한 던전 크롤러 RPG 게임. GIST 자료구조및알고리즘 수업 팀 프로젝트.

절차적으로 생성되는 던전을 탐험하며 적을 처치하고, 5층의 보스를 잡아 탈출하는 턴 기반 로그라이크입니다. 수업에서 요구하는 **6가지 핵심 자료구조/알고리즘 요소**를 게임 메커닉에 녹여 구현했습니다.

## 핵심 기능 (DS&A 6요소)

| # | 기능 | 자료구조 / 알고리즘 | 위치 |
|---|------|--------------------|------|
| 1 | **Dungeon Map** | 2D 그리드 `list[list[int]]`, 절차적 방 배치 + L자 복도, 시작/도착 거리 보장 | [map.py](map.py) |
| 2 | **Undo System** | Stack(LIFO), 최대 30프레임. 맵은 한 층 동안 불변이라 프레임 간 공유해 복사 비용 절감 | [frame.py](frame.py), [main.py](main.py) |
| 3 | **Turn Management** | 플레이어 행동 → 적 AI 순회 → 아이템 픽업 순서의 턴 처리 | [main.py](main.py) |
| 4 | **Item Inventory** | List(슬롯 10칸), 숫자키로 사용 (포션 회복 / 무기 장착) | [player.py](player.py), [item.py](item.py) |
| 5 | **Enemy AI** | BFS 추적 + Bresenham 시야 판정, 일반 4종 + 보스(2×2) | [enemy.py](enemy.py) |
| 6 | **Leaderboard** | 이름→최고점 `dict`, `sorted` 내림차순 정렬, JSON 영속화 | [leaderboard.py](leaderboard.py) |

## 게임 흐름

- **승리**: 보스층(5층)에서 보스를 처치하면 출구가 열리고, 출구에 도달하면 클리어. (보스 미처치 시 출구 잠김)
- **패배**: 적 AI 턴 이후 플레이어 HP가 0이 되면 사망. Undo로 되살아날 수 없도록 차단됨.
- **결과 화면**: 이름 입력 → 리더보드 저장 → TOP10 표시 → `R` 재시작 / `ESC`·`Q` 종료.

## 점수 계산식

`render.compute_score`가 계산하며, 상수는 [balance.py](balance.py)에 정의됩니다.

```
점수 = max(0, killXP×100 − Undo횟수×10 − 경과초×10)
```

| 항목 | 상수 | 값 |
|------|------|---:|
| 처치 XP 1당 | `SCORE_PER_XP` | +100 |
| 골드 1당 | `SCORE_PER_GOLD` | +500 |
| Undo 1회당 | `SCORE_UNDO_PENALTY` | −10 |
| 경과 1초당 | `SCORE_TIME_PENALTY` | −10 |

## 조작법

| 입력 | 동작 |
|------|------|
| `W` `A` `S` `D` | 이동 |
| 마우스 좌클릭 | 근접 공격 |
| `U` | Undo (이전 상태로 되돌리기, 최대 30회) |
| `1` ~ `9`, `0` | 인벤토리 슬롯 1~10번 아이템 사용 |
| `R` | 새 게임 (결과 화면에서) |
| `ESC` / `Q` | 종료 |

## HUD 정보

- 층 / 경과 시간 / 레벨 / XP
- HP 바 (빨강), Undo 잔여 횟수 바 (초록)
- ATK / DEF / 화살 수
- 현재 점수
- 인벤토리 목록

## 성능 최적화

- **Undo 맵 공유**: 맵은 한 층 동안 변하지 않으므로 `deepcopy` 대상에서 제외하고 모든 프레임이 동일 맵을 공유. 층 전환 시 `Frame.reset_history()`로 Undo 스택을 리셋.
- **적 AI 거리 게이팅**: 플레이어와 맨해튼 거리가 `AI_ACTIVE_RADIUS`(=12) 이내인 적만 매 턴 `update()`를 돌려 BFS 비용을 줄임. 보스는 멀리서도 추적하는 설계라 게이팅에서 제외.
- **이미지 1회 로드**: `render()`가 매 프레임 `load_images()`를 호출하던 병목을 제거하고, 이미지 캐시(`IMAGES`)가 비었을 때만 1회 로드.

## 파일 구조

```
DSA/
├── main.py          # 게임 루프, 입력 처리, 턴 진행, 카메라, 게임오버 화면
├── map.py           # 던전 맵 생성 (방 배치 + L자 복도 + 스폰)
├── player.py        # 플레이어 상태·이동·공격·인벤토리·층 이동
├── enemy.py         # Enemy 부모 + Melee/Ranged/Fast/Boss(2×2) AI
├── item.py          # Weapon / Potion 랜덤 생성
├── frame.py         # Undo용 Stack 프레임
├── render.py        # 맵·적·플레이어 렌더링 + HUD + 점수 계산
├── leaderboard.py   # 점수 저장/로드 (JSON), 정렬
├── balance.py       # 게임 밸런스 상수 (스탯·스폰·점수·성능)
├── assets/          # 스프라이트 이미지 (Player, Enemy, Tiles)
├── MAP.md           # 던전 맵 설계 문서
└── DSA Project.pdf  # 프로젝트 발표 슬라이드
```

## 실행

```bash
pip install pygame
python main.py
```
