import badgyal
import chess

class MeanGirlNet:
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.MGNet(cuda=cuda)

    def evaluate(self, board : chess.Board):
        result = None
        if board.is_game_over(claim_draw=True):
            result = board.result(claim_draw=True)

        if result != None:
            if result == "1/2-1/2":
                return dict(), 0.0
            else:
                # Always return -1.0 when checkmated
                # and we are checkmated because it's our turn to move
                return dict(), -1.0
        return self.net.eval(board)
