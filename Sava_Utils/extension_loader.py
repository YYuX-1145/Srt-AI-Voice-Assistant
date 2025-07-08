import os
import sys
import traceback
import gradio as gr
import importlib.util
from . import i18n, logger, MANUAL, ext_tab, no_ext_mode
from . import utils,audio_utils
from .tts_engines import Base_Component, TTSProjet
from .translator import Traducteur
from .settings import Settings, Shared_Options

current_path = os.environ.get("current_path")


def _load_package_from_dir(dir_path: str):
    package_name = f"extension_{os.path.basename(dir_path)}"
    init_file = os.path.join(dir_path, "__init__.py")
    if not os.path.isfile(init_file):
        raise FileNotFoundError(f"{init_file} not found")
    spec = importlib.util.spec_from_file_location(package_name, init_file, submodule_search_locations=[dir_path])
    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    spec.loader.exec_module(module)
    return module


def load_ext_from_dir(roots: list[str], ext_enabled_dict: dict[str:bool]) -> list[Base_Component]:
    loaded_ext = []
    if no_ext_mode:
        return loaded_ext
    for extension_root in roots:
        if not os.path.isdir(extension_root):
            # does not exist
            continue
        for entry in os.listdir(extension_root):
            ext_enabled = ext_enabled_dict.get(entry, True)
            if not ext_enabled:
                continue
            entry_path = os.path.join(current_path, extension_root, entry)
            try:
                if not os.path.isdir(entry_path):
                    continue
                module = _load_package_from_dir(entry_path)
                assert hasattr(module, "register"), f"{entry}: register() not found"
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
                        "Shared_Options": Shared_Options,
                    },
                )
                assert extension_instance is not None
                assert hasattr(extension_instance, "name")
                setattr(extension_instance, "dirname", entry)
                loaded_ext.append(extension_instance)
                logger.info(f"Loaded extension: {entry}")
            except Exception as e:
                logger.warning(f"Failed to load extension: {entry}")
                traceback.print_exc()
    return loaded_ext


class Extension_Loader(Base_Component):
    def __init__(self):
        self.components = load_ext_from_dir(["Sava_Extensions/extension"], ext_enabled_dict=ext_tab["extension"])
        self.extension_dict = {i.name: i for i in self.components}
        super().__init__()

    def _UI(self, components):
        for i in self.components:
            try:
                assert i.title, "Title must not be empty."
                with gr.TabItem(i.title):
                    i.getUI(components)
            except:
                logger.error(f"Failed to load extension UI: {i.dirname}")
                traceback.print_exc()

    def getUI(self, *args, **kwargs):
        super().getUI(*args, **kwargs)
        return len(self.components) != 0
