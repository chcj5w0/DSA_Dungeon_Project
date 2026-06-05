import random
import item
import balance

# 플레이어 클래스: 위치, 체력, 공격력, 레벨, 경험치, 인벤토리 등 플레이어 상태와 행동을 관리
class Player():

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.max_health = balance.PLAYER_BASE_HP
        self.health = self.max_health
        self.base_attack_power = balance.PLAYER_BASE_ATK
        self.defense = balance.PLAYER_BASE_DEF
        self.lvl = 1
        self.exp = 0
        self.exp_to_next_lvl = balance.EXP_BASE
        self.inventory = []
        self.inventory_size = balance.PLAYER_INVENTORY
        self.equipped_weapon = None
        self.alive = True
        self.boss_defeated = False  # 보스를 처치하면 True (승리 조건의 전제)
        self.won = False            # 보스 처치 후 출구 도달 시 True
    
    # 플레이어가 이동하려는 타일이 벽이거나 적이 점유 중이면 True 반환, 아니면 False 반환
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
    
    # 플레이어 이동: 방향에 따라 위치 변경. 이동하려는 타일이 벽이나 적이 점유 중이면 이동하지 않음.
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
            if game_map.is_boss_floor():
                # 보스 층의 출구: 보스를 처치했을 때만 통과 = 승리.
                # 아직 안 잡았으면 출구가 잠긴 셈 치고 다음 층으로 보내지 않는다.
                if self.boss_defeated:
                    self.won = True
            else:
                # 일반 층의 출구: 다음 층으로 이동. 플레이어 위치는 다음 층 시작점으로 초기화.
                game_map.load_next_floor()
                self.x, self.y = game_map.start

    # 공격: 플레이어 주변 8방향에 적이 있으면 공격력만큼 피해를 입힌다.
    def attack(self, game_enemies):
        adjacent_enemies = []
        # 주변 8방향에 적이 있는지 확인해서 공격할 적 리스트를 만든다. 시간복잡도는 O(적수)이다.
        for enemy in game_enemies:
            for ex, ey in enemy.occupied_tiles():
                if abs(self.x - ex)<=1 and abs(self.y - ey) <= 1:
                    adjacent_enemies.append(enemy)
                    break
        # 공격력만큼 피해를 입힌다.
        # 아무리 적수가 많아도 최대 8칸만 영향을 주므로 시간복잡도는 O(1)이다.
        for enemy in adjacent_enemies:
            enemy.take_damage(self.get_attack_power())
        #공격 후 죽은 적이 있으면 경험치 획득, 아이템 드롭, 적 리스트에서 제거한다. 아무리 적수가 많아도 최대 8칸만 확인하므로 시간복잡도는 O(1)이다.
        for enemy in adjacent_enemies:
            if not enemy.is_alive():
                self.get_exp(enemy.exp_reward)
                if random.random() < enemy.DROP_RATE and len(self.inventory) < self.inventory_size:
                    self.inventory.append(item.generate_random_item())
                game_enemies.remove(enemy)

    # 경험치 획득: 경험치를 더하고 레벨업이 필요한지 확인한다. 레벨업이 필요하면 레벨업한다.
    def get_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_next_lvl:
            self.lvl_up()

    # 레벨업: 레벨을 올리고 경험치를 다음 레벨까지 필요한 양으로 초기화한다. 체력, 공격력, 방어력도 증가시킨다.
    def lvl_up(self):
        self.lvl += 1
        self.exp = self.exp - self.exp_to_next_lvl
        self.exp_to_next_lvl = int(self.exp_to_next_lvl * balance.EXP_GROWTH)
        self.max_health += balance.LVLUP_HP
        self.base_attack_power += balance.LVLUP_ATK
        self.defense += balance.LVLUP_DEF
        
    # 공격력 계산: 기본 공격력에 장착한 무기의 공격 보너스를 더해서 최종 공격력을 반환한다.
    def get_attack_power(self):
        if self.equipped_weapon:
            return self.base_attack_power + self.equipped_weapon.attack_bonus
        return self.base_attack_power

    # 피해 입기: 체력에서 피해량을 빼고, 체력이 0 이하가 되면 사망 처리한다.
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.die()
    
    # 아이템 사용: 인벤토리에서 아이템을 사용한다. 포션이면 체력을 회복하고, 무기면 장착한다. 사용한 아이템은 인벤토리에서 제거한다.
    def use_item(self, item_index):
        if 0<= item_index <len(self.inventory):
            item = self.inventory[item_index]
            if item.type == 'potion':
                self.health = min(self.max_health, self.health + item.effect_amount)
                del self.inventory[item_index]
            elif item.type == 'weapon':
                # 장착한 무기보다 공격 보너스가 더 좋은 무기라면 장착하고 더 안좋은 무기라면 버리고 폐기한다. (인벤토리에서 제거한다.)
                if (not self.equipped_weapon) or (item.attack_bonus > self.equipped_weapon.attack_bonus):
                    self.equipped_weapon = item
                del self.inventory[item_index]

    # 플레이어가 살아있는지 여부를 반환한다. alive 플래그가 True이고 체력이 0보다 크면 살아있는 것으로 간주한다.
    def is_alive(self):
        return self.alive and self.health > 0

    def die(self):
        # 사망 시점 훅. 패배 판정 자체는 main.turn_update가 is_alive()로 처리하므로
        # 여기서는 사망 순간 한정 효과(드롭, 사운드 등)만 둔다. 현재는 상태만 확정.
        self.alive = False