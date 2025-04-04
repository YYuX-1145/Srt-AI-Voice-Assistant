import locale
from .. import logger


class Man:
    def __init__(self, language=None):
        if language in ["Auto", None]:
            language = locale.getdefaultlocale()[0]
        ls = dict()
        for x in ['README', 'changelog', 'title', 'help_custom', 'issues', 'help']:
            try:
                exec(f"from .{language} import {x}", globals(), ls)
            except ImportError:
                exec(f"from .en_US import {x}", globals(), ls)
                logger.info(f"Manual <{x}> does not support {language}.")
        self.Manual_dict = {
            "readme": ls["README"].README,
            "changelog": ls["changelog"].changelog,
            "title": ls["title"].title,
            "help_custom": ls["help_custom"].help_custom,
            "issues": ls["issues"].issues,
            "help": ls["help"].help,
        }

    def getInfo(self, key):
        return self.Manual_dict[key]
