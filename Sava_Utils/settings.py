from typing import Literal, Callable, Any
import os
import gradio as gr
import json
import Sava_Utils
import time
import traceback
import sys
import platform
import shutil
import numpy as np
from collections import defaultdict
from . import logger, i18n


current_path = os.environ.get("current_path")


EXT_TYPES = ["tts_engine", "translator", "extension"]
EXT_TYPES_TITLE = {
    "tts_engine": i18n("TTS Engine"),
    "translator": i18n("Translator"),
    "extension": i18n("Extensions"),
}
EXT_TYPES_TITLE_REV = {v: k for k, v in EXT_TYPES_TITLE.items()}
# https://huggingface.co/datasets/freddyaboulton/gradio-theme-subdomains/resolve/main/subdomains.json
gradio_hf_hub_themes = [
    "default",
    "base",
    "glass",
    "soft",
    "gradio/monochrome",
    "gradio/seafoam",
    "gradio/dracula_test",
    "abidlabs/dracula_test",
    "abidlabs/Lime",
    "abidlabs/pakistan",
    "Ama434/neutral-barlow",
    "dawood/microsoft_windows",
    "finlaymacklon/smooth_slate",
    "Franklisi/darkmode",
    "freddyaboulton/dracula_revamped",
    "freddyaboulton/test-blue",
    "gstaff/xkcd",
    "Insuz/Mocha",
    "Insuz/SimpleIndigo",
    "JohnSmith9982/small_and_pretty",
    "nota-ai/theme",
    "nuttea/Softblue",
    "ParityError/Anime",
    "reilnuud/polite",
    "remilia/Ghostly",
    "rottenlittlecreature/Moon_Goblin",
    "step-3-profit/Midnight-Deep",
    "Taithrah/Minimal",
    "ysharma/huggingface",
    "ysharma/steampunk",
    "NoCrypt/miku",
]


class Settings:
    def __init__(
        self,
        language: str = "Auto",
        server_port: int = 0,
        LAN_access: bool = False,
        overwrite_workspace: bool = False,
        clear_tmp: bool = False,
        concurrency_count: int = 2,
        server_mode: bool = False,
        min_interval: float = 0.3,
        max_accelerate_ratio: float = 1.0,
        output_sr: int = 0,
        remove_silence: bool = False,
        num_edit_rows: int = 7,
        export_spk_pattern: str = "",
        theme: str = "default",
        shared_opts: dict = dict(),
        **kwargs,
    ):
        self.language = language
        self.server_port = int(server_port)
        self.LAN_access = LAN_access
        self.overwrite_workspace = overwrite_workspace
        self.clear_tmp = clear_tmp
        self.concurrency_count = int(concurrency_count)
        self.server_mode = server_mode
        self.min_interval = min_interval
        self.max_accelerate_ratio = max_accelerate_ratio
        self.output_sr = int(output_sr)
        self.remove_silence = remove_silence
        self.num_edit_rows = max(int(num_edit_rows), 1)
        self.export_spk_pattern = export_spk_pattern
        self.theme = theme
        self.shared_opts = shared_opts

    def query(self, key: str, default=None):
        return self.shared_opts.get(key, default)

    def to_list(self):
        return list(self.to_dict().values())

    def to_dict(self):
        return self.__dict__

    def save(self):
        dic = self.to_dict()
        os.makedirs(os.path.join(current_path, "SAVAdata"), exist_ok=True)
        with open(os.path.join(current_path, "SAVAdata", "config.json"), "w", encoding="utf-8") as f:
            json.dump(dic, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, dict):
        return cls(**dict)


def load_cfg():
    config_path = os.path.join(current_path, "SAVAdata", "config.json")
    if os.path.exists(config_path):
        try:
            config = Settings.from_dict(json.load(open(config_path, encoding="utf-8")))
        except Exception as e:
            config = Settings()
            logger.warning(f"Failed to load settings, reset to default: {e}")
    else:
        config = Settings()
    return config


class Shared_Options:

    def __init__(self, key: str, default_value: Any, gr_component_type: gr.components.FormComponent, validator: Callable[[Any, Settings], Any] | None = None, **gr_kwargs):
        """
        Example:
            def validate_path(value,config):
                # (Optional) define a validator function, throwing exceptions is acceptable here.
                # You can access shared options via config.
                if not os.path.isfile(value):
                    value = ""
                return value    # must return modified value.

            Shared_Options(
                "gsv_pydir",        # key
                "",                 # default value
                gr.Textbox,         # gradio component type
                validate_path,    # function

                # These keyword arguments below will be passed to the class constructors of gr.FormComponent
                label=i18n('Python Interpreter Path for GPT-SoVITS'),
                interactive=True,
            )
        """
        self.key = key
        self.default_value = default_value
        self.gr_component_type = gr_component_type
        self.validator = validator
        self.gr_kwargs = gr_kwargs


