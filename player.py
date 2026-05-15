class Player():
    
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.max_health = 100
        self.health = self.max_health
        self.attack_power = 10
        self.defense = 5

    def move(self, game_map, direction):
        if direction == 'up':
            if game_map.is_walkable(self.x, self.y - 1):
                self.y -= 1
        elif direction == 'down':
            if game_map.is_walkable(self.x, self.y + 1):
                self.y += 1
        elif direction == 'left':
            if game_map.is_walkable(self.x - 1, self.y):
                self.x -= 1
        elif direction == 'right':
            if game_map.is_walkable(self.x + 1, self.y):
                self.x += 1

    def attack(self, game_enemies):
        for enemy in game_enemies:
            if abs(self.x - enemy.x) <= 1 and abs(self.y - enemy.y) <= 1:
                enemy.health -= self.attack_power