class Pruner:
    def __init__(self, factor=1.0):
        super().__init__()
        self.nps = None
        self.time_left = None
        self.factor = factor

    def update_board(self, board):
        # find any checkmate moves
        self.mates = set()
        self.draws = set()

        # loop through the moves
        bd = board.copy()
        count = 0
        for m in board.legal_moves:
            bd.push(m)
            count += 1
            if bd.is_game_over(claim_draw=True):
                result = bd.result(claim_draw=True)
                if (result == "1/2-1/2"):
                    self.draws.add(m.uci())
                else:
                    # gotta be a mate
                    self.mates.add(m.uci())
            bd.pop()
        # TODO: if all the moves are terminals, make a note of that
        self.all_terminal_ = (len(self.draws)+len(self.mates)) == count

    def all_terminal(self):
        return self.all_terminal_
        
    def get_mate(self):
        if len(self.mates) < 1:
            return None
        else:
            return self.mates.pop()

    def get_draw(self):
        if len(self.draws) < 1:
            return None
        else:
            return self.draws.pop()

    def update_nps(self, nps):
        if self.nps == None:
            self.nps = nps
        else:
            # moving average of nps
            self.nps = (2*self.nps+nps)/3.0
        #print("new nps = {}".format(self.nps))

    def set_timeleft(self, time_left):
        self.time_left = time_left
        #print("time left = {}".format(time_left))

    def is_draw(self, mv):
        return mv in self.draws

    def prune(self, nodes):
        if (self.nps == None) or (self.time_left == None):
            return nodes
        max_visits = None
        for n in nodes:
            if max_visits == None:
                max_visits = n.number_visits
            if n.number_visits > max_visits:
                max_visits = n.number_visits

        nodes_left = self.nps * self.time_left

        retval = []
        for n in nodes:
            delta = (max_visits - n.number_visits)*self.factor
            if (delta < nodes_left):
                retval.append(n)
        #print("pruned {} to {}".format(len(nodes), len(retval)))
        return retval
