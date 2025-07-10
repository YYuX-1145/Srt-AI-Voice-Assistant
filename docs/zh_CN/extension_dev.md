# 插件开发文档

本项目支持通过继承基类实现插件扩展。开发者或者大语言模型只需派生自己的插件类并实现必要的方法，即可完成业务逻辑的封装与 UI 集成。  

*这个文档有一半以上是GPT写的并经过我的修改

---

## 1. 插件结构设计

插件必须以类的形式实现，并继承于内置的基类之一：

* 所有插件最基础的基类是 `Base_Component`
* 如果是**文本转语音类插件**，请继承 `TTSProjet`
* 如果是**翻译器类插件**，请继承 `Traducteur`
* 如果是**一般插件(即扩展插件)**，请继承 `Base_Component`

---

## 2. 提示：Python 类继承与覆写

在Python中，**派生类** 可以继承 **基类** 的方法和属性。你可以通过覆写某些方法来自定义行为，未覆写的部分将自动使用基类中的默认实现。

例如：

```python
class MyPlugin(TTSProjet):
    def api(self, text):
        return my_custom_tts(text)
```

上述代码中，`MyPlugin` 继承自 `TTSProjet`，只覆写了 `api()` 方法，其他未覆写的方法如 `arg_filter()`、`before_gen_action()` 等会自动沿用 `TTSProjet` 的实现。

---

## 3. 基类说明
### [完整的示例插件代码看这里](/Sava_Extensions/)，以及你参阅内置组件的代码也是一样的

### 🔧 Base_Component（用于一般插件）

这是所有插件组件的最顶层基类，提供统一的配置接口和 UI 接入方式。

**重要方法与属性：**

| 方法                              | 说明                                                           |
| ------------------------------- | ------------------------------------------------------------ |
| `__init__(name, title = "", config = None)` | 插件初始化时必须提供唯一的 `name`。如果未指定 `title`，将使用 `name` 作为显示标题。        |
| `update_cfg(config)`            | 接收全局配置对象 `Settings`，可调用 `config.query(key, default)` 获取共享配置。 |
| `register_settings()`           | 返回共享配置项列表（可选），类型为 `list[Shared_Option]`。                    |
| `getUI()`                       | 获取组件 UI，内部会调用 `_UI()`，**不建议覆写此方法**。                          |
| `_UI()`                         | 抽象方法，必须由子类实现，用于构建 UI 组件。**对于TTS引擎和翻译器，必须返回包含gradio组件的列表作为参数输入。**                                    |
| `__new__()`                     | 实现了单例模式，防止插件被重复实例化，**不得覆写**。                                 |

---

### 🔊 TTSProjet（用于 TTS 插件）
`TTSProjet`(**继承自`Base_Component`**)是用于构建文本转语音插件的基础框架，提供 API 调用、参数过滤、执行流程等典型钩子。

**推荐覆写的方法：**

| 方法                                   | 说明                                        |
| ------------------------------------ | ----------------------------------------- |
|`__init__`等基类方法 |见`Base_Component` |
| `api(*args, **kwargs)`               | 必须实现。处理 API 调用，返回音频的二进制数据（如 `.wav` 文件内容）。 |
| `arg_filter(*args)`                  | 可选。对输入参数进行验证与转换，例如将numpy格式音频转为二进制数据或存储为文件。必须返回一个参数元组，它将被输入`save_action`方法。        |
| `before_gen_action(*args, **kwargs)` | 可选。在调用 `api()` 前执行的预处理逻辑，例如加载模型、配置环境等。       |
| `save_action(*args, **kwargs)`       | 默认调用 `self.api()`，可根据需求重写。必须返回wav音频二进制数据或None(如果遭遇错误)|
| `api_launcher()`                     | （可选）用于创建快捷启动API服务的按钮控件UI, 直接定义按钮并绑定触发事件，无需返回值 |
| `_UI()`                              | 必须实现，构建 UI 界面布局。你无需定义生成按钮`self.btn`。 **必须返回包含gradio组件的列表作为参数输入。**                          |

