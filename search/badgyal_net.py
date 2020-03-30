import badgyal
import chess
import search

class BadGyalNet(search.Net):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.BGNet(cuda=cuda)
