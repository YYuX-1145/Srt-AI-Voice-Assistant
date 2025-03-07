import requests
import gradio as gr
import json
from . import Traducteur
from .. import logger

class Ollama(Traducteur):
    def __init__(self):
        self.models=[]
        super().__init__(name="ollama")

    def get_models(self,url):
        try:
            response = requests.get(f'{url}/api/tags')
            response.raise_for_status()
            self.models.clear()
            for item in json.loads(response.content)["models"]:
                self.models.append(item["name"])
        except Exception as e:
            gr.Warning(f"获取模型列表失败：{str(e)}")
            logger.error(f"获取模型列表失败：{str(e)}")
        return gr.update(choices=self.models,value=self.models[0] if len(self.models)!=0 else "")

    def api(self,text,target_lang,model_name,url):
        if model_name in [None,[],""]:
            gr.Warning(f"翻译失败：必须指定模型")
            return None
        data_json = {
            "model": model_name,
            "prompt": f"Translate the following text to {target_lang}, do not reply with irrelevant content:{text}",
            "stream": False,
        }
        try:
            response=requests.post(url=f'{url}/api/generate',json=data_json) 
            response.raise_for_status()
            return json.loads(response.content)["response"]
        except Exception as e:
            logger.error(f"翻译失败：{str(e)}")
            gr.Warning(f"翻译失败：{str(e)}")
            return None

    def _UI(self,*inputs,output_info):
        from ..subtitle_translation import start_translation
        with gr.Column():
            self.select_model=gr.Dropdown(label="选择模型",choices=self.models,allow_custom_value=True)
            self.refresh_model_btn=gr.Button(value="刷新模型")            
            self.api_url=gr.Text(value="http://localhost:11434",interactive=True,max_lines=1)
            self.refresh_model_btn.click(self.get_models,inputs=[self.api_url],outputs=[self.select_model])
            self.translate_btn=gr.Button(value="开始翻译",variant="primary")
            self.translate_btn.click(lambda *args:start_translation(*args,translator="ollama"),inputs=[*inputs,self.select_model,self.api_url],outputs=[output_info])