---
### 🌍 Traducteur（用于字幕翻译插件）

`Traducteur` (**继承自`Base_Component`**)是用于构建翻译插件的基类，适用于处理多段字幕文本的自动翻译流程。它封装了批处理任务构建逻辑，并要求开发者实现核心的 `api()` 方法。

**推荐覆写的方法：**

| 方法                                                                       | 说明                                                              |
| ------------------------------------------------------------------------ | --------------------------------------------------------------- |
|`__init__`等基类方法 |见`Base_Component` |
| `construct_tasks(subtitles, batch_size=1)`                               | 将字幕条目分批组织为任务列表，默认按 `batch_size` 聚合。每个任务是一个字符串列表，内容为清洗后的字幕文本。可以选择覆写。    |
| `api(tasks, target_lang, interrupt_flag, *args, file_name="", **kwargs)` | 必须实现。处理翻译逻辑，接收 `construct_tasks()` 返回的任务列表，并返回翻译后的字符串列表（可以附加消息）。 |

---

#### 📦 self.construct_tasks(subtitles, batch_size=1)

默认实现是用于将字幕列表拆分为批次任务，但愿能提升一点上下文联系。每个任务是一小组字符串，最终以 `list[list[str]]` 返回：

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

**参数说明：**

| 参数           | 说明                             |
| ------------ | ------------------------------ |
| `subtitles`  | 输入字幕对象列表，每项需具备 `.text` 字段。     |
| `batch_size` | 每批任务的字幕数目。默认值为 `1`，代表一条字幕一组。   |
| 返回值          | `list[list[str]]`，每组作为翻译任务的输入。 |

---

#### 🧠 self.api(...)

插件核心翻译逻辑的实现方法，必须由派生类覆写。

**参数说明：**

| 参数               | 说明                                                           |
| ---------------- | ------------------------------------------------------------ |
| `tasks`          | 来自 `construct_tasks()` 的任务批次，是一个二维字符串列表。                     |
| `target_lang`    | 目标语言的字符串表示，未来可能有所调整。["中文", "English", "日本語", "한국어", "Français"]                        |
| `interrupt_flag` | 中断控制对象，类型为 `Flag`，可使用 `interrupt_flag.is_set()` 判断是否被用户取消任务。 |
| `*args`          | 从 `_UI()` 方法中返回的参数输入。用于传入用户输入值，如模型选项等。                |
| `file_name`      | 可选文件名，用于在进度提示中标识当前处理的字幕文件。                                   |
| `**kwargs`       | 其他可选参数，现在暂时没用。                                                |

**返回值：**

* 必须返回一个 `list[str]`，对应翻译后的字幕文本（按任务顺序展开）；
* 也可返回 `tuple[list[str], str]`，附带提示信息（如 `"模型出现了幻觉"`）。

---

#### 🚦 Flag：中断控制建议工具

框架提供了 `Flag` 类用于中断任务，翻译插件应在耗时操作中定期检查是否收到中断请求：

```python
if interrupt_flag.is_set():
    return []
```

该标志由用户控制任务取消按钮触发，开发者无需自行实现逻辑，只需检查并响应即可。

---

## 4. 插件注册机制

### 📁 插件目录结构（Plugin Directory Structure）

* 所有插件模块应放置于 `Sava_Extensions/<插件类型>/<插件名称>/` 目录中。  
* 每个插件必须包含 `__init__.py` 文件，文件中必须定义 `register(context)` 函数。

示例：

```
Sava_Extensions/
└── tts_engine/
    ├── Custom_OLD/
    │   ├── __init__.py
    │   └── custom.py
    └── MyPlugin/
        ├── __init__.py
        └── ...
```

---

插件需要通过 `__init__.py` 文件中的 `register(context)` 方法进行注册：

```python
def register(context):    
    globals().update(context)  # 将依赖注入模块命名空间
    from .custom import Custom
    return Custom()  # 返回插件类实例
```

