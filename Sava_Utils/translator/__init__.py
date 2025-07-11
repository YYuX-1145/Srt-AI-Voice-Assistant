from abc import ABC, abstractmethod
from ..base_component import Base_Component
import re


class Traducteur(Base_Component):
    def __init__(self, name, config=None):
        self.name = name
        super().__init__(name, config=config)

    def update_cfg(self, config):
        super().update_cfg(config)

    def construct_tasks(self, subtitles, batch_size: int = 1):
        """
        By default, tasks are grouped into batches.

        Example with batch_size = 2:
            Subtitle 1: Hello!
            Subtitle 2: 你好!
            Subtitle 3: Bonjour!

        The returned value will look like:
            [['Hello!', '你好!'], ['Bonjour!']]
        """
        tasks: list[list[str]] = [[]]
        for idx, item in enumerate(subtitles):
            tasks[-1].append(re.sub(r'\n+', '\n', item.text).strip())
            if (idx + 1) % batch_size == 0:
                tasks.append([])
        if len(tasks[-1]) == 0:
            tasks.pop(-1)
        return tasks

    @abstractmethod
    def api(self, tasks, target_lang, interrupt_flag, *args, file_name: str = "", **kwargs) -> list[str] | tuple[list[str], str]:
        """
        This method must be implemented by subclasses.
        It returns a list of translated subtitle strings.

        Parameters:
            tasks: The result from self.construct_tasks().
            target_lang: The language to translate into.
            interrupt_flag: A control object that allows the task to be cancelled.
                            Check interrupt_flag.is_set() periodically during long-running operations.
            *args: Additional arguments from self._UI(), typically user inputs like API keys or options.
            file_name: (Optional) You can use it to show a tqdm progress bar labeled with the file name.
            **kwargs: Other optional keyword arguments.

        Returns:
            A list of translated strings, or a tuple (translated_list, message).
        """
        raise NotImplementedError
