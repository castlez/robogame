import random


class Robot:
    def act(self, game):
        return random.randomchoice((['guard'], ['suicide']))
