# a single frame of the game should have all the current information of the game

# Player's position, inventory, health, etc.
# Map information, such as the layout of the grid, locations of enemies, items, etc
# implement the frames as a stack, so that we can easily implement undo functionality

class Frame():

    frame = []

    def __init__(self, f):
        Frame.frame.append(f)
        if len(Frame.frame) > 30:
            Frame.frame.pop(0)
    
    def undo(self):
        if len(Frame.frame) > 1:
            Frame.frame.pop()
    
        

        

        