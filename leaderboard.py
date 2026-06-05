import json

# 리더보드 한 항목(레코드) 구조: {"score": int, "cleared": bool, "time": float}
# 정렬 우선순위: ① 클리어 우선  ② 점수 내림차순  ③ 소요시간 오름차순(동점 시 빠른 쪽)


def _rank_key(rec):
    #정렬 키. sorted(reverse=False)에서 작을수록 위로 오도록 변환.
    # - cleared: True가 위 → not cleared (False<True 이므로 클리어가 0)
    # - score: 큰 게 위 → 음수
    # - time: 작은 게 위 → 그대로
    return (not rec.get("cleared", False), -rec.get("score", 0), rec.get("time", float("inf")))


def _is_better(new_rec, old_rec):
    #같은 이름의 두 기록 중 new_rec이 더 좋은(위에 와야 할) 기록인가.
    return _rank_key(new_rec) < _rank_key(old_rec)

# 리더보드 클래스: 이름과 레코드(점수, 클리어 여부, 시간)를 관리. 파일 입출력 포함.
class leaderboard:
    def __init__(self):
        self.scores = {}  # {player_name: record}
        self._filename = 'leaderboard.json' # 기본 파일명

    # 파일에서 리더보드 불러오기. 없거나 깨진 파일은 빈 리더보드로 시작.
    def load_leaderboard(self, filename):
        self._filename = filename
        try:
            with open(filename, 'r') as f:
                raw = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            raw = {}
        # 하위호환: 옛 형식 {이름: 숫자} → {이름: 레코드}로 변환
        self.scores = {}
        # raw의 각 항목이 딕셔너리인지 숫자인지 확인하여 self.scores에 저장, 시간복잡도는 O(n)
        for name, val in raw.items():
            if isinstance(val, dict):
                self.scores[name] = {
                    "score":   val.get("score", 0),
                    "cleared": val.get("cleared", False),
                    "time":    val.get("time", 0.0),
                }
            else:  # 숫자만 있던 옛 데이터
                self.scores[name] = {"score": val, "cleared": False, "time": 0.0}

    # 새 기록 추가. 기존 기록보다 좋을 때만 갱신. 이후 파일에 저장.
    # 시간복잡도는 O(1) + O(n) (파일 저장이 O(n)) → 전체적으로 O(n)
    def add_score(self, player_name, score, cleared=False, time=0.0):
        rec = {"score": score, "cleared": cleared, "time": time}
        old = self.scores.get(player_name)
        # 더 좋은 기록일 때만 갱신(클리어>미클리어, 같으면 점수, 그것도 같으면 빠른 시간)
        if old is None or _is_better(rec, old):
            self.scores[player_name] = rec
        self.save_leaderboard(self._filename)

    # 리더보드 파일에 저장. 시간복잡도는 O(n) (항목 수에 비례)
    def save_leaderboard(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.scores, f)

    def get_leaderboard(self):
        # (이름, 레코드) 목록을 정렬 우선순위대로 반환. Timsort를 사용하므로 시간복잡도는 O(n log n)
        return sorted(self.scores.items(), key=lambda item: _rank_key(item[1]))
