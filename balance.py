"""게임 밸런스 / 레벨 디자인 튜닝 값을 한곳에 모은 모듈.

여기 숫자만 바꾸면 전투·성장·스폰 밸런스를 조정할 수 있다.
의존성 없음(순수 상수/공식) — 어느 모듈에서 import해도 순환 위험 없음.

각 값은 코드 곳곳에 흩어져 있던 기존 수치를 '동작 그대로' 옮긴 것이다.
밸런스를 바꾸려면 이 파일만 수정한다.
"""

# ──────────────────────────────────────────────────────────
# 플레이어 — 초기 스탯
# ──────────────────────────────────────────────────────────
PLAYER_BASE_HP      = 100   # 시작 최대 체력
PLAYER_BASE_ATK     = 10    # 시작 공격력
PLAYER_BASE_DEF     = 5     # 시작 방어력
PLAYER_INVENTORY    = 10    # 인벤토리 칸 수

# 플레이어 — 레벨업 성장량 (레벨업 1회당 증가치)
LVLUP_HP            = 10
LVLUP_ATK           = 2
LVLUP_DEF           = 1

# 플레이어 — 경험치 곡선
EXP_BASE            = 100   # Lv1→2 필요 경험치
EXP_GROWTH          = 1.1   # 레벨업마다 필요 경험치 배수


# ──────────────────────────────────────────────────────────
# 전투 — 공통 공식 파라미터
# ──────────────────────────────────────────────────────────
MIN_DAMAGE          = 1     # 방어가 공격 이상이어도 최소 이만큼은 들어감

# 적 레벨 스케일: stat = base * (SCALE_BASE + lvl * SCALE_PER_LVL)
ENEMY_SCALE_BASE    = 1
ENEMY_SCALE_PER_LVL = 1
# 적 경험치 보상: reward = XP * lvl  (계수)
ENEMY_XP_PER_LVL    = 1


# ──────────────────────────────────────────────────────────
# 적 종류별 기본 스탯  (hp, atk, xp, sight, drop, 그 외 특수)
# 적 실제 스탯 = base * 레벨 스케일 (위 공식)
# ──────────────────────────────────────────────────────────
ENEMY_STATS = {
    "Enemy":  dict(hp=20, atk=5,  xp=20, sight=6,   drop=0.30),  # 추상 기본값
    "Melee":  dict(hp=30, atk=6,  xp=10, sight=6,   drop=0.30),
    "Ranged": dict(hp=12, atk=5,  xp=15, sight=8,   drop=0.30,
                   min_dist=2, max_dist=4),
    "Fast":   dict(hp=10, atk=4,  xp=12, sight=7,   drop=0.30,
                   steps_per_turn=2),
    "Boss":   dict(hp=2000, atk=40, xp=100, sight=999, drop=1.0,
                   size=2),
}

# 일반 적이 도주를 시작하는 체력 비율 (MeleeEnemy: HP < MAX/RETREAT_DIVISOR)
RETREAT_HP_DIVISOR  = 5


# ──────────────────────────────────────────────────────────
# 맵 / 스폰 / 진행
# ──────────────────────────────────────────────────────────
BOSS_FLOOR          = 5      # 이 층(이상)에서 보스 스폰 + 클리어 가능
ROOM_COUNT          = 20      # 방 생성 시도 수
SPAWN_PER_ROOM_MIN  = 2      # 방당 적 수 하한
SPAWN_PER_ROOM_MAX  = 10      # 방당 적 수 상한


# ──────────────────────────────────────────────────────────
# 점수 공식 (render.compute_score 와 일치)
# ──────────────────────────────────────────────────────────
SCORE_PER_XP        = 100   # killXP 1당 점수
SCORE_PER_GOLD      = 500   # gold 1당 점수
SCORE_UNDO_PENALTY  = 10    # Undo 1회당 차감
SCORE_TIME_PENALTY  = 10    # 경과 1초당 차감


# ──────────────────────────────────────────────────────────
# 헬퍼 — 공식을 코드 여러 곳에서 같은 식으로 쓰기 위한 함수
# ──────────────────────────────────────────────────────────
def enemy_scale(lvl):
    """적 스탯 스케일 배수."""
    return ENEMY_SCALE_BASE + (lvl-1) * ENEMY_SCALE_PER_LVL


def scaled_stat(base, lvl):
    """기본 스탯 → 레벨 반영 정수 스탯."""
    return int(base * enemy_scale(lvl))


def damage(attack, defense):
    """공통 데미지 공식."""
    return max(MIN_DAMAGE, attack - defense)
