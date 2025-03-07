from abc import ABC, abstractmethod
import gradio as gr
class Traducteur(ABC):
    _instances = {}

    def __init__(self, name):
        self.name = name
        self.args = []
        self.ui = False

    def update_cfg(self, config):
        pass

    @abstractmethod
    def api(self, *args, **kwargs):
        pass

    def getUI(self,*args,**kwargs):
        if not self.ui:
            self.ui = True
            return self._UI(*args,**kwargs)
        else:
            raise "ERR"

    @abstractmethod
    def _UI(self):
        raise "err"

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls, *args, **kwargs)
        return cls._instances[cls]