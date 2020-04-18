import badgyal
import search
import chess

class GoodGyalNet(search.BaseNet):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.GGNet(cuda=cuda, torchScript=cuda)
