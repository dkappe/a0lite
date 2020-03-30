import chess
import random
import pylru

class EPDLRUNet:
    # not a net

    def __init__(self, net, size):
        super().__init__()
        self.cache = pylru.lrucache(size)
        self.net = net

    def cached_evaluate(self, board : chess.Board):
        epd = board.epd()
        if epd in self.cache:
            policy, value = self.cache[epd]
            return policy, value
        else:
            policy, value = self.net.cached_evaluate(board)
            if policy != None:
                self.cache[epd] = (policy, value)
                return policy, value
            else:
                return None, None

    def bulk_evaluate(self, boards):
        bulk_policies, bulk_values = self.net.bulk_evaluate(boards)
        for i, b in enumerate(boards):
            epd = b.epd()
            if not epd in self.cache:
                self.cache[epd] = (bulk_policies[i], bulk_values[i])
        return bulk_policies, bulk_values
