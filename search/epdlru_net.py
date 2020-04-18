import chess
import random
import pylru
import search

class EPDLRUNet:
    # not a net

    def __init__(self, net, size):
        super().__init__()
        self.cache = pylru.lrucache(size)
        self.net = net

    def dummy_policy(self, board : chess.Board):
        retval = {}
        for m in board.legal_moves:
            retval[m.uci()] = 0.01
        return retval

    def terminal(self, board : chess.Board):
        result = None
        if board.is_game_over(claim_draw=True):
            result = board.result(claim_draw=True)

        if result != None:
            if result == "1/2-1/2":
                return self.dummy_policy(board), 0.0, 0.0
            else:
                # Always return -1.0 when checkmated
                # and we are checkmated because it's our turn to move
                return self.dummy_policy(board), -1.0, -1.0
        return None, None, None

    def evaluate(self, board : chess.Board):
        policy, value, certainty = self.terminal(board)
        if value != None:
            return policy, value, certainty
        epd = board.epd()
        if epd in self.cache:
            policy, value, certainty = self.cache[epd]
            return policy, value, certainty
        else:
            policy, value, certainty = self.net.evaluate(board)
            self.cache[epd] = [policy, value, certainty]
            return policy, value, certainty
