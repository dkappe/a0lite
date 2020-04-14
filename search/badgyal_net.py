import badgyal
import search
import chess

class BadGyalNet(search.BaseNet):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.BGNet(cuda=cuda)
