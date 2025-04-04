from abc import ABC, abstractmethod


class TTSProjet(ABC):
    _instances = {}

    def __init__(self, name, config):
        self.name = name
        self.server_mode = False
        self.args = []
        self.ui = False
        self.update_cfg(config)

    def update_cfg(self, config):
        self.server_mode = config.server_mode

    @abstractmethod
    def api(self, *args, **kwargs):
        pass

    @abstractmethod
    def save_action(self, *args, **kwargs):
        pass

    def before_gen_action(self, *args, **kwargs):
        pass

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def getUI(self):
        if not self.ui:
            self.ui = True
            return self._UI()
        else:
            raise "ERR"

    @abstractmethod
    def _UI(self):
        raise "err"

    @abstractmethod
    def arg_filter(self, *args):
        pargs = []
        kwargs = {}
        return pargs, kwargs
