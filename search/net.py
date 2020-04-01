import chess

class Net:
    def __init__(self):
        super().__init__()

    def cached_evaluate(self, board : chess.Board):
        result = None
        if board.is_game_over():
            result = board.result()

        if result != None:
            moves = list(board.legal_moves)
            if len(moves) > 0:
                t = 1.0/len(moves)
            else:
                t = 0.01
            policy = dict()
            for m in moves:
                policy[m.uci()]  = t
            if result == "1/2-1/2":
                return policy, 0.0
            elif result == "1-0":
                if board.turn:
                    return policy, 1.0
                else:
                    return policy, -1.0
            else:
                if board.turn:
                    return policy, -1.0
                else:
                    return policy, 1.0

        # TODO: caching
        return self.net.cache_eval(board)

    def bulk_evaluate(self, boards):
        return self.net.bulk_eval(boards)
