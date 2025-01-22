import os

from .zh import readme, title,help_custom,custom_warn,issues,help
Manual_dict_zh = {
    "readme": readme.readme,
    "title": title.title,
    "help_custom": help_custom.help_custom,
    "custom_warn": custom_warn.custom_warn,
    "issues": issues.issues,
    "help": help.help,
}

class Man():
    def __init__(self):
        self.lang="zh"
        self.dict = {"zh": Manual_dict_zh}
    def getInfo(self,key):
        return self.dict[self.lang][key]
