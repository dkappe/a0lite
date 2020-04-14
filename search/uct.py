import numpy as np
import math
import chess
from collections import OrderedDict
from time import time
from search.util import cp

FPU = -1.0
FPU_ROOT = 0.0
WIN = 1.0
LOSS = -1.0
DRAW = 0.0
DRAW_THRESHOLD = -50

class UCTNode():
    def __init__(self, board=None, parent=None, move=None, prior=0):
        self.board = board
        self.move = move
        self.is_expanded = False
        self.parent = parent  # Optional[UCTNode]
        self.children = OrderedDict()  # Dict[move, UCTNode]
        self.prior = prior  # float
        if parent == None:
            self.total_value = FPU_ROOT  # float
        else:
            self.total_value = FPU
        self.number_visits = 0  # int
        self.certainty = None # do we have a certain outcome like draw or mate

    def Q(self):  # returns float
        if self.certainty != None:
            return -self.certainty
        else:
            return self.total_value / (1 + self.number_visits)

    def U(self):  # returns float
        return (math.sqrt(self.parent.number_visits)
                * self.prior / (1 + self.number_visits))

    def uncertain_children(self):
        return [v for v in self.children.values() if v.certainty == None]

    def certain_children(self):
        return [v for v in self.children.values() if v.certainty != None]

    def best_child(self, C):
        children = self.uncertain_children()
        return max(children,
                   key=lambda node: node.Q() + C*node.U())

    def select_leaf(self, C):
        current = self
        while current.is_expanded and current.children:
            current = current.best_child(C)
        if not current.board:
            current.board = current.parent.board.copy()
            current.board.push_uci(current.move)
        return current

    def expand(self, child_priors):
        self.is_expanded = True
        for move, prior in child_priors.items():
            self.add_child(move, prior)

    def add_child(self, move, prior):
        self.children[move] = UCTNode(parent=self, move=move, prior=prior)

    def compute_certainty(self):
        all_certain = True
        best_value = None
        for child in self.children.values():
            if child.certainty == LOSS:
                return WIN
            if child.certainty == None:
                all_certain = False
            elif best_value == None:
                best_value = -child.certainty
            else:
                best_value = max(best_value, -child.certainty)
        if all_certain:
            return best_value
        else:
            return None

    def backup(self, value_estimate: float):
        current = self
        # Child nodes are multiplied by -1 because we want max(-opponent eval)
        turnfactor = -1
        while current.parent is not None:
            current.number_visits += 1
            current.total_value += (value_estimate *
                                    turnfactor)
            if self.certainty == None:
                current.certainty = current.compute_certainty()
            current = current.parent
            turnfactor *= -1
        current.number_visits += 1
        current.certainty = current.compute_certainty()

def get_best_move(root):
    # TODO deal with certain draws if the alternative "best move" sucks
    if root.certainty == WIN:
        for c in root.certain_children():
            if c.certainty == LOSS:
                bestmove = c.move
                node = c
                break
    else:
        bestmove, node = max(root.children.items(), key=lambda item: (item[1].number_visits, item[1].Q()))

    drawmove = None
    drawnode = None

    for c in root.certain_children():
        if c.certainty == DRAW:
            drawmove = c.move
            drawnode = c
            break

    score = int(round(cp(node.Q()),0))
    if (score < DRAW_THRESHOLD) and (drawmove != None):
        return drawmove, drawnode, 0
    return bestmove, node, score

def send_info(send, bestmove, count, delta, score):
    if send != None:
        send("info depth 1 seldepth 1 score cp {} nodes {} nps {} pv {}".format(score, count, int(round(count/delta, 0)), bestmove))

def UCT_search(board, num_reads, net=None, C=1.0, verbose=False, max_time=None, tree=None, send=None):
    if max_time == None:
        # search for a maximum of an hour
        max_time = 3600.0
    max_time = max_time - 0.05

    start = time()
    count = 0
    delta_last = 0

    root = UCTNode(board)
    for i in range(num_reads):
        count += 1
        leaf = root.select_leaf(C)
        child_priors, value_estimate, certainty = net.evaluate(leaf.board)
        leaf.certainty = certainty
        leaf.expand(child_priors)
        leaf.backup(value_estimate)
        now = time()
        delta = now - start
        if (delta - delta_last > 5):
            delta_last = delta
            bestmove, node, score = get_best_move(root)
            send_info(send, bestmove, count, delta, score)

        if (time != None) and (delta > max_time):
            break
        # check to see if we have a forced win
        if root.certainty != None:
            break

    bestmove, node, score = get_best_move(root)

    if send != None:
        for nd in sorted(root.children.items(), key= lambda item: item[1].number_visits):
            send("info string {} {} \t(P: {}%) \t(Q: {}) \t(Cert: {})".format(nd[1].move, nd[1].number_visits, round(nd[1].prior*100,2), round(nd[1].Q(), 5), nd[1].certainty))
        send("info depth 1 seldepth 1 score cp {} nodes {} nps {} pv {}".format(score, count, int(round(count/delta, 0)), bestmove))

    # if we have a bad score, go for a draw
    return bestmove, score
