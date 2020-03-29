import chess

AVOID_DRAW = 0.87
PENALTY = 0.05

class NoDraw:
    def __init__(self, net):
        super().__init__()
        self.net = net

    def evaluate(self, board : chess.Board):
        move_count = len(list(board.legal_moves))
        white_count = len([x for x in board.piece_map().values() if x.color])
        black_count = len([x for x in board.piece_map().values() if not x.color])
        if board.turn:
            piece_count = white_count
        else:
            piece_count = black_count
        eval = (move_count/40.0)+(piece_count/16.0) # [0, 2.0]
        eval -= 1.0
        policy, value = self.net.evaluate(board)

        value = (0.9 * value) + (0.1 * eval)

        # avoid the draw or seek it
        if (value > AVOID_DRAW):
            if board.is_repetition(count=2):
                value -= PENALTY
        if (value < -AVOID_DRAW):
            if board.is_repetition(count=2):
                value += PENALTY
        return policy, value
