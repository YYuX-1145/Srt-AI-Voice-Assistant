import os
import gradio as gr
import json
import Sava_Utils
import time
import os
import sys
import platform

from . import logger, i18n

current_path = os.environ.get("current_path")

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
        theme: str = "default",
        bv2_pydir: str = "",
        bv2_dir: str = "",
        bv2_args: str = "",
        gsv_fallback: bool = False,
        gsv_pydir: str = "",
        gsv_dir: str = "",
        gsv_args: str = "",
        ms_region: str = "eastasia",
        ms_key: str = "",
        ms_lang_option: str = "zh",
        ollama_url: str = "http://localhost:11434",
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
        self.num_edit_rows = int(num_edit_rows)
        self.theme = theme
        self.bv2_pydir = bv2_pydir
        self.bv2_dir = bv2_dir
        self.bv2_args = bv2_args
        self.gsv_fallback = gsv_fallback
        self.gsv_pydir = gsv_pydir
        self.gsv_dir = gsv_dir
        self.gsv_args = gsv_args
        self.ms_region = ms_region
        self.ms_key = ms_key
        self.ms_lang_option = ms_lang_option
        self.ollama_url = ollama_url
        # detect python envs####
        if bv2_pydir != "":
            if os.path.exists(bv2_pydir):
                self.bv2_pydir = os.path.abspath(bv2_pydir)
            else:
                gr.Warning(f"{i18n('Error, Invalid Path')}:{self.bv2_pydir }")
                self.bv2_pydir = ""
        else:
            if os.path.exists(os.path.join(current_path, "venv\\python.exe")) and "VITS2" in current_path.upper():
                self.bv2_pydir = os.path.join(current_path, "venv\\python.exe")
                logger.info(f"{i18n('Env detected')}: Bert-VITS2")
            else:
                self.bv2_pydir = ""

        if gsv_pydir != "":
            if os.path.exists(gsv_pydir):
                self.gsv_pydir = os.path.abspath(gsv_pydir)
            else:
                gr.Warning(f"{i18n('Error, Invalid Path')}:{self.gsv_pydir }")
                self.gsv_pydir = ""
        else:
            if os.path.exists(os.path.join(current_path, "runtime\\python.exe")) and "GPT" in current_path.upper():
                self.gsv_pydir = os.path.join(current_path, "runtime\\python.exe")
                logger.info(f"{i18n('Env detected')}: GPT-SoVITS")
            else:
                self.gsv_pydir = ""
        ###################
        if self.bv2_pydir != "" and bv2_dir == "":
            self.bv2_dir = os.path.dirname(os.path.dirname(self.bv2_pydir))
        if self.gsv_pydir != "" and gsv_dir == "":
            self.gsv_dir = os.path.dirname(os.path.dirname(self.gsv_pydir))

    def to_list(self):
        val = self.to_dict()
        return [val[x] for x in list(val.keys())]

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
        os.system(f"taskkill /PID {os.getpid()} /F")


