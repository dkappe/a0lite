import chess
import random
import pylru

class EPDLRUNet:
    # not a net

    def __init__(self, net, size):
        super().__init__()
        self.cache = pylru.lrucache(size)
        self.net = net

    def evaluate(self, board : chess.Board):
        epd = board.epd()
        if epd in self.cache:
            policy, value, certainty = self.cache[epd]
            return policy, value, certainty
        else:
            policy, value, certainty = self.net.evaluate(board)
            self.cache[epd] = [policy, value, certainty]
            return policy, value, certainty
