class Tile():
    def __init__(self, location):
        self.symbol = " " #Character to be displayed
        self.location = location #[x value, y value]

class Wall(Tile):
    def __init__(self, location):
        self.location = location
        self.symbol = "X"