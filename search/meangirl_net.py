import badgyal
import chess

class MeanGirlNet:
    def __init__(self, device="cpu"):
        super().__init__()
        self.net = badgyal.MGNet(device=device)

    def evaluate(self, board : chess.Board):
        outcome = board.outcome(claim_draw=True)
        if outcome is not None:
            if outcome.winner is None:
                return dict(), 0.0
            # +1.0 if the side to move won, -1.0 if they lost
            if outcome.winner == board.turn:
                return dict(), 1.0
            return dict(), -1.0
        return self.net.eval(board)
