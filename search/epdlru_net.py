import chess
import random
import pylru

class EPDLRUNet:
    # not a net

    def __init__(self, net, size):
        super().__init__()
        self.cache = pylru.lrucache(size)
        self.net = net

    def terminal(self, board : chess.Board):
        # Only care about this close to the end of the game
        #if len(board.piece_map()) > 12:
        #    return None, None
        result = None
        if board.is_game_over(claim_draw=True):
            result = board.result(claim_draw=True)

        if result != None:
            if result == "1/2-1/2":
                return {}, 0.0
            else:
                # Always return -1.0 when checkmated
                # and we are checkmated because it's our turn to move
                return {}, -1.0
        return None, None

    def cached_evaluate(self, board : chess.Board, at_root=False):
        if not at_root:
            policy, value = self.terminal(board)
            if value != None:
                return policy, value
        
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
