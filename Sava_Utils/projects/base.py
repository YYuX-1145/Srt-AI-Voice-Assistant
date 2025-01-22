from abc import ABC, abstractmethod
class Projet(ABC):
    def __init__(self,name):
        self.name=name
        self.args=[]
    
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
