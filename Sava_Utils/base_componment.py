from abc import ABC, abstractmethod


class Base_Componment(ABC):
    _instances = {}

    def __init__(self, config=None):
        self.ui = False
        self.server_mode = False
        if config is not None:
            self.update_cfg(config)
        super().__init__()

    def getUI(self, *args, **kwargs):
        if not self.ui:
            self.ui = True
            return self._UI(*args, **kwargs)
        else:
            raise "ERR"

    def update_cfg(self, config):
        self.server_mode = config.server_mode

    @abstractmethod
    def _UI(self):
        raise NotImplementedError

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]