class Settings_UI:
    def __init__(self, componments: list):
        self.componments = componments
        self.ui = False
        self._apply_to_componments()

    def _apply_to_componments(self):
        for i in self.componments:
            i.update_cfg(config=Sava_Utils.config)

    def save_settngs(self, *args):
        current_edit_rows = Sava_Utils.config.num_edit_rows
        Sava_Utils.config = Settings(*args)
        Sava_Utils.config.save()
        self._apply_to_componments()
        if Sava_Utils.config.num_edit_rows != current_edit_rows:
            Sava_Utils.config.num_edit_rows = current_edit_rows
        logger.info(i18n('Settings saved successfully!'))
        gr.Info(i18n('Settings saved successfully!'))
        return Sava_Utils.config.to_list()

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
        gr.Markdown(f"⚠️{i18n('Click Apply & Save for these settings to take effect.')}⚠️")
        with gr.Group():
            gr.Markdown(value=i18n('General'))
            self.language = gr.Dropdown(label="Language (Requires a restart)", value=Sava_Utils.config.language, allow_custom_value=False, choices=['Auto', "en_US", "zh_CN", "ja_JP", "ko_KR", "fr_FR"])
            with gr.Row():
                self.server_port = gr.Number(label=i18n('The port used by this program, 0=auto. When conflicts prevent startup, use -p parameter to specify the port.'), value=Sava_Utils.config.server_port, minimum=0, scale=3)
                self.LAN_access = gr.Checkbox(label=i18n('Enable LAN access. Restart to take effect.'), value=Sava_Utils.config.LAN_access, scale=1)
            with gr.Row():
                self.overwrite_workspace = gr.Checkbox(label=i18n('Overwrite history records with files of the same name instead of creating a new project.'), value=Sava_Utils.config.overwrite_workspace, interactive=True)
                self.clear_cache = gr.Checkbox(label=i18n('Clear temporary files on each startup (which will also erase history records).'), value=Sava_Utils.config.clear_tmp, interactive=True)
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
            self.num_edit_rows = gr.Number(label=i18n('Edit Panel Row Count (Requires a restart)'), minimum=1, maximum=20, value=Sava_Utils.config.num_edit_rows)
            self.theme = gr.Dropdown(choices=gradio_hf_hub_themes, value=Sava_Utils.config.theme, label=i18n('Theme (Requires a restart)'), interactive=True)
        with gr.Accordion(i18n('Submodule Settings'),open=False):
            with gr.Group():
                gr.Markdown(value="BV2")
                self.bv2_pydir_input = gr.Textbox(label=i18n('Python Interpreter Path for BV2'), interactive=True, value=Sava_Utils.config.bv2_pydir)
                self.bv2_dir_input = gr.Textbox(label=i18n('Root Path of BV2'), interactive=True, value=Sava_Utils.config.bv2_dir)
                self.bv2_args = gr.Textbox(label=i18n('Start Parameters'), interactive=True, value=Sava_Utils.config.bv2_args)
            with gr.Group():
                gr.Markdown(value="GSV")
                self.gsv_fallback = gr.Checkbox(value=False, label=i18n('Downgrade API version to v1'), interactive=True)
                self.gsv_pydir_input = gr.Textbox(label=i18n('Python Interpreter Path for GSV'), interactive=True, value=Sava_Utils.config.gsv_pydir)
                self.gsv_dir_input = gr.Textbox(label=i18n('Root Path of GSV'), interactive=True, value=Sava_Utils.config.gsv_dir)
                self.gsv_args = gr.Textbox(label=i18n('Start Parameters'), interactive=True, value=Sava_Utils.config.gsv_args)
            with gr.Group():
                gr.Markdown(value="Azure-TTS(Microsoft)")
                self.ms_region = gr.Textbox(label="Server Region", interactive=True, value=Sava_Utils.config.ms_region)
                self.ms_key = gr.Textbox(label=i18n('KEY Warning: Key is stored in plaintext. DO NOT send the key to others or share your configuration file!'), interactive=True, value=Sava_Utils.config.ms_key)
                self.ms_lang_option = gr.Textbox(label=i18n('Select required languages, separated by commas or spaces.'), interactive=True, value=Sava_Utils.config.ms_lang_option)
            with gr.Group():
                gr.Markdown(value=i18n('Translation Module'))
                self.ollama_url = gr.Textbox(label=i18n('Default Request Address for Ollama'), interactive=True, value=Sava_Utils.config.ollama_url)
        self.clear_cache_btn = gr.Button(value=i18n('Clear temporary files'), variant="primary")
        self.clear_cache_btn.click(Sava_Utils.utils.clear_cache, inputs=[], outputs=[])        
        self.save_settings_btn = gr.Button(value=i18n('Apply & Save'), variant="primary")
        self.restart_btn = gr.Button(value=i18n('Restart UI'), variant="stop")

        componments_list = [
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
            self.theme,
            self.bv2_pydir_input,
            self.bv2_dir_input,
            self.bv2_args,
            self.gsv_fallback,
            self.gsv_pydir_input,
            self.gsv_dir_input,
            self.gsv_args,
            self.ms_region,
            self.ms_key,
            self.ms_lang_option,
            self.ollama_url,
        ]

        self.save_settings_btn.click(self.save_settngs, inputs=componments_list, outputs=componments_list)
        self.restart_btn.click(restart, [], [])
