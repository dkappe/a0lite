import badgyal
import search
import chess

class MeanGirlNet(search.BaseNet):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.MGNet(cuda=cuda)
