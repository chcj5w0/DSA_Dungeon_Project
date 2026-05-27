import json

class leaderboard:
    def __init__(self):
        self.scores = {}
        
    def load_leaderboard(self, filename):
        try:
            with open(filename, 'r') as f:
                self.scores = json.load(f)
        except FileNotFoundError:
            self.scores = {}

    def add_score(self, player_name, score):
        if player_name in self.scores:
            self.scores[player_name] = max(self.scores[player_name], score)
        else:
            self.scores[player_name] = score
        self.save_leaderboard('leaderboard.json')
        
    def save_leaderboard(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.scores, f)

    def get_leaderboard(self):
        return sorted(self.scores.items(), key=lambda x: x[1], reverse=True)