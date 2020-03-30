import badgyal
import chess
import search

class MeanGirlNet(search.Net):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.MGNet(cuda=cuda)
