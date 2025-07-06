import requests
import gradio as gr
import time
import os
from . import *
current_path = os.environ.get("current_path")


class Custom(TTSProjet):
    def __init__(self, config=None):
        self.custom_api_list = []
        self.refresh_custom_api_list()
        super().__init__("custom", config, title=i18n('Custom API'))

    def api(self, func, text):
        return func(text)

    def _UI(self):
        with gr.Column():
            gr.Markdown(value=MANUAL.getInfo("help_custom"))                
            self.choose_custom_api = gr.Dropdown(label=i18n('Choose Custom API Code File'), choices=self.custom_api_list, value=self.custom_api_list[0] if self.custom_api_list != [] else '', allow_custom_value=False, scale=4)
            with gr.Row():
                self.gen_btn = gr.Button(value=i18n('Generate Audio'), variant="primary", scale=8)
                self.refresh_custom_btn = gr.Button(value="🔄️", scale=1, min_width=40)                    
            self.refresh_custom_btn.click(self.refresh_custom_api_list, outputs=[self.choose_custom_api])
        return [self.choose_custom_api]

    def before_gen_action(self, custom_api_path, temp_namesp, **kwargs):
        # print(args)
        logger.info(f"Exec: custom_api_path {custom_api_path}")
        with open(os.path.join(current_path, "SAVAdata", "presets", custom_api_path), "r", encoding="utf-8") as f:
            code = f.read()
        exec(code, temp_namesp)

    def save_action(self, custom_api_path, temp_namesp, text):
        return self.api(temp_namesp["custom_api"], text)

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
        return (custom_api, dict()), kwargs  #
