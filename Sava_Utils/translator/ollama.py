import requests
import gradio as gr
import json
import re
import subprocess
from . import Traducteur
from ..utils import rc_open_window
from .. import logger

class Ollama(Traducteur):
    def __init__(self):
        self.models=[]
        super().__init__(name="ollama")

    def update_cfg(self, config):
        self.ollama_url=config.ollama_url
        return super().update_cfg(config)

    def get_models(self,url):
        try:
            if self.server_mode:
                result = subprocess.run("ollama list",capture_output=True,text=True) #consider using awk
                lines=result.stdout.strip().split("\n")[1:]
                self.models=[i.split()[0] for i in lines]
                #print(self.models)
                return gr.update(choices=self.models,value=self.models[0] if len(self.models)!=0 else None)
            if url in [None,"","Default"]:
                url=self.ollama_url        
            response = requests.get(f'{url}/api/tags')
            response.raise_for_status()
            self.models.clear()
            for item in json.loads(response.content)["models"]:
                self.models.append(item["name"])
        except Exception as e:
            gr.Warning(f"ollama获取模型列表失败：{str(e)}")
            logger.error(f"ollama获取模型列表失败：{str(e)}")
        return gr.update(choices=self.models,value=self.models[0] if len(self.models)!=0 else None)

    def unload_model(self,model):
        if model in [None,[],""] or self.server_mode:
            gr.Warning(f"必须指定模型")
            return None
        rc_open_window(f"ollama stop {model} && exit")        

    def api(self,text,target_lang,model_name,url):
        if url in [None,"","Default"] or self.server_mode:
            url=self.ollama_url
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
        if self.server_mode:
            self.get_models("")
        with gr.Column():
            gr.Markdown("⚠️LLM在运行时会占用较多VRAM。使用完毕后不要忘了选择并卸载对应模型以释放显存！⚠️")
            gr.Markdown("⚠️不建议使用推理模型执行翻译任务！⚠️")
            self.select_model=gr.Dropdown(label="选择模型",choices=self.models,allow_custom_value=False)
            self.api_url=gr.Text(value="Default",interactive=not self.server_mode,label="请求地址",max_lines=1) 
            with gr.Row():  
                self.unload_model_btn=gr.Button(value="卸载模型",visible=not self.server_mode,interactive=not self.server_mode)
                self.unload_model_btn.click(self.unload_model,inputs=[self.select_model])
                if not self.server_mode:
                    self.refresh_model_btn=gr.Button(value="刷新模型")
                    self.refresh_model_btn.click(self.get_models,inputs=[self.api_url],outputs=[self.select_model])
            self.translate_btn=gr.Button(value="开始翻译",variant="primary")
            self.translate_btn.click(lambda *args:start_translation(*args,translator="ollama"),inputs=[*inputs,self.select_model,self.api_url],outputs=[output_info,output_files])
