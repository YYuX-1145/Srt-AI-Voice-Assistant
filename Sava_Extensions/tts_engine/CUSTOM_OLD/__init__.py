"""
# Sava_Utils/extension_loader.py
# context passed to function 'register'
extension_instance = module.register(
    {
        "current_path": current_path,
        "Base_Component": Base_Component,
        "TTSProjet": TTSProjet,
        "Traducteur": Traducteur,
        "utils": utils,
        "audio_utils":audio_utils,
        "i18n": i18n,
        "MANUAL": MANUAL,
        "logger": logger,
        "Settings": Settings,
        "Shared_Option": Shared_Option,
    },
)
"""

def register(context):
    globals().update(context)
    from .custom import Custom
    return Custom()
