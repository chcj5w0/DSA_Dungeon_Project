import random
import frame
import item
import render

class Player():
    
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.max_health = 100
        self.health = self.max_health
        self.base_attack_power = 10
        self.defense = 5
        self.lvl = 1
        self.exp = 0
        self.exp_to_next_lvl = 100
        self.inventory = []
        self.inventory_size = 10
        self.equipped_weapon = None
        self.alive = True
        self.items=[]
    
    def _blocked(self, x, y, game_map, enemies):
        if not game_map.is_walkable(x, y):
            return True
        for e in enemies:
            if e is self or not e.is_alive():
                continue
            for ex, ey in e.occupied_tiles():
                if ex == x and ey == y:
                    return True
        return False
    
    def move(self, game_map, direction, enemies):
        if direction == 'up':
            if not self._blocked(self.x, self.y - 1, game_map, enemies):
                self.y -= 1
        elif direction == 'down':
            if not self._blocked(self.x, self.y + 1, game_map, enemies):
                self.y += 1
        elif direction == 'left':
            if not self._blocked(self.x - 1, self.y, game_map, enemies):
                self.x -= 1
        elif direction == 'right':
            if not self._blocked(self.x + 1, self.y, game_map, enemies):
                self.x += 1
        if game_map.is_end(self.x, self.y):
            game_map.load_next_floor()
            self.x, self.y = game_map.start

    def attack(self, game_enemies):
        adjacent_enemies = []
        for enemy in game_enemies:
            for ex, ey in enemy.occupied_tiles():
                if abs(self.x - ex)<=1 and abs(self.y - ey) <= 1:
                    adjacent_enemies.append(enemy)
                    break
        for enemy in adjacent_enemies:
            enemy.take_damage(self.get_attack_power())

        for enemy in list(game_enemies):
            if not enemy.is_alive():
                self.get_exp(enemy.exp_reward)
                if random.random() < enemy.DROP_RATE and len(self.inventory) < self.inventory_size:
                    self.inventory.append(item.generate_random_item())
                    
                game_enemies.remove(enemy)

    def get_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_next_lvl:
            self.lvl_up()

    def lvl_up(self):
        self.lvl += 1
        self.exp = self.exp - self.exp_to_next_lvl
        self.exp_to_next_lvl = int(self.exp_to_next_lvl * 1.1)
        self.max_health += 10
        self.base_attack_power += 2
        self.defense += 1
        
    def get_attack_power(self):
        if self.equipped_weapon:
            return self.base_attack_power + self.equipped_weapon.attack_bonus
        return self.base_attack_power

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.die()
            
    def use_item(self, item_index):
        if 0<= item_index <len(self.inventory):
            item = self.inventory[item_index]
            if item.type == 'potion':
                self.health = min(self.max_health, self.health + item.effect_amount)
                del self.inventory[item_index]
            elif item.type == 'weapon':
                self.equipped_weapon = item
                del self.inventory[item_index]

    def is_alive(self):
        return self.alive and self.health > 0

    def die(self):
        pass