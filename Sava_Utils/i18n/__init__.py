import locale
import os

class I18n():
    def __init__(self, language=None):
        if language in ["Auto", None]:
            language = locale.getdefaultlocale()[0]  
        if not os.path.exists(os.path.join('locale', f"{language}.py")):
            language = "en_US"
        try:
            exec(f"from .locale.{language} import i18n_dict")
        except:
            i18n_dict=dict()
        self.language_map=i18n_dict

    def __call__(self, key):
        return self.language_map.get(key, key)

    def __repr__(self):
        return f"Using Language: {self.language}"