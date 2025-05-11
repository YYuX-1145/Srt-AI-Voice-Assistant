from ..base_componment import Base_Componment
from abc import ABC, abstractmethod


class TTSProjet(Base_Componment):

    def __init__(self, name, config):
        self.name = name
        self.args = []
        super().__init__(config)

    @abstractmethod
    def api(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def save_action(self, *args, **kwargs):
        raise NotImplementedError

    def before_gen_action(self, *args, **kwargs):
        pass

    @abstractmethod
    def arg_filter(self, *args):
        raise NotImplementedError
