# a single frame of the game should have all the current information of the game

# Player's position, inventory, health, etc.
# Map information, such as the layout of the grid, locations of enemies, items, etc
# implement the frames as a stack, so that we can easily implement undo functionality

from collections import deque

# 프레임은 게임의 현재 상태및 과거 상태를 저장하는 객체입니다.
# 프레임 스택은 "뒤로 push/pop(스택) + 상한 초과 시 앞에서 eviction"하는 bounded stack이다.
# 리스트로도 동작하지만 앞 원소 제거가 O(n)이라, 양 끝 연산이 모두 O(1)인 deque로 구현했다.
class Frame():
    # 프레임 스택. 최대 30개까지만 저장한다.
    frame = deque()
    undo_count = 0

    # 프레임을 생성할 때마다 스택에 추가한다. 최대 30개까지만 저장한다.
    def __init__(self, f):
        Frame.frame.append(f)
        if len(Frame.frame) > 30:
            Frame.frame.popleft()


    @classmethod
    def undo(cls):
        if len(cls.frame) > 1:
            cls.frame.pop()
            cls.undo_count += 1

    @classmethod
    def reset_history(cls):
        # 층 전환 시 호출. 모든 프레임이 같은 Map 객체를 공유하므로,
        # 이전 층의 프레임들은 이미 새 층으로 변형된 맵을 가리켜 undo 대상이 될 수 없다.
        # 가장 최근(=새 층) 프레임만 남겨 undo 스택의 새 바닥으로 삼는다.
        if cls.frame:
            cls.frame = deque([cls.frame[-1]])