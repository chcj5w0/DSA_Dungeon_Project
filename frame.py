# a single frame of the game should have all the current information of the game

# Player's position, inventory, health, etc.
# Map information, such as the layout of the grid, locations of enemies, items, etc
# implement the frames as a stack, so that we can easily implement undo functionality

class Frame():

    frame = []
    undo_count = 0

    def __init__(self, f):
        Frame.frame.append(f)
        if len(Frame.frame) > 30:
            Frame.frame.pop(0)

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
            cls.frame[:] = [cls.frame[-1]]
    
        

        

        