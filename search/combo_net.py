import chess
import random


class ComboNet:
    # not a net

    def __init__(self, main_net=None, end_net=None, piece_count=16):
        super().__init__()
        self.main_net = main_net
        self.end_net = end_net
        self.piece_count = piece_count

    def evaluate(self, board : chess.Board):
        if len(board.piece_map()) > self.piece_count:
            return self.main_net.evaluate(board)
        else:
            return self.end_net.evaluate(board)
