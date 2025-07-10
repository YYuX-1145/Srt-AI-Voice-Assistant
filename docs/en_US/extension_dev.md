# Extension Development Documentation

This project supports extension extension by inheriting base classes. Developers or large language models only need to derive their own extension classes and implement the necessary methods to encapsulate business logic and integrate with the UI.

*More than half of this document was written by GPT and then edited by me.*

## 1. Extension Structure Design

Extensions must be implemented as classes and inherit from one of the built-in base classes:

* The fundamental parent class for all extensions is `Base_Component`
* For **text-to-speech extensions**, inherit from `TTSProjet`
* For **translator extensions**, inherit from `Traducteur`
* For **general (extension) extensions**, inherit from `Base_Component`

---

## 2. Tip: Python Class Inheritance and Overriding

In Python, **derived classes** can inherit methods and attributes from **base classes**. You can override specific methods to customize behavior. Methods that are not overridden will use the base class implementation by default.

Example:

```python
class MyPlugin(TTSProjet):
    def api(self, text):
        return my_custom_tts(text)
```

In the example above, `MyPlugin` inherits from `TTSProjet` and only overrides the `api()` method. Other methods like `arg_filter()` and `before_gen_action()` will default to `TTSProjet`’s implementation.

---

## 3. Base Class Description

### [See complete example extension code here](/Sava_Extensions/) and also refer to the code of built-in components.

### 🔧 Base_Component (for general extensions)

This is the top-level base class for all extension components, providing a unified configuration interface and UI integration.

**Important methods and properties:**

| Method                          | Description                                                                                                                                                                         |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__(name, title = "", config = None)` | Requires a unique `name` upon initialization. If `title` is not specified, `name` will be used as the display title.                                                                |
| `update_cfg(config)`            | Accepts the global configuration object `Settings`; use `config.query(key, default)` to access shared settings.                                                                     |
| `register_settings()`           | Returns a list of shared settings items (optional), of type `list[Shared_Option]`.                                                                                                  |
| `getUI()`                       | Retrieves the UI component, internally calls `_UI()`. **Overriding this method is not recommended.**                                                                                |
| `_UI()`                         | Abstract method that must be implemented by subclasses to build the UI components. **For TTS and translator extensions, must return a list of Gradio components as parameter inputs.** |
| `__new__()`                     | Implements singleton pattern to prevent duplicate instantiation. **Do not override.**                                                                                               |

---

### 🔊 TTSProjet (for TTS extensions)

`TTSProjet` (**inherits from `Base_Component`**) is the base framework for building text-to-speech extensions. It provides hooks for API calls, parameter filtering, and execution processes.

**Recommended methods to override:**

| Method                               | Description                                                                                                                                                      |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|Base class methods like `__init__` |See`Base_Component` |
| `api(*args, **kwargs)`               | Must be implemented. Handles API calls and returns binary audio data (e.g., `.wav`).                                                                             |
| `arg_filter(*args)`                  | Optional. Validates/transforms input parameters, e.g., convert numpy audio to binary or file. Must return a tuple of parameters for `save_action`.               |
| `before_gen_action(*args, **kwargs)` | Optional. Preprocessing logic before calling `api()`, such as model loading or environment setup.                                                                |
| `save_action(*args, **kwargs)`       | By default, calls `self.api()`. Can be overridden if needed. Must return binary wav audio data or None (on error).                                               |
| `api_launcher()`                     | (Optional) Creates a shortcut API launch button UI. Define button and bind event; no return value needed.                                                        |
| `_UI()`                              | Must be implemented to construct the UI layout. You do not need to define the generate button `self.btn`. **Must return a list of Gradio components as inputs.** |

---

### 🌍 Traducteur (for subtitle translation extensions)

`Traducteur` (**inherits from `Base_Component`**) is the base class for translation extensions. It is designed to handle batch translation of subtitle text and requires implementation of the core `api()` method.

**Recommended methods to override:**

| Method                                                                   | Description                                                                                                                      |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
|Base class methods like `__init__` |See`Base_Component` |
| `construct_tasks(subtitles, batch_size=1)`                               | Organizes subtitle entries into task batches. Each task is a cleaned-up subtitle list. Optional to override.                     |
| `api(tasks, target_lang, interrupt_flag, *args, file_name="", **kwargs)` | Must be implemented. Handles the translation logic; takes a task list and returns translated strings (optionally with messages). |

---

#### 📦 self.construct_tasks(subtitles, batch_size=1)

The default implementation splits the subtitle list into smaller task batches to improve context continuity. Each task is a group of strings returned as `list[list[str]]`.

```python
# batch_size = 2
# Subtitle 1 : Hello!
# Subtitle 2 : 你好!
# Subtitle 3 : Bonjour!
[
  ["Hello!", "你好!"],
  ["Bonjour!"]
]
```

**Parameter Description:**

| Parameter    | Description                                          |
| ------------ | ---------------------------------------------------- |
| `subtitles`  | List of subtitle objects, each with a `.text` field. |
| `batch_size` | Number of subtitles per batch. Default is `1`.       |
| Return Value | `list[list[str]]`, each group as translation input.  |

---

#### 🧠 self.api(...)

Core implementation of the translation logic, must be overridden by the subclass.

**Parameter Description:**

| Parameter        | Description                                                                                                 |
| ---------------- | ----------------------------------------------------------------------------------------------------------- |
| `tasks`          | Task batches from `construct_tasks()`, as a 2D list of strings.                                             |
| `target_lang`    | Target language as a string (e.g., "中文", "English", "日本語", etc.). May be modified in the future.                             |
| `interrupt_flag` | Interruption control object of type `Flag`; use `interrupt_flag.is_set()` to check if the task is canceled. |
| `*args`          | Parameters returned from `_UI()`; user inputs like model options.                                           |
| `file_name`      | Optional file name, used to label the subtitle being processed.                                             |
| `**kwargs`       | Other optional parameters, currently unused.                                                                |

**Return Value:**

* Must return a `list[str]` representing translated subtitles (in order).
* Can also return `tuple[list[str], str]` with a message (e.g., "Model hallucinated").

---

#### 🚦 Flag: Interruption Control Tool

The framework provides a `Flag` class to support task interruption. Translation extensions should regularly check for cancellation during long-running tasks:

```python
if interrupt_flag.is_set():
    return []
