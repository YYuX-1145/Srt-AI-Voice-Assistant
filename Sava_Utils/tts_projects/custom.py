from . import TTSProjet
import requests
import gradio as gr
from ..utils import positive_int
from .. import logger
from ..man.manual import Man
import time
import os

current_path=os.environ.get("current_path")

class Custom(TTSProjet):
    def __init__(self):
        super().__init__("bv2")
        self.custom_api_list = []

    def api(self,text):
        return custom_api(text)

    def _UI(self):
        with gr.Column():
            man=Man()
            gr.Markdown(value=man.getInfo("custom_warn"))
            gr.Markdown(value=man.getInfo("help_custom"))                            
            self.choose_custom_api=gr.Dropdown(label='选择自定义API代码文件',choices=self.custom_api_list,value=self.custom_api_list[0] if self.custom_api_list!=[] else '',allow_custom_value=True)
            self.refresh_custom_btn = gr.Button(value="刷新")
            self.gen_btn4 = gr.Button(value="生成", variant="primary", visible=True)
            self.refresh_custom_btn.click(self.refresh_custom_api_list,outputs=[self.choose_custom_api])
        return []
    
    def before_gen_action(self,*args,**kwargs):
            #print(args)
            custom_api_path=args[0]
            logger.info(f"Exec: custom_api_path {custom_api_path}")
            with open(os.path.join(current_path,"SAVAdata","presets",custom_api_path),"r",encoding="utf-8") as f:
                code=f.read()
            exec(code,globals())
    
    def save_action(self, *args, text):
        return self.api(text)
    
    def refresh_custom_api_list(self):
        self.custom_api_list=['None']
        try:
            preset_dir=os.path.join(current_path,"SAVAdata","presets")
            if os.path.isdir(preset_dir):
                self.custom_api_list+=[i for i in os.listdir(preset_dir) if i.endswith(".py")]
            else:
                logger.info("当前没有自定义API预设")
        except Exception as e:
            self.custom_api_list = ['None']
            err=f"刷新预设失败：{e}"
            logger.error(err)
            gr.Warning(err)
        time.sleep(0.1)
        return gr.update(value="None", choices=self.custom_api_list)  

    def arg_filter(self,*args):
        input_file,fps,offset,workers,custom_api=args
        if custom_api in [None,'None','']:
            gr.Info("请选择API配置文件！")
            raise Exception("请选择API配置文件！")
        kwargs={'in_files':input_file,'fps':fps,'offset':offset,'proj':"custom",'max_workers':workers}
        return (custom_api,None), kwargs #