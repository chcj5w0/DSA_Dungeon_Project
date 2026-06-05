# Dungeon Crawler RPG — 진행상황

> 작성일: 2026-06-05
> 마지막 커밋: `568ff45` (6/3 commit)

## DS&A 6대 요소 진행 현황 — **전부 구현 완료**

| # | 요소 | 자료구조 / 알고리즘 | 상태 | 위치 |
|---|------|--------------------|:----:|------|
| 1 | Dungeon Map | 2D 그리드, 절차생성 + L자 복도 | ✅ | [map.py](map.py) |
| 2 | Undo System | Stack(최대 30) + 맵 공유 최적화 | ✅ | [frame.py](frame.py), [main.py](main.py) |
| 3 | Turn Management | 플레이어 → 적 AI → 아이템 픽업 | ✅ | [main.py](main.py) |
| 4 | Item Inventory | List(10칸), 숫자키 사용 | ✅ | [player.py](player.py), [item.py](item.py) |
| 5 | Enemy AI | BFS 추적 + Bresenham 시야, 4종 + 보스 | ✅ | [enemy.py](enemy.py) |
| 6 | Leaderboard | dict + sorted + JSON 영속 | ✅ | [leaderboard.py](leaderboard.py) |

> 게임오버/클리어 화면, 리더보드 저장·로드까지 모두 완성되어 6요소 전부 동작합니다.

---

## 최근 변경 (성능 최적화)

- **Undo 맵 공유**: 맵은 한 층 동안 불변 → `deepcopy`에서 제외, 프레임 간 공유. 층 전환 시 `Frame.reset_history()`로 스택 리셋.
- **적 AI 거리 게이팅** ([main.py](main.py)): 플레이어 맨해튼 거리 `AI_ACTIVE_RADIUS`(=12) 이내인 적만 매 턴 `update()`. 보스는 예외(항상 작동) → BFS 비용 절감.
- **이미지 1회 로드** ([render.py](render.py)): 매 프레임 `load_images()` 호출 제거, `IMAGES`가 빌 때만 1회 로드.

---

## 게임 종료 흐름

- **패배**: 적 AI 후 `player.is_alive()` False → 프레임 `status="dead"`, Undo로 부활 차단.
- **승리**: 보스 처치 시 `player.boss_defeated=True` → 보스층(5층) 출구 도달 시 클리어. 보스 미처치면 출구 잠김.
- **결과 화면** (`main.game_over_screen`): 이름 입력 → 리더보드 저장 → TOP10 표시 → `R` 재시작 / `ESC`·`Q` 종료.

---

## 남은 작업

1. **실제 창에서 종료 흐름 검증** — 이름 타이핑·결과 렌더·`R` 재시작은 시뮬레이션만 거침. 디스플레이 환경에서 `python3 main.py` 직접 플레이 필요.
2. **코드 정리**
   - `enemy_boss.py` 중복 (`enemy.BossEnemy`와 겹침) 확인 후 삭제
   - `animation.py` 스켈레톤 정리
   - `main.py`의 `[DEBUG]` 코드(floor=5 시작 등) 정식 빌드 전 제거
3. **평가 대비** — 면접(25%) Q&A는 `GUIDANCE_QnA.md` 참고.

---

## 평가 배점 (Guidance 기준)

| 항목 | 비중 |
|------|---:|
| PPT / 제출 | 30% |
| 6기능 구현 | 15% |
| 알고리즘 비교 | 10% |
| **면접** | **25%** |
| 데모 | 20% |

> 키워드: "Run it / Defend it / Compare it"

---

## 알려진 이슈

- `gold`는 현재 항상 0 → 점수 공식의 골드 항목 미사용 상태.
