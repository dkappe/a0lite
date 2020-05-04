import numpy as np
import math
from math import sqrt
import chess
from collections import OrderedDict
from time import time
from search.util import cp
from search.pruner import Pruner

FPU = -1.0
FPU_ROOT = 0.0
PRUNER = Pruner(factor=1.0)
MATE_VAL = 32000
BATCH_SIZE = 64
COLLISION_SIZE = 999
VIRTUAL_LOSS_WEIGHT = 1.3
DRAW_THRESHOLD = -120
SINGLE_BATCH = 2

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
        # for batching
        self.virtual_loss = 0

    def Q(self):  # returns float
        calc_loss = (self.virtual_loss * VIRTUAL_LOSS_WEIGHT)
        return (self.total_value - calc_loss) / (1 + self.number_visits + calc_loss)

    def U(self):  # returns float
        return (sqrt(self.parent.number_visits)
                * self.prior / (1 + self.number_visits + (self.virtual_loss * VIRTUAL_LOSS_WEIGHT)))

    def best_child(self, C):
        # do something special at root
        if self.parent:
            chillin = self.children.values()
        else:
            non_draws = [child[1] for child in self.children.items() if not PRUNER.is_draw(child[0])]
            chillin = PRUNER.prune(non_draws)
            if len(chillin) < 1:
                chillin = self.children.values()
        return max(chillin,
                   key=lambda node: node.Q() + C*node.U())

    def select_leaf(self, C):
        current = self
        current.virtual_loss += 1
        while current.is_expanded and current.children:
            current = current.best_child(C)
            current.virtual_loss += 1
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

    def backup(self, value_estimate: float):
        current = self
        # Child nodes are multiplied by -1 because we want max(-opponent eval)
        turnfactor = -1
        while current.parent is not None:
            current.number_visits += 1
            current.virtual_loss -= 1
            current.total_value += (value_estimate *
                                    turnfactor)
            current = current.parent
            turnfactor *= -1
        current.number_visits += 1
        current.virtual_loss -= 1

    def undo_virtual_loss(self):
        current = self
        while current.parent is not None:
            current.virtual_loss -= 1
            current = current.parent
        current.virtual_loss -= 1

    def makeroot(self):
        self.parent = None
        return self

    def childByEpd(self, epd):
        # find a child with a board and a matching epd
        for child in self.children.values():
            if (child.board != None) and (child.board.epd() == epd):
                return child
        # None found
        return None

    def size(self):
        count = 1
        exp_count = 0
        if self.is_expanded:
            exp_count = 1
        if self.children == None:
            return count, exp_count
        for child in self.children.values():
            c, e = child.size()
            count += c
            exp_count += e
        return count, exp_count

    def match_position(self, board):
        return self.board.epd() == board.epd()


def process_batch(net, batch, collision_nodes):
    for leaf in collision_nodes:
        leaf.undo_virtual_loss()
    collision_nodes *= 0
    if len(batch) < 1:
        return
    # do the processing
    bulk_child_priors, bulk_value_estimates = net.bulk_evaluate([l.board for l in batch])
    for i, leaf in enumerate(batch):
        leaf.expand(bulk_child_priors[i])
        leaf.backup(bulk_value_estimates[i])
    # empty the list
    batch *= 0

def UCT_search(board, num_reads, net=None, C=1.0, verbose=False, max_time=None, tree=None, send=None):
    if max_time == None:
        # search for a maximum of an hour
        max_time = 3600.0
    max_time = max_time - 0.05
    PRUNER.update_board(board)

    # if we have a mate or all moves result in mates or draws, handle it without a search
    mate = PRUNER.get_mate()
    if mate != None:
        send("info depth 1 seldepth 1 score cp {} nodes {} nps {} pv {}".format(MATE_VAL, 0, 0, mate))
        return mate, MATE_VAL, None

    if PRUNER.all_terminal():
        draw = PRUNER.get_draw()
        send("info depth 1 seldepth 1 score cp {} nodes {} nps {} pv {}".format(0, 0, 0, draw))
        return draw, 0, None

    # reduce num_reads if there is only one move
    if len(list(board.legal_moves)) == 1:
        num_reads = 50

    # back to searching
    PRUNER.set_timeleft(max_time)

    start = time()
    count = 0
    collisions = 0
    cache_hits = 0

    # tree reuse
    if tree != None:
        root = tree
    else:
        root = UCTNode(board)

    batch = []
    collision_nodes = []

    nodes_done = 0

    while count < num_reads:
        leaf = root.select_leaf(C)

        if leaf.virtual_loss > 1:
            # we've already seen this leaf, so skip it
            #leaf.undo_virtual_loss()
            collisions += 1
            collision_nodes.append(leaf)
            if ((len(batch) >= BATCH_SIZE) or (len(collision_nodes) >= COLLISION_SIZE) or (count < SINGLE_BATCH)):
                #send("info string batch {} collisions {}".format(len(batch), len(collision_nodes)))
                process_batch(net, batch, collision_nodes)
                if PRUNER.futile(root.children.items()):
                    send("info string smart prune stop")
                    now = time()
                    delta = now - start
                    break
        else:
            # otherwise put it in the batch
            count += 1
            # see if we already have this thing
            child_priors, value_estimate = net.cached_evaluate(leaf.board, at_root=(leaf.parent == None))
            if child_priors == None:
                batch.append(leaf)
                if ((len(batch) >= BATCH_SIZE) or (len(collision_nodes) >= COLLISION_SIZE) or (count < SINGLE_BATCH)):
                    #send("info string batch {} collisions {}".format(len(batch), len(collision_nodes)))
                    process_batch(net, batch, collision_nodes)
                    if PRUNER.futile(root.children.items()):
                        send("info string smart prune stop")
                        now = time()
                        delta = now - start
                        break
            else:
                cache_hits += 1
                leaf.expand(child_priors)
                leaf.backup(value_estimate)
        now = time()
        delta = now - start
        PRUNER.set_timeleft(max_time-delta)
        if (time != None) and (delta > max_time):
            break


    # process any left over batch
    process_batch(net, batch, collision_nodes)

    # now get the rest
    bestmove, node = max(root.children.items(), key=lambda item: (item[1].number_visits, item[1].Q()))
    score = int(round(cp(node.Q()),0))
    PRUNER.update_nps(count/delta)

    if send != None:
        for nd in sorted(root.children.items(), key= lambda item: item[1].number_visits):
            send("info string {} {} \t(P: {}%) \t(Q: {})".format(nd[1].move, nd[1].number_visits, round(nd[1].prior*100,2), round(nd[1].Q(), 5)))
        send("info string collisions {} cache hits {} nps avg {}".format(collisions, cache_hits, round(PRUNER.nps, 2)))
        send("info depth 1 seldepth 1 score cp {} nodes {} nps {} pv {}".format(score, count, int(round(count/delta, 0)), bestmove))

    # if we have a bad score, go for a draw
    if score < DRAW_THRESHOLD:
        draw = PRUNER.get_draw()
        if draw != None:
            return draw, 0, None

    # make our succesor position the new root
    node.makeroot()
    return bestmove, score, node
