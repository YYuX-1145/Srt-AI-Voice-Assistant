from . import TTSProjet
import requests
import gradio as gr
from .. import logger, i18n, MANUAL
import time
import os

current_path = os.environ.get("current_path")


class Custom(TTSProjet):
    def __init__(self, config):
        self.custom_api_list = []
        self.refresh_custom_api_list()
        super().__init__("custom", config)

    def api(self, text):
        return custom_api(text)

    def _UI(self):
        with gr.TabItem(i18n('Custom API')):
            with gr.Column():
                gr.Markdown(value=MANUAL.getInfo("help_custom"))
                self.choose_custom_api = gr.Dropdown(label=i18n('Choose Custom API Code File'), choices=self.custom_api_list, value=self.custom_api_list[0] if self.custom_api_list != [] else '', allow_custom_value=False)
                self.refresh_custom_btn = gr.Button(value="🔄️")
                self.gen_btn4 = gr.Button(value=i18n('Generate Audio'), variant="primary", visible=True)
                self.refresh_custom_btn.click(self.refresh_custom_api_list, outputs=[self.choose_custom_api])
        return []

    def before_gen_action(self, *args, **kwargs):
        # print(args)
        custom_api_path = args[0]
        logger.info(f"Exec: custom_api_path {custom_api_path}")
        with open(os.path.join(current_path, "SAVAdata", "presets", custom_api_path), "r", encoding="utf-8") as f:
            code = f.read()
        exec(code, globals())

    def save_action(self, *args, text):
        return self.api(text)

    def refresh_custom_api_list(self):
        self.custom_api_list = ['None']
        try:
            preset_dir = os.path.join(current_path, "SAVAdata", "presets")
            if os.path.isdir(preset_dir):
                self.custom_api_list += [i for i in os.listdir(preset_dir) if i.endswith(".py")]
            else:
                logger.info(i18n('No custom API code file found.'))
        except Exception as e:
            self.custom_api_list = ['None']
            err = f"Error: {e}"
            logger.error(err)
            gr.Warning(err)
        time.sleep(0.1)
        return gr.update(value="None", choices=self.custom_api_list)

    def arg_filter(self, *args):
        input_file, fps, offset, workers, custom_api = args
        if custom_api in [None, 'None', '']:
            gr.Info(i18n('Please select a valid custom API code file!'))
            raise Exception(i18n('Please select a valid custom API code file!'))
        kwargs = {'in_files': input_file, 'fps': fps, 'offset': offset, 'proj': "custom", 'max_workers': workers}
        return (custom_api, None), kwargs  #
