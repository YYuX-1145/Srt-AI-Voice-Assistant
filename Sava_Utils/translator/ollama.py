import requests
import gradio as gr
from . import Traducteur
from .. import logger

class Ollama(Traducteur):
    def __init__(self):
        self.models=[]
        super().__init__(name="ollama")

    def get_models(self):
        try:
            response = requests.get('http://localhost:11434/api/tags')
            response.raise_for_status()
            self.models.clear()
            for item in response.content["model"]:
                self.models.append(item["name"])
        except Exception as e:
            gr.Warning(f"获取模型列表失败：{str(e)}")
            logger.error(f"获取模型列表失败：{str(e)}")

    def api(self,text,target_lang,model_name):
        data_json = {
            "model": model_name,
            "prompt": f"Translate the following text to {target_lang}, do not reply with irrelevant content:{text}",
            "stream": False,
        }
        try:
            response=requests.post(url='http://localhost:11434/api/generate',json=data_json) 
            response.raise_for_status()
            return response.content["response"]
        except Exception as e:
            logger.error(f"翻译失败：{str(e)}")
            gr.Warning(f"翻译失败：{str(e)}")
            return None

    def _UI(self,*inputs):
        with gr.Column():
            pass
