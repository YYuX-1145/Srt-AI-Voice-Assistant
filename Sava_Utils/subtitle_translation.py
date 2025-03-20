import gradio as gr
import os
import concurrent.futures
from tqdm import tqdm
import Sava_Utils
from .utils import read_prcsv, read_srt, read_txt
from .translator.ollama import Ollama


LANGUAGE = ["中文", "English", "日本語", "한국어", "Français"]
TRANSLATORS = {"ollama": Ollama()}
current_path = os.environ.get("current_path")

def start_translation(in_files, language, output_dir, *args, translator=None):
    output_list=[]
    if in_files is None:
        gr.Info("请上传字幕文件！")
        return "请上传字幕文件！",output_list    
    for in_file in in_files:
        if in_file.name[-4:].lower() == ".csv":
            subtitle_list = read_prcsv(in_file.name, fps=30, offset=0)
        elif in_file.name[-4:].lower() == ".srt":
            subtitle_list = read_srt(in_file.name, offset=0)
        elif in_file.name[-4:].lower() == ".txt":
            subtitle_list = read_txt(in_file.name)
        else:
            gr.Warning("未知的格式，请确保扩展名正确！")
            continue
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                x=list(
                        tqdm(executor.map(lambda x:TRANSLATORS[translator].api(*x),[(i.text,language,*args) for i in subtitle_list]),
                            total=len(subtitle_list), 
                            desc=f"正在翻译{os.path.basename(in_file.name)}"
                            )
                        )
            for sub,txt in zip(subtitle_list,x):
                sub.text=txt      
            output_path=os.path.join(output_dir, f"{os.path.basename(in_file.name)[:-4]}_translated_to_{language}.srt")
            subtitle_list.export(fp=output_path,open_explorer=False,raw=True)
            output_list.append(output_path)                          
        except Exception as e:
            gr.Warning(f"{in_file.name}翻译失败：{str(e)}")
            continue


    #os.system(f'explorer {output_dir}')
    return "ok" if len(output_list)==len(in_files) else "出现错误",output_list


class Translation_module:
    def __init__(self,config):
        self.ui = False
        self.config=config
        self.menu = []

    def update_cfg(self,config):
        self.config=config
        for i in TRANSLATORS.values():
            i.update_cfg(config=config)

    def UI(self,*args):
        if not self.ui:
            self.ui = True
            self._UI(*args)
        else:
            raise "err"

    def _UI(self,file_main):
        with gr.TabItem("字幕翻译"):
            with gr.Row():
                with gr.Column():
                    self.translation_upload = gr.File(label="上传字幕(可多个)",file_count="multiple",type="file",file_types=[".srt", ".csv", ".txt"])
                    self.result = gr.Text(interactive=False, value="", label="输出信息")
                    self.translation_output=gr.File(label="文件输出",file_count="multiple",interactive=False)
                    self.send_btn=gr.Button(value="发送至主页面",interactive=True)
                    self.send_btn.click(lambda x:[i.name for i in x] if x is not None else x,inputs=[self.translation_output],outputs=[file_main])
                with gr.Column():
                    self.translation_target_language = gr.Dropdown(label="选择目标语言",choices=LANGUAGE,value=LANGUAGE[1],interactive=True)
                    self.output_dir=gr.Text(value=os.path.join(current_path, "SAVAdata", "output"),label="输出路径",interactive=not Sava_Utils.config.server_mode,visible=not Sava_Utils.config.server_mode,max_lines=1)
                    self.translator = gr.Radio(label="选择翻译器",choices=[i for i in TRANSLATORS.keys()],value="ollama")
                    Base_args = [self.translation_upload,self.translation_target_language,self.output_dir]
                    with gr.Column():
                        v = True
                        for i in TRANSLATORS.keys():
                            x = gr.Column(i, visible=v)
                            with x:
                                TRANSLATORS[i].update_cfg(config=self.config)
                                TRANSLATORS[i].getUI(*Base_args,output_info=self.result,output_files=self.translation_output)
                            v = False
                        self.menu.append(x)
                self.translation_target_language.change(lambda x: [gr.update(visible= x==i ) for i in TRANSLATORS.keys()],inputs=[self.translator],outputs=self.menu)
                    