def rm_workspace(name):
    try:
        shutil.rmtree(os.path.join(current_path, "SAVAdata", "workspaces", name))
        gr.Info(f"{name} {i18n('was removed successfully.')}")
        time.sleep(0.1)
        return gr.update(visible=False), gr.update(visible=False)
    except Exception as e:
        gr.Warning(f"{i18n('An error occurred')}: {str(e)}")
        return gr.update(), gr.update()


def restart():
    gr.Warning(i18n('Restarting...'))
    time.sleep(0.5)
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
    if os.environ.get('exe') != 'True':
        os.execl(sys.executable, f'"{sys.executable}"', f'"{sys.argv[0]}"')
    else:
        try:
            a = os.environ["_PYI_APPLICATION_HOME_DIR"]
            b = os.environ["_PYI_ARCHIVE_FILE"]
            c = os.environ["_PYI_PARENT_PROCESS_LEVEL"]
            os.unsetenv("_PYI_APPLICATION_HOME_DIR")
            os.unsetenv("_PYI_ARCHIVE_FILE")
            os.unsetenv("_PYI_PARENT_PROCESS_LEVEL")
            Sava_Utils.utils.rc_open_window(command=f"{sys.executable}", dir=current_path)
            os.environ["_PYI_APPLICATION_HOME_DIR"] = a
            os.environ["_PYI_ARCHIVE_FILE"] = b
            os.environ["_PYI_PARENT_PROCESS_LEVEL"] = c
        except Exception as e:
            gr.Warning(f"{i18n('An error occurred. Please restart manually!')} {str(e)}")
        os.system(f"taskkill /PID {os.getpid()} /F && exit")


from .base_component import Base_Component


