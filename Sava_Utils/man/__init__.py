import locale

class Man():
    def __init__(self,language=None):
        if language in ["Auto", None]:
            language = locale.getdefaultlocale()[0]  
        ls=dict()
        try:
            exec(f"from .{language} import readme, title,help_custom,custom_warn,issues,help",globals(),ls)
        except:
            exec("from .zh_CN import readme, title,help_custom,custom_warn,issues,help",globals(),ls)
        self.Manual_dict = {
            "readme": ls["readme"].readme,
            "title": ls["title"].title,
            "help_custom": ls["help_custom"].help_custom,
            "custom_warn": ls["custom_warn"].custom_warn,
            "issues": ls["issues"].issues,
            "help": ls["help"].help,
        }
    def getInfo(self,key):
        return self.Manual_dict[key]
