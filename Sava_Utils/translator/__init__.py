from abc import ABC, abstractmethod
from ..base_componment import Base_Componment


class Traducteur(Base_Componment):
    def __init__(self, name, config=None):
        self.name = name
        self.args = []
        super().__init__(config)

    def update_cfg(self, config):
        self.server_mode = config.server_mode

    @abstractmethod
    def api(self, *args, **kwargs):
        pass
