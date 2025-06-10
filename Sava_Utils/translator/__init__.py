from abc import ABC, abstractmethod
from ..base_componment import Base_Componment
import re

class Traducteur(Base_Componment):
    def __init__(self, name, config=None):
        self.name = name
        self.args = []
        super().__init__(config)

    def update_cfg(self, config):
        super().update_cfg(config)

    def construct_tasks(self, subtitles, batch_size: int = 1):
        tasks = [[]]
        for idx, item in enumerate(subtitles):
            tasks[-1].append(re.sub(r'\n+', '\n', item.text).strip())
            if (idx + 1) % batch_size == 0:
                tasks.append([])
        if len(tasks[-1]) == 0:
            tasks.pop(-1)
        return tasks

    @abstractmethod
    def api(self, tasks, target_lang, interrupt_flag, *args, file_name: str = "", **kwargs):
        raise NotImplementedError
