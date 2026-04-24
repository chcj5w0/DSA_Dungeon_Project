import pygame
import player
import map
from frame import Frame

KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_i, pygame.K_u]

## KEY FEATURES:
## TURN-BASED
## UNDOS
## GRID-BASED
## 2D TOP-DOWN VIEW
## SIMPLE COMBAT SYSTEM
## INVENTORY SYSTEM

def turn_update(key, frame):
    player = frame["player"]
    map = frame["map"]
    enemies = frame["enemies"]
    items = frame["items"]

    # --- UNDO 기능 ---
    if key == pygame.K_u:
        Frame.undo()
        return

    # --- 플레이어 행동 ---
    if key == pygame.K_w:
        player.move('up')
    elif key == pygame.K_s:
        player.move('down')
    elif key == pygame.K_a:
        player.move('left')
    elif key == pygame.K_d:
        player.move('right')
    elif key == pygame.K_i:
        # TODO: 인벤토리 열기
        pass

    # --- 적 AI 행동 (플레이어 이동 후) ---
    for _ in enemies:
        # TODO: enemy.act(player, map)
        pass

    # --- 아이템 자동 획득 ---
    for item in items[:]:
        if item.x == player.x and item.y == player.y:
            # TODO: player.inventory.add(item)
            items.remove(item)

    f = {"player":player, "map":map, "enemies":enemies, "items":items}
    Frame(f)

def render(frame, screen):
    pass
    
    

def main():
    pygame.init()

    screen = pygame.display.set_mode((800, 600))

    pygame.display.set_caption("DSA Project")

    _player = player.Player()
    _map = map.Map()
    
    
    # KEY
    # WASD : move
    # I : inventory
    # U : Undo
    # Mouse : Attack
    
    # ESC : quit

    
    running = True
    while running:
        curr_frame = Frame.frame[-1]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in KEYS:
                    turn_update(event.key, curr_frame)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                turn_update(event.button, curr_frame)
        pygame.display.update()
    pygame.quit()



if __name__ == "__main__":
    main()
    