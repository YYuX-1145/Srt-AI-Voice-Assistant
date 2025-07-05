import os
import importlib.util

current_path = os.environ.get("current_path")


def _load_package_from_dir(dir_path: str):
    package_name = f"extension_{os.path.basename(dir_path)}"
    init_file = os.path.join(dir_path, "__init__.py")
    if not os.path.isfile(init_file):
        raise FileNotFoundError(f"{init_file} not found")
    spec = importlib.util.spec_from_file_location(package_name, init_file, submodule_search_locations=[dir_path])
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_ext_from_dir(roots: list[str]):
    loaded_ext = []
    for extension_root in roots:
        if not os.path.isdir(extension_root):
            # does not exist
            continue
        for entry in os.listdir(extension_root):
            entry_path = os.path.join(current_path, extension_root, entry)
            try:
                module = _load_package_from_dir(entry_path)
                assert hasattr(module, "register"), f"register()"
                extension_instance = module.register()
                loaded_ext.append(extension_instance)
                print(f"ok: {getattr(extension_instance, 'name', entry)}")
            except Exception as e:
                print(f"error| {entry}: {e}")
    return loaded_ext
