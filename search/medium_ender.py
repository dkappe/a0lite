import badgyal
import search
import chess

class MediumEnderNet(search.BaseNet):
    def __init__(self, cuda=True):
        super().__init__()
        self.net = badgyal.MENet(cuda=cuda, torchScript=cuda)
