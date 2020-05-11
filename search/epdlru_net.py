import chess
import chess.syzygy
import random
import pylru

TB_CACHE_SIZE = 20000
TBMEN = 6

class EPDLRUNet:
    # not a net

    def __init__(self, net, size, tbpath=None):
        super().__init__()
        self.cache = pylru.lrucache(size)
        self.net = net
        if tbpath:
            self.tb = chess.syzygy.open_tablebase(tbpath)
        else:
            self.tb = None
        self.tbhits = 0
        self.tbcache = pylru.lrucache(TB_CACHE_SIZE)

    def reset_tbhits(self):
        self.tbhits = 0

    def tb_hits(self):
        return self.tbhits

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

    def tb_eval(self, board, policy, value):
        if not self.tb:
            return policy, value
        if len(board.piece_map()) > TBMEN:
            return policy, value
        fen = board.fen()
        if fen in self.tbcache:
            self.tbhits += 1
            return policy, self.tbcache[fen]
        wdl = self.tb.get_wdl(board)
        dtz = self.tb.get_dtz(board)
        if not wdl:
            return policy, value
        if wdl == 2:
            wdl = 1.0
        elif wdl == 1:
            wdl = 0.1
        elif wdl == -2:
            wdl = -1.0
        elif wdl == -1:
            wdl = -0.1
        else:
            wdl = 0.0
        if dtz:
            wdl = ((1000.0-dtz)/1000)*wdl
        #print("wdl {} original {} fen {}".format(wdl, value, fen))

        self.tbcache[fen] = wdl
        self.tbhits += 1
        return policy, wdl

    def cached_evaluate(self, board : chess.Board, at_root=False):
        if not at_root:
            policy, value = self.terminal(board)
            if value != None:
                return self.tb_eval(board, policy, value)

        epd = board.epd()
        if epd in self.cache:
            policy, value = self.cache[epd]
            return self.tb_eval(board, policy, value)
        else:
            policy, value = self.net.cached_evaluate(board)
            if policy != None:
                self.cache[epd] = (policy, value)
                return self.tb_eval(board, policy, value)
            else:
                return None, None

    def bulk_evaluate(self, boards):
        bulk_policies, bulk_values = self.net.bulk_evaluate(boards)
        for i, b in enumerate(boards):
            epd = b.epd()
            if not epd in self.cache:
                self.cache[epd] = (bulk_policies[i], bulk_values[i])
            p, v = self.tb_eval(b, bulk_policies[i], bulk_values[i])
            bulk_values[i] = v
        return bulk_policies, bulk_values
