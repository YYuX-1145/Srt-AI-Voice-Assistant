import gradio as gr
from ..utils import run_command
import os

current_path = os.environ.get("current_path")

class WAV2SRT():
    def __init__(self,config):
          self.config=config
          self.ui=False
    def update_cfg(self,config):
          self.config=config
    def UI(self,file_main,file_tr):
        if not self.ui:
             self.ui=True
             return self._UI(file_main,file_tr)
        else:
             raise "err"
    def _UI(self,file_main,file_tr):
        available=False
        if os.path.exists(os.path.join(current_path,"tools","wav2srt.py")):
            available=True
            with gr.TabItem("音频转字幕"):
                        with gr.Row():
                            self.wav2srt_last_output=gr.State(value="")
                            with gr.Column():
                                self.wav2srt_input=gr.File(label="上传音频文件",interactive=True)
                                self.wav2srt_out_dir=gr.Textbox(value=os.path.join(current_path,"SAVAdata","output"),label="保存路径，填文件夹名",interactive=True)
                                self.wav2srt_pydir=gr.Textbox(value=self.config.gsv_pydir,label="Python解释器路径",interactive=True)
                                self.wav2srt_engine=gr.Radio(choices=["funasr","whisper"],value="funasr",label="选择asr模型，funasr只支持中文但更快更准，faster whisper支持多语言",interactive=True)
                                self.wav2srt_min_length=gr.Slider(label="(ms)每段最小多长，如果第一段太短一直和后面段连起来直到超过这个值",minimum=0,maximum=90000,step=100,value=5000)
                                self.wav2srt_min_interval=gr.Slider(label="(ms)最短切割间隔",minimum=0,maximum=5000,step=10,value=300)
                                self.wav2srt_sil=gr.Slider(label="(ms)切完后静音最多留多长",minimum=0,maximum=2000,step=100,value=1000)
                                self.wav2srt_args=gr.Textbox(value="",label="其他参数",interactive=True)
                                self.wav2srt_run=gr.Button(value="开始",variant="primary",interactive=True)
                                self.wav2srt_send2main=gr.Button(value="发送到主页面",variant="secondary",interactive=True)
                                self.wav2srt_send2main.click(send,inputs=[self.wav2srt_last_output],outputs=[file_main])
                                self.wav2srt_send2tr=gr.Button(value="发送到翻译",variant="secondary",interactive=True)
                                self.wav2srt_send2tr.click(lambda x:send(x,list=True),inputs=[self.wav2srt_last_output],outputs=[file_tr])
                                self.wav2srt_run.click(self.run_wav2srt,inputs=[self.wav2srt_input,self.wav2srt_out_dir,self.wav2srt_pydir,self.wav2srt_engine,self.wav2srt_min_length,self.wav2srt_min_interval,self.wav2srt_sil,self.wav2srt_args],outputs=[self.wav2srt_last_output])
                            with gr.Column():
                                gr.Markdown("""
本功能可直接用于GPT-SoVITS整合包，否则需要自己安装对应依赖。<br>
# 其他参数：
`--whisper_size` 默认:large-v3 使用faster whisper时指定模型<br>
`--threshold` 默认:-40 音量小于这个值视作静音的备选切割点<br>
`--hop_size` 默认:20 怎么算音量曲线，越小精度越大计算量越高（不是精度越大效果越好）<br>
                                            """)
        return available
    def run_wav2srt(self,input,out_dir,pydir,engine,min_length,min_interval,max_sil_kept,args):
        if input is None:
            gr.Warning("请上传音频文件！")
            return None
        pydir=pydir.strip('"')
        if pydir in [None,""]:
            gr.Warning("请指定解释器！")
            return None          
        out_dir=out_dir.strip('"')
        out_dir=f"{os.path.join(out_dir,os.path.basename(input.name))}.srt"
        run_command(command=f'"{pydir}" tools\\wav2srt.py -input_dir "{input.name}" -output_dir "{out_dir}" -engine {engine} --min_length {int(min_length)} --min_interval {int(min_interval)} --max_sil_kept {int(max_sil_kept)}  {args}',dir=current_path)
        gr.Info("已打开新的处理窗口")
        return out_dir

def send(fp,list=False):
     if os.path.isfile(fp):
          if list:
               return [fp]
          return fp
     else:
          gr.Info("输出文件不存在！")
          return None