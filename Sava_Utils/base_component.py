from abc import ABC, abstractmethod
from . import settings

class Base_Component(ABC):
    _instances = {}

    def __init__(self, name = "", title = "", config=None):
        """
        The name parameter must not be empty for extensions.
        """
        self.ui = False
        self.server_mode = False
        self.name = name
        self.title = title if title else name
        if config is not None:
            self.update_cfg(config)
        super().__init__()

    def getUI(self, *args, **kwargs):
        if not self.ui:
            self.ui = True
            return self._UI(*args, **kwargs)
        else:
            raise "ERR"

    def update_cfg(self, config:settings.Settings):
        """
        Receive the global configuration and you can store the desired settings in class members.
        You can use config.query(key, default_value) to quickly access shared options.
        """
        self.server_mode = config.server_mode

    def register_settings(self) -> list[settings.Shared_Options]:
        """
        Returns a list containing settings.Shared_Options objects, to be used for registering shared configuration options.
        """
        return []

    @abstractmethod
    def _UI(self):
        """
        Define UI here.
        """
        raise NotImplementedError

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]
