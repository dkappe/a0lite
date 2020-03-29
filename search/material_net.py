import chess
import random
import math

class MaterialNet:
    # not a net

    def __init__(self):
        super().__init__()

    @staticmethod
    def scale_score(cp):
        # [-1,1]
        return (2/(1+math.exp(-0.004 * cp)) - 1)

    @staticmethod
    def norm_score(score):
        # [0,1]
        return (score+1.0)/2.0

    def _material_eval(self, board : chess.Board):
        eval = 0.0
        eval += len(board.pieces(chess.QUEEN, chess.WHITE)) * 9.0
        eval += len(board.pieces(chess.ROOK, chess.WHITE)) * 5.0
        eval += len(board.pieces(chess.BISHOP, chess.WHITE)) * 3.25
        eval += len(board.pieces(chess.KNIGHT, chess.WHITE)) * 3.0
        eval += len(board.pieces(chess.PAWN, chess.WHITE)) * 1.0
        eval -= len(board.pieces(chess.QUEEN, chess.BLACK)) * 9.0
        eval -= len(board.pieces(chess.ROOK, chess.BLACK)) * 5.0
        eval -= len(board.pieces(chess.BISHOP, chess.BLACK)) * 3.25
        eval -= len(board.pieces(chess.KNIGHT, chess.BLACK)) * 3.0
        eval -= len(board.pieces(chess.PAWN, chess.BLACK)) * 1.0
        eval += random.uniform(0.1, -0.1)
        moves = list(board.pseudo_legal_moves)
        move_val = len(moves)/30.0

        if board.turn:
            return self.scale_score(eval+move_val)
        else:
            return self.scale_score(-eval+move_val)

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

        board2 = board.copy()

        for m in moves:
            board2.push(m)
            pre = self.norm_score(-self._material_eval(board2)) + random.uniform(0, 0.05)
            #pre = random.random()+2.0
            board2.pop()
            policy[m.uci()] = pre
            total += pre

        for m in moves:
            policy[m.uci()] = policy[m.uci()]/total

        value = self._material_eval(board)

        return policy, value
