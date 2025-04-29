import requests
import gradio as gr
import json
import re
import subprocess
from . import Traducteur
from ..utils import rc_open_window
from .. import logger, i18n


class Ollama(Traducteur):
    def __init__(self, config=None):
        self.models = []
        super().__init__("ollama", config)

    def update_cfg(self, config):
        self.ollama_url = config.ollama_url
        super().update_cfg(config)

    def get_models(self, url):
        try:
            if self.server_mode:
                result = subprocess.run("ollama list", capture_output=True, text=True)  # consider using awk
                lines = result.stdout.strip().split("\n")[1:]
                self.models = [i.split()[0] for i in lines]
                # print(self.models)
                return gr.update(choices=self.models, value=self.models[0] if len(self.models) != 0 else None)
            if url in [None, "", "Default"]:
                url = self.ollama_url
            response = requests.get(f'{url}/api/tags')
            response.raise_for_status()
            self.models.clear()
            for item in json.loads(response.content)["models"]:
                self.models.append(item["name"])
        except Exception as e:
            gr.Warning(f"{i18n('Failed to get model list from Ollama')}: {str(e)}")
            logger.error(f"{i18n('Failed to get model list from Ollama')}: {str(e)}")
        return gr.update(choices=self.models, value=self.models[0] if len(self.models) != 0 else None)

    def unload_model(self, model):
        if model in [None, [], ""] or self.server_mode:
            gr.Warning(i18n('You must specify the model!'))
            return None
        rc_open_window(f"ollama stop {model} && exit")

    def api(self, text, target_lang, model_name, url, prompt):
        if url in [None, "", "Default"] or self.server_mode:
            url = self.ollama_url
        if model_name in [None, [], ""]:
            raise ValueError(i18n('You must specify the model!'))
        if prompt:
            prompt = prompt + ' ' + text
        else:
            prompt = f"Directly translate the following content to {target_lang} WITHOUT replying with any additional notes or questions:{text}"
        data_json = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
        }
        # print(data_json["prompt"])
        response = requests.post(url=f'{url}/api/generate', json=data_json)
        response.raise_for_status()
        return re.sub(r'<think>.*?</think>', '', json.loads(response.content)["response"], flags=re.DOTALL).strip()

    def _UI(self, *inputs, output_info, output_files):
        from ..subtitle_translation import start_translation

        if self.server_mode:
            self.get_models("")
        with gr.Column():
            gr.Markdown(i18n('OLLAMA_NOTICE'))
            self.select_model = gr.Dropdown(label=i18n('Select Your Model'), choices=self.models, allow_custom_value=False)
            self.api_url = gr.Text(value="Default", interactive=not self.server_mode, label="URL", max_lines=1)
            with gr.Row():
                self.unload_model_btn = gr.Button(value=i18n('Unload Model'), visible=not self.server_mode, interactive=not self.server_mode)
                self.unload_model_btn.click(self.unload_model, inputs=[self.select_model])
                if not self.server_mode:
                    self.refresh_model_btn = gr.Button(value="🔄️")
                    self.refresh_model_btn.click(self.get_models, inputs=[self.api_url], outputs=[self.select_model])
            self.prompt = gr.Text(label=i18n('Custom prompt (enabled when filled in)'), value='', placeholder="Directly translate the following content to English:", interactive=True)
            self.translate_btn = gr.Button(value=i18n('Start Translating'), variant="primary")
            self.translate_btn.click(lambda *args: start_translation(*args, translator="ollama"), inputs=[*inputs, self.select_model, self.api_url, self.prompt], outputs=[output_info, output_files])
