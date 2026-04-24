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

## 파일 구조

```
DSA/
├── main.py       # 게임 루프, 렌더링, 입력 처리
├── map.py        # 던전 맵 생성 및 구조
├── player.py     # 플레이어 상태, 전투, 인벤토리
└── DSA Project.pdf  # 프로젝트 발표 슬라이드
```

## 실행

```bash
python main.py
```

> pygame 라이브러리 필요: `pip install pygame`
