import random

def generate_random_item():
    item_type = 'potion' if random.random() < 0.7 else 'weapon'
    
    if item_type == 'weapon':
        names = ['Stick', 'Crude Iron Sword', 'Sharp Iron Sword', 'Mystic Dagger']
        randval = random.random()
        if randval < 0.4:
            name=names[0]
            attack_bonus = random.randint(1, 4)
        elif randval < 0.7:
            name=names[1]
            attack_bonus = random.randint(5, 8)
        elif randval < 0.9:
            name=names[2]
            attack_bonus = random.randint(9, 12)
        else:
            name=names[3]
            attack_bonus = random.randint(13, 20)
        return Weapon(name, attack_bonus)
    else:  # potion
        names = ['Small Health Potion', 'Large Healing Potion', 'Master Healing Elixir']
        randval = random.random()
        if randval < 0.5:
            name=names[0]
            effect_amount = random.randint(10, 19)
        elif randval < 0.8:
            name=names[1]
            effect_amount = random.randint(20, 49)
        else:
            name=names[2]
            effect_amount = random.randint(50, 100)
        return Potion(name, effect_amount)

class Item:
    def __init__(self, name="item"):
        self.name = name

    def __repr__(self):
        return f"{self.name}"
    
class Weapon(Item):
    def __init__(self, name="item", attack_bonus=0):
        super().__init__(name)
        self.attack_bonus = attack_bonus
        self.type = 'weapon'

    def __repr__(self):
        return f"{self.name}(+{self.attack_bonus}atk)"

class Potion(Item):
    def __init__(self, name="item", effect_amount=0):
        super().__init__(name)
        self.effect_amount = effect_amount
        self.type = 'potion'

    def __repr__(self):
        return f"{self.name}(+{self.effect_amount}hp)"