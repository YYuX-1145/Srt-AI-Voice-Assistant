import requests
import gradio as gr
import json
import re
import subprocess
from . import Traducteur
from ..utils import rc_open_window
from .. import logger, i18n
from tqdm import tqdm


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
                result = subprocess.run("ollama list", capture_output=True, text=True, shell=True)  # consider using awk
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

    def api(self, tasks, target_lang, interrupt_flag, model_name, url, custom_prompt, num_history, no_think, file_name: str = ""):
        num_history = int(num_history)
        if url in [None, "", "Default"] or self.server_mode:
            url = self.ollama_url
        if model_name in [None, [], ""]:
            raise ValueError(i18n('You must specify the model!'))
        ret = []
        msg = ""
        request_data = {
            "model": model_name,
            "messages": [],
            "stream": False,
            "think": not no_think,
        }
        # print(request_data)
        for task in tqdm(tasks, desc=f"{i18n('Translating')}: {file_name}", total=len(tasks)):
            if interrupt_flag.is_set():
                break
            text = "\n\n".join(task)
            if custom_prompt:
                prompt = custom_prompt + '\n' + text
            else:
                prompt = f"Please translate the following content into {target_lang}. Strictly preserve the original paragraph structure. Do not include any additional comments or explanations---return only the translated text:\n{text}"
            data = {"role": "user", "content": prompt}
            request_data["messages"].append(data)
            response = requests.post(url=f'{url}/api/chat', json=request_data)
            response.raise_for_status()
            response_dict = json.loads(response.content)["message"]
            # print(response_dict["content"])
            result = re.sub(r'<think>.*?</think>', '', response_dict["content"], flags=re.DOTALL).strip()

            request_data["messages"].append(response_dict)
            if len(request_data["messages"]) > 2 * num_history:
                request_data["messages"].pop(0)
                request_data["messages"].pop(0)

            # print(request_data)
            batch = result.split("\n\n")
            d = len(task) - len(batch)
            if d:
                msg += f"{i18n('The language model has probably made a mistake')} @{len(ret)+1}-{len(ret)+len(task)}\n"
                if d > 0:
                    batch += ["" for _ in range(d)]
                else:
                    batch = batch[: len(task)]
            ret += batch
        return ret, msg

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
            self.num_history = gr.Slider(label=i18n('History Message Limit'), value=2, minimum=0, maximum=10, step=1)
            self.no_think_mode = gr.Checkbox(label="No Think", value=True, interactive=True)
            self.translate_btn = gr.Button(value=i18n('Start Translating'), variant="primary")
            self.translate_btn.click(lambda progress=gr.Progress(track_tqdm=True), *args: start_translation(*args, translator="ollama"), inputs=[*inputs, self.select_model, self.api_url, self.prompt, self.num_history, self.no_think_mode], outputs=[output_info, output_files])
