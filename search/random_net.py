import chess
import random

class RandomNet:
    # not a net

    def __init__(self):
        super().__init__()

    def evaluate(self, board : chess.Board):
        result = None
        
        if board.is_game_over(claim_draw=True):
            result = board.result()
            
        if result:
            if result == "1/2-1/2":
                return dict(), 0.0
            else:
                # Always return -1.0 when checkmated
                return dict(), -1.0

        policy = {}
        total = 0.0
        moves = board.legal_moves

        for m in moves:
            r = random.random()
            policy[m.uci()] = r
            total += r

        for m in moves:
            policy[m.uci()] = policy[m.uci()]/total

        value = random.uniform(-1.0, 1.0)

        return policy, value