```

This flag is triggered by the user through a cancel button. You only need to check and respond; no need to implement the logic.

---

## 4. Extension Registration Mechanism

### 📁 Extension Directory Structure

* All extension modules should be placed under the `Sava_Extensions/<extension_type>/<extension_name>/` directory.  
* Each extension must contain an `__init__.py` file, which includes the `register(context)` function.

Example:

```
Sava_Extensions/
└── tts_engine/
    ├── Custom/
    │   ├── __init__.py
    │   └── custom.py
    └── MyPlugin/
        ├── __init__.py
        └── ...
```

---

Extensions must be registered via the `register(context)` function in the `__init__.py` file:

```python
def register(context):    
    globals().update(context)  # Inject dependencies into the module namespace
    from .custom import Custom
    return Custom()  # Return an instance of the extension class
```

The framework will call `register()` and pass the dependency context.

---

## 5. Extension UI Construction Mechanism

Each extension must define its own UI structure by implementing `_UI()`. This method typically returns a set of Gradio components, for example:

```python
def _UI(self):
    with gr.Column():
        self.text_input = gr.Textbox(label="Input Text")
        self.gen_btn = gr.Button("Generate")
    return [self.text_input]    # TTS/Translator extensions must return a parameter list
```

The `getUI()` method is already handled by the base class. It ensures the UI is built only once and automatically injects the trigger button (e.g., `gen_btn`).

---

## 6. Shared Configuration Items: Shared_Option

`Shared_Option` is used to **declare and register global shared configuration items**.
Extensions or core components can expose configurable parameters to the “Settings Panel” and retrieve user-specified values at runtime via the `Settings` object.

---

### 1. Workflow Overview

1. **Declaration**
   Inside the extension, create `Shared_Option` instances to define keys, default values, UI component types, and (optional) validators.

2. **Registration**
   Return all `Shared_Option` objects as a **list** from `register_settings()`. The framework will automatically generate the Gradio form and persist user input to the global `Settings`.

3. **Access**
   Anywhere in the extension, use `config.query("your_key", default)` to read user settings. In validators, use the second parameter `config` to access other shared values.

---

### 2. Constructor Parameters

| Parameter                                           | Description                                                                                                                                                   |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `key: str`                                          | **Unique key name** for storing and retrieving the configuration value.                                                                                       |
| `default_value: Any`                                | Default value, applied on first run or reset.                                                                                                                 |
| `gr_component_type: gr.components.FormComponent`    | Gradio form component type (`gr.Textbox`, `gr.Slider`, `gr.Dropdown`, etc.).                                                                                  |
| `validator: Callable[[Any, Settings], Any] \| None` | (Optional) Validation/conversion function. Receives the **user input** and **global Settings**, must return a value. Raise an exception to revert to default. |
| `**gr_kwargs`                                       | Additional keyword arguments passed to the component constructor, such as `label`, `choices`, `interactive`, etc.                                             |

---

### 3. Example

```python
# Validator function: first argument is the current value, second is the global settings
def validate_path(value, config):   
    if not os.path.isfile(value):
        raise ValueError("Invalid path")  # Raising exception resets the value to default
    else:
        value = value.strip()  # You can also modify the value directly
    return value  # Must return the final value

def register_settings(self):
    return [
        Shared_Option(
            key="gsv_pydir",
            default_value="",
            gr_component_type=gr.Textbox,
            validator=validate_path,
            label="Path to Python interpreter",
            interactive=True,
        )
    ]
```

* The **validator** `validate_path` runs before saving. Raise an exception to reset, or modify the value as needed.
* To share a configuration across extensions, **use the same `key`**—all extensions will access the same stored value.
* All UI component properties (`choices`, `value`, `visible`, etc.) can be passed via `gr_kwargs`, enabling “declaration as UI”.
* **Tip**: Inside `validator`, you can use `config.query(key, default_value)` to access other settings, allowing **cross-field validation** (e.g., all paths must be on the same disk).

---

### Retrieve Updated Values

```python
class GSV(TTSProjet):
    def update_cfg(self, config: Settings):
        self.gsv_fallback = config.query("gsv_fallback")
        self.gsv_dir = config.query("gsv_dir")
        self.gsv_pydir = config.query("gsv_pydir")
        self.gsv_args = config.query("gsv_args")
        super().update_cfg(config)
```

Following these conventions allows any extension configuration item to be seamlessly integrated into the global settings system, enabling **unified UI, centralized management, and immediate effect**.
