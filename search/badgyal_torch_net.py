import badgyal
import chess
import search

class BadGyalTorchNet(search.Net):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.BGTorchNet(cuda=cuda)
