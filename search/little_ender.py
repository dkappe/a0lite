import badgyal
import search
import chess

class LittleEnderNet(search.BaseNet):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.LENet(cuda=cuda)