class Settings_Manager:
    def __init__(self, components: dict[int : dict[str:Base_Component]]):
        self.components = components
        self.ui = False
        self.shared_opts_info: list[str] = []
        self.shared_opts_validators: dict[str:Callable] = {}

        # get default value and set up validators
        default_shared_opts: dict[str:Any] = dict()
        for lst in [self.components[1].values(), list(self.components[2]["translation_module"].TRANSLATORS.values()), self.components[3].values()]:
            for item in lst:
                for opt in item.register_settings():
                    if opt.key in default_shared_opts:
                        gr.Warning(f"{i18n('Duplicate shared option from extension')}: {opt.key}")
                        logger.warning(f"{i18n('Duplicate shared option from extension')}: {opt.key}")
                    default_shared_opts[opt.key] = opt.default_value
                    if opt.validator:
                        self.shared_opts_validators[opt.key] = opt.validator
        new_shared_opts = dict(default_shared_opts)
        new_shared_opts.update(Sava_Utils.config.shared_opts)
        Sava_Utils.config.shared_opts = new_shared_opts
        for key, val in self.shared_opts_validators.items():
            try:
                Sava_Utils.config.shared_opts[key] = val(Sava_Utils.config.shared_opts[key], Sava_Utils.config)
            except:
                Sava_Utils.config.shared_opts[key] = default_shared_opts[key]
                traceback.print_exc()
        self._apply_to_components()

    def _apply_to_components(self):
        for item in self.components.values():
            for i in item.values():
                try:
                    i.update_cfg(config=Sava_Utils.config)
                except:
                    name = i.dirname if hasattr(i, "dirname") else str(type(i))
                    logger.error(f"{i18n('Failed to apply settings to component')}: {name}")
                    traceback.print_exc()

    def save_settngs(self, *args):
        shared_opts_dict = dict()
        for key, value in zip(reversed(self.shared_opts_info), reversed(args)):
            shared_opts_dict[key] = value  # new value
        old_opts = Sava_Utils.config.shared_opts
        Sava_Utils.config.shared_opts = shared_opts_dict
        for key, value in self.shared_opts_validators.items():
            try:
                shared_opts_dict[key] = value(shared_opts_dict[key], Sava_Utils.config)
            except:
                shared_opts_dict[key] = old_opts[key]
                traceback.print_exc()
        current_edit_rows = Sava_Utils.config.num_edit_rows
        Sava_Utils.config = Settings(*args[: -len(self.shared_opts_info)], shared_opts_dict)
        Sava_Utils.config.save()
        if Sava_Utils.config.num_edit_rows != current_edit_rows:
            Sava_Utils.config.num_edit_rows = current_edit_rows
        self._apply_to_components()
        logger.info(i18n('Settings saved successfully!'))
        gr.Info(i18n('Settings saved successfully!'))
        all_vals = list(Sava_Utils.config.to_list()[:-1]) + [Sava_Utils.config.shared_opts[key] for key in self.shared_opts_info]
        return all_vals

    def get_ext_tab(self):
        rows = []
        comp_dict = {
            "tts_engine": [i.dirname for i in self.components[1].values() if hasattr(i, "dirname")],
            "translator": [i.dirname for i in self.components[2]["translation_module"].TRANSLATORS.values() if hasattr(i, "dirname")],
            "extension": [i.dirname for i in self.components[3].values() if hasattr(i, "dirname")],
        }
        config_path = os.path.join(current_path, "Sava_Extensions/extensions_config.json")
        if os.path.isfile(os.path.join(current_path, "Sava_Extensions/extensions_config.json")):
            ext_config = defaultdict(dict, json.load(open(config_path, encoding="utf-8")))
        else:
            ext_config = defaultdict(dict)
        for ext_type in EXT_TYPES:
            os.makedirs(os.path.join(current_path, "Sava_Extensions", ext_type), exist_ok=True)
            for i in [x for x in os.listdir(os.path.join(current_path, "Sava_Extensions", ext_type)) if os.path.isdir(os.path.join(current_path, "Sava_Extensions", ext_type, x))]:
                rows.append([i, EXT_TYPES_TITLE[ext_type], i18n('Running') if i in comp_dict[ext_type] else "", ext_config[ext_type].get(i, True)])
        return np.array(rows)

    def save_ext_tab(self, tab):
        cfg = defaultdict(dict)
        for i in tab:
            cfg[EXT_TYPES_TITLE_REV.get(i[1], "extension")][i[0]] = True if i[-1] in [True, 'True', 'true'] else False  # gradio bug
        with open(os.path.join(current_path, "Sava_Extensions/extensions_config.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return self.get_ext_tab()

    def getUI(self):
        if not self.ui:
            self.ui = True
            return self._UI()
        else:
            raise "ERR"

    def _UI(self):
        if Sava_Utils.config.server_mode:
            gr.Markdown(i18n('Settings have been disabled!'))
            return []
        with gr.Row():
            self.save_settings_btn = gr.Button(value=i18n('Apply & Save'), variant="primary", scale=2)
            self.restart_btn = gr.Button(value=i18n('Restart UI'), variant="stop")
        gr.Markdown(f"⚠️{i18n('Click Apply & Save for these settings to take effect.')}⚠️")
        with gr.TabItem(i18n('General')):
            with gr.Group():
                self.language = gr.Dropdown(label="Language (Requires a restart)", value=Sava_Utils.config.language, allow_custom_value=False, choices=['Auto', "en_US", "zh_CN", "ja_JP", "ko_KR", "fr_FR"])
                with gr.Row():
                    self.server_port = gr.Number(label=i18n('The port used by this program, 0=auto. When conflicts prevent startup, use -p parameter to specify the port.'), value=Sava_Utils.config.server_port, minimum=0)
                    self.LAN_access = gr.Checkbox(label=i18n('Enable LAN access. Restart to take effect.'), value=Sava_Utils.config.LAN_access)
                with gr.Row():
                    self.overwrite_workspace = gr.Checkbox(label=i18n('Overwrite history records with files of the same name instead of creating a new project.'), value=Sava_Utils.config.overwrite_workspace, interactive=True)
                    self.clear_cache = gr.Checkbox(label=i18n('Clear temporary files on each startup'), value=Sava_Utils.config.clear_tmp, interactive=True)
                with gr.Row():
                    self.concurrency_count = gr.Number(label=i18n('Concurrency Count'), value=Sava_Utils.config.concurrency_count, minimum=2, interactive=True)
                    self.server_mode = gr.Checkbox(label=i18n('Server Mode can only be enabled by modifying configuration file or startup parameters.'), value=Sava_Utils.config.server_mode, interactive=False)
                with gr.Column():
                    with gr.Row():
                        self.min_interval = gr.Slider(label=i18n('Minimum voice interval (seconds)'), minimum=0, maximum=3, value=Sava_Utils.config.min_interval, step=0.1)
                        self.max_accelerate_ratio = gr.Slider(label=i18n('Maximum audio acceleration ratio (requires ffmpeg)'), minimum=1, maximum=2, value=Sava_Utils.config.max_accelerate_ratio, step=0.01)
                    with gr.Row():
                        self.output_sr = gr.Dropdown(label=i18n('Sampling rate of output audio, 0=Auto'), value='0', allow_custom_value=True, choices=['0', '16000', '22050', '24000', '32000', '44100', '48000'])
                        self.remove_silence = gr.Checkbox(label=i18n('Remove inhalation and silence at the beginning and the end of the audio'), value=Sava_Utils.config.remove_silence, interactive=True)
                    with gr.Row():
                        self.num_edit_rows = gr.Number(label=i18n('Edit Panel Row Count (Requires a restart)'), minimum=1, maximum=50, value=Sava_Utils.config.num_edit_rows)
                        self.export_spk_pattern = gr.Text(label=i18n('Export subtitles with speaker name. Fill in your template to enable.'), placeholder=r"{#NAME}: {#TEXT}", value=Sava_Utils.config.export_spk_pattern)
                self.theme = gr.Dropdown(choices=gradio_hf_hub_themes, value=Sava_Utils.config.theme, label=i18n('Theme (Requires a restart)'), interactive=True, allow_custom_value=True)

        with gr.TabItem(i18n('Storage Management')):
            self.clear_cache_btn = gr.Button(value=i18n('Clear temporary files'), variant="primary")
            self.clear_cache_btn.click(Sava_Utils.utils.clear_cache, inputs=[], outputs=[])
            self.workspaces_archieves_state = gr.State(value=list())
            self.list_workspaces_btn = gr.Button(value=i18n('List Archives'), variant="primary")
            self.list_workspaces_btn.click(Sava_Utils.edit_panel.refworklist, outputs=[self.workspaces_archieves_state])
            workspaces_manager_ui_empty_md = f"### <center>{i18n('No Archives Found. Click the <List Archives> button to refresh.')}</center>"

            @gr.render(inputs=self.workspaces_archieves_state)
            def workspaces_manager_ui(x: list):
                if len(x) == 0:
                    gr.Markdown(value=workspaces_manager_ui_empty_md)
                    return
                with gr.Group():
                    for i in x:
                        with gr.Row(equal_height=True):
                            item = gr.Textbox(value=i, show_label=False, interactive=False, scale=8)
                            b = gr.Button(value="🗑️", variant="stop", scale=1, min_width=40)
                            b.click(rm_workspace, inputs=[item], outputs=[item, b])

        components_list = [
            self.language,
            self.server_port,
            self.LAN_access,
            self.overwrite_workspace,
            self.clear_cache,
            self.concurrency_count,
            self.server_mode,
            self.min_interval,
            self.max_accelerate_ratio,
            self.output_sr,
            self.remove_silence,
            self.num_edit_rows,
            self.export_spk_pattern,
            self.theme,
        ]

        with gr.TabItem(i18n('Submodule Settings')):
            EXT_POINTER = {
                "tts_engine": self.components[1].values(),
                "translator": self.components[2]["translation_module"].TRANSLATORS.values(),
                "extension": self.components[3].values(),
            }
            for ext_type in EXT_TYPES:
                with gr.TabItem(EXT_TYPES_TITLE[ext_type]):
                    for comp in EXT_POINTER[ext_type]:
                        opt_list = comp.register_settings()
                        if opt_list:
                            with gr.TabItem(comp.name):
                                try:
                                    for c in opt_list:
                                        c.gr_kwargs["value"] = Sava_Utils.config.query(c.key, c.default_value)
                                        components_list.append(c.gr_component_type(**c.gr_kwargs))
                                        self.shared_opts_info.append(c.key)
                                except Exception as e:
                                    print(e)
        with gr.TabItem(i18n('Extension Management')):
            ext_mgr_table = gr.Dataframe(
                value=self.get_ext_tab(),
                show_label=False,
                headers=[i18n('Name'), i18n('Type'), i18n('Status'), i18n('Enabled')],
                column_widths=['40%', '20%', '20%', '20%'],
                datatype=["str", "str", "str", "bool"],
                col_count=(4, 'fixed'),
                row_count=(0, 'fixed'),
                type="numpy",
                static_columns=[0, 1, 2],
                interactive=True,
            )
            save_ext_table_btn = gr.Button(i18n('Save'), variant="primary")
            save_ext_table_btn.click(self.save_ext_tab, inputs=[ext_mgr_table], outputs=[ext_mgr_table])

        self.save_settings_btn.click(self.save_settngs, inputs=components_list, outputs=components_list)
        self.restart_btn.click(restart, [], [])
