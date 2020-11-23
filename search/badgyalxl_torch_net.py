import badgyal
import chess
import search

class BadGyalXLTorchNet(search.Net):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.BGXLTorchNet(cuda=cuda)
