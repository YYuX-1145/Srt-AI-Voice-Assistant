from abc import ABC, abstractmethod
class TTSProjet(ABC):
    _instances = {}    

    def __init__(self,name):
        self.name=name
        self.args=[]
        self.ui=False        

    def update_cfg(self,config):
        pass

    @abstractmethod
    def api(self,*args,**kwargs):
        pass

    @abstractmethod    
    def save_action(self,*args, **kwargs):
        pass

    def before_gen_action(self,*args, **kwargs):
        pass

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls, *args, **kwargs)
        return cls._instances[cls]
    
    def getUI(self):
        if not self.ui:
            self.ui=True
            return self._UI()            
        else:
            raise "ERR"

    @abstractmethod
    def _UI(self):
        raise "err"

    @abstractmethod
    def arg_filter(self,*args):
        pargs=[]
        kwargs={}
        return pargs,kwargs
