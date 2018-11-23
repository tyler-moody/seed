from entity import Entity

class Food(Entity):
    def __init__(self):
        super().__init__()
        self.name = 'Food'
        self.ch = '.'
        self.x = None
        self.y = None

    def update(self):
        pass
