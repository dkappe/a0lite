import numpy as np
import math
import chess
from collections import OrderedDict
from time import time
from search.util import cp

FPU = -1.0
FPU_ROOT = 0.0

BATCH_SIZE = 128
COLLISION_SIZE = 16
VIRTUAL_LOSS_WEIGHT = 3

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
        return self.total_value / (1 + self.number_visits + (self.virtual_loss * VIRTUAL_LOSS_WEIGHT))

    def U(self):  # returns float
        return (math.sqrt(self.parent.number_visits)
                * self.prior / (1 + self.number_visits + (self.virtual_loss * VIRTUAL_LOSS_WEIGHT)))

    def best_child(self, C):
        return max(self.children.values(),
                   key=lambda node: node.Q() + C*node.U())

    def select_leaf(self, C):
        current = self
        current.number_visits += VIRTUAL_LOSS_WEIGHT
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
            #process_batch(net, batch)
        else:
            # otherwise put it in the batch
            count += 1
            # see if we already have this thing
            child_priors, value_estimate = net.cached_evaluate(leaf.board)
            if child_priors == None:
                batch.append(leaf)
                if ((len(batch) >= BATCH_SIZE) or (len(collision_nodes) >= COLLISION_SIZE) or (count < 32)):
                    process_batch(net, batch, collision_nodes)
            else:
                cache_hits += 1
                leaf.expand(child_priors)
                leaf.backup(value_estimate)
        now = time()
        delta = now - start
        if (time != None) and (delta > max_time):
            break

    # process any left over batch
    process_batch(net, batch, collision_nodes)

    # now get the rest
    bestmove, node = max(root.children.items(), key=lambda item: (item[1].number_visits, item[1].Q()))
    score = int(round(cp(node.Q()),0))
    
    if send != None:
        for nd in sorted(root.children.items(), key= lambda item: item[1].number_visits):
            send("info string {} {} \t(P: {}%) \t(Q: {})".format(nd[1].move, nd[1].number_visits, round(nd[1].prior*100,2), round(nd[1].Q(), 5)))
        send("info string collisions {} cache hits {}".format(collisions, cache_hits))
        send("info depth 1 seldepth 1 score cp {} nodes {} nps {} pv {}".format(score, count, int(round(count/delta, 0)), bestmove))

    # make our succesor position the new root
    node.makeroot()
    return bestmove, score, node
