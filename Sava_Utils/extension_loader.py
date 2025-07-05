import os
import sys
import traceback
import importlib.util
import builtins

current_path = os.environ.get("current_path")




def _load_package_from_dir(dir_path: str, Class_dict:dict=None):
    package_name = f"extension_{os.path.basename(dir_path)}"
    init_file = os.path.join(dir_path, "__init__.py")
    if not os.path.isfile(init_file):
        raise FileNotFoundError(f"{init_file} not found")
    spec = importlib.util.spec_from_file_location(package_name, init_file, submodule_search_locations=[dir_path])
    module = importlib.util.module_from_spec(spec)
    if Class_dict:
        for name, cls in Class_dict.items():
            setattr(builtins, name, cls)
    sys.modules[package_name] = module
    spec.loader.exec_module(module)
    return module


def load_ext_from_dir(roots: list[str], Class_dict: dict = None):
    loaded_ext = []
    for extension_root in roots:
        if not os.path.isdir(extension_root):
            # does not exist
            continue
        for entry in os.listdir(extension_root):
            entry_path = os.path.join(current_path, extension_root, entry)
            try:
                module = _load_package_from_dir(entry_path,Class_dict)
                assert hasattr(module, "register"), f"function register() not found"
                extension_instance = module.register()
                assert extension_instance is not None
                loaded_ext.append(extension_instance)
                print(f"ok: {getattr(extension_instance, 'name', entry)}")
            except Exception as e:
                print(f"error| {entry}: {e}")
                traceback.print_exc()
    return loaded_ext
