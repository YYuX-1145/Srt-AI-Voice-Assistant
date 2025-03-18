import requests
import gradio as gr
import json
import re
from . import Traducteur
from ..utils import rc_open_window
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

    def unload_model(self,model):
        if model in [None,[],""]:
            gr.Warning(f"必须指定模型")
            return None
        rc_open_window(f"ollama stop {model} && exit")        

    def api(self,text,target_lang,model_name,url):
        if model_name in [None,[],""]:
            raise ValueError(f"必须指定模型")
        data_json = {
            "model": model_name,
            "prompt": f"Directly translate the following content to {target_lang} WITHOUT replying with any additional notes or questions:{text}",
            "stream": False,
        }
        #print(data_json["prompt"])
        response=requests.post(url=f'{url}/api/generate',json=data_json) 
        response.raise_for_status()
        return re.sub(r'<think>.*?</think>','',json.loads(response.content)["response"],flags=re.DOTALL).strip()

    def _UI(self,*inputs,output_info,output_files):
        from ..subtitle_translation import start_translation
        with gr.Column():
            gr.Markdown("⚠️LLM在运行时会占用较多VRAM。使用完毕后不要忘了选择并卸载对应模型以释放显存！⚠️")
            gr.Markdown("⚠️不建议使用推理模型执行翻译任务！⚠️")
            self.select_model=gr.Dropdown(label="选择模型",choices=self.models,allow_custom_value=True)
            self.api_url=gr.Text(value="http://localhost:11434",interactive=True,label="请求地址",max_lines=1) 
            with gr.Row():  
                self.unload_model_btn=gr.Button(value="卸载模型")
                self.unload_model_btn.click(self.unload_model,inputs=[self.select_model])
                self.refresh_model_btn=gr.Button(value="刷新模型")
                self.refresh_model_btn.click(self.get_models,inputs=[self.api_url],outputs=[self.select_model])
            self.translate_btn=gr.Button(value="开始翻译",variant="primary")
            self.translate_btn.click(lambda *args:start_translation(*args,translator="ollama"),inputs=[*inputs,self.select_model,self.api_url],outputs=[output_info,output_files])
