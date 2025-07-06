import os
import sys
import traceback
import importlib.util
from . import i18n, logger, MANUAL
from . import utils
from .tts_projects import Base_Componment, TTSProjet

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


def load_ext_from_dir(roots: list[str], ext_enabled_dict:dict[str:bool]):
    loaded_ext = []
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
                assert hasattr(module, "register"), f"entry register() not found"
                extension_instance = module.register(
                    {
                        "Base_Componment": Base_Componment,
                        "TTSProjet": TTSProjet,
                        "utils": utils,
                        "i18n": i18n,
                        "MANUAL": MANUAL,
                        "logger": logger,
                    },
                )
                assert extension_instance is not None
                setattr(extension_instance, "dirname", entry)
                loaded_ext.append(extension_instance)
                logger.info(f"Loaded extension: {entry}")
            except Exception as e:
                logger.warning(f"Failed to load extension: {entry}")
                traceback.print_exc()
    return loaded_ext
