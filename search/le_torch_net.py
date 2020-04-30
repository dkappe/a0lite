import badgyal
import chess
import search

class LETorchNet(search.Net):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.LETorchNet(cuda=cuda)
