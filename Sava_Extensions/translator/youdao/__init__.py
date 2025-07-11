def register(context):
    globals().update(context)
    # print(f'i18n current language: {i18n.get_language()}')
    i18n.update({"Youdao": "有道翻译", "APP_KEY": "您的应用ID", "APP_SECRET": "您的应用密钥"})
    from .TranslateDemo import Youdao
    return Youdao()  