框架将调用 `register()` 并传入依赖上下文。

---

## 5. 插件 UI 构建机制

每个插件必须通过实现 `_UI()` 方法来定义自己的 UI 界面结构。该方法通常返回一组 Gradio 组件，例如：

```python
def _UI(self):
    with gr.Column():
        self.text_input = gr.Textbox(label="Input Text")
        self.gen_btn = gr.Button("Generate")
    return [self.text_input]    #TTS/翻译类插件需要返回参数列表
```

`getUI()` 方法已由基类管理，内部确保 UI 只构建一次，并可自动注入触发按钮（如 `gen_btn`）。

---

## 6. 共享配置项：Shared_Option

`Shared_Option` 用于 **声明与注册全局共享配置项**。
插件或核心组件可以把自己的可配置参数统一暴露给「设置面板」，并在运行期通过 `Settings` 对象取回用户设定的值。

---

### 1. 工作流程概览

1. **声明**
   在插件内部创建 `Shared_Option` 实例，描述该配置项的键名、默认值、UI 组件类型与（可选）校验函数。

2. **注册**
   将所有 `Shared_Option` 对象以**列表**形式返回给 `register_settings()`，框架会自动生成对应的 Gradio 表单控件，并把用户输入写入全局 `Settings`。

3. **读取**
   在插件任意位置，通过 `config.query("your_key", default)` 读取用户设置；或在校验函数里使用第二个参数 `config` 访问其他共享项。

---

### 2. 构造函数参数

| 参数                                                  | 说明                                                                       |
| --------------------------------------------------- | ------------------------------------------------------------------------ |
| `key: str`                                          | **唯一键名**，用于存储与检索该配置值。                                                    |
| `default_value: Any`                                | 默认值。初次运行或重置时生效。                                                          |
| `gr_component_type: gr.components.FormComponent`    | 指定 Gradio 表单组件类型（`gr.Textbox`、`gr.Slider`、`gr.Dropdown` 等）。              |
| `validator: Callable[[Any, Settings], Any] \| None` | （可选）验证 / 转换函数。接收 **用户输入值** 与 **全局 Settings**，必须返回最终写入设置的值；如发现非法输入，可抛出异常。 |
| `**gr_kwargs`                                       | 其他将直接传给组件构造函数的关键字参数，如 `label`、`choices`、`interactive` 等。                 |

---

### 3. 典型示例
---
```python
# 验证函数，第一个参数接收当前设置项，第二个参数为全局设置项
def validate_path(value, config):   
    if not os.path.isfile(value):
        raise ValueError("Invalid path")    # 对非法参数你可以抛出异常，这将让此项回到默认值
    else:
        value = value.strip()   #也可以直接对值进行处理，也可以通过config访问全局设置。
    return value # 必须返回修改后的值，无论是否修改过

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
* **验证器** `validate_path` 在保存前执行；若抛出异常，该项将重置为默认值。你可以对值进行修改。
* 对同一配置项，如需跨插件共享，可 **使用相同的 `key`**，不同插件读取的将是同一存储值。
* UI 组件所有属性 (`choices`, `value`, `visible` 等) 均可通过 `gr_kwargs` 直接传入，做到「声明即 UI」。
* **提示**：在 `validator` 内也可以调用 `config.query(key,default_value)` 访问其他共享项，实现 **相互依赖校验**（例如多个路径必须位于同一磁盘分区）。
---
### 获取更新后的值
```python
class GSV(TTSProjet):
    def update_cfg(self, config: Settings):
        self.gsv_fallback = config.query("gsv_fallback")
        self.gsv_dir = config.query("gsv_dir")
        self.gsv_pydir = config.query("gsv_pydir")
        self.gsv_args = config.query("gsv_args")
        super().update_cfg(config)
```
按照以上规范即可将任意插件配置项无缝接入到全局设置系统，实现 **统一 UI、集中管理、即时生效**。

---
