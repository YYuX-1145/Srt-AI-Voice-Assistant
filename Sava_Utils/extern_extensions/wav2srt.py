import gradio as gr
from ..utils import rc_bg,kill_process
import os

current_path = os.environ.get("current_path")
OUT_DIR_DEFAULT=os.path.join(current_path,"SAVAdata","output")
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
                            self.wav2srt_pid=gr.State(value=-1)
                            with gr.Column():
                                self.wav2srt_input=gr.File(label="上传音频文件",type="file",file_count="multiple",interactive=True)
                                self.wav2srt_out_dir=gr.Textbox(value="Default",label="保存路径，填文件夹名，默认为SAVAdata\\output",visible=not self.config.server_mode,interactive=not self.config.server_mode)
                                self.wav2srt_pydir=gr.Textbox(value='Auto',label="Python解释器路径,默认和GSV一致",visible=not self.config.server_mode,interactive=not self.config.server_mode)
                                self.wav2srt_engine=gr.Radio(choices=["funasr","whisper"],value="funasr",label="选择asr模型，funasr只支持中文但更快更准，faster whisper支持多语言",interactive=True)
                                self.wav2srt_min_length=gr.Slider(label="(ms)每段最小多长，如果第一段太短一直和后面段连起来直到超过这个值",minimum=0,maximum=90000,step=100,value=5000)
                                self.wav2srt_min_interval=gr.Slider(label="(ms)最短切割间隔",minimum=0,maximum=5000,step=10,value=300)
                                self.wav2srt_sil=gr.Slider(label="(ms)切完后静音最多留多长",minimum=0,maximum=2000,step=100,value=1000)
                                self.wav2srt_args=gr.Textbox(value="",label="其他参数",interactive=True)                     
                            with gr.Column():
                                gr.Markdown("""
本功能可直接用于GPT-SoVITS整合包，否则需要自己安装对应依赖。<br>
# 其他参数：
`--whisper_size` 默认:large-v3 使用faster whisper时指定模型<br>
`--threshold` 默认:-40 音量小于这个值视作静音的备选切割点<br>
`--hop_size` 默认:20 怎么算音量曲线，越小精度越大计算量越高（不是精度越大效果越好）<br>
                                            """)
                                self.wav2srt_output=gr.File(label="输出文件",type="file",file_count="multiple",interactive=False)
                                self.wav2srt_output_status=gr.Textbox(label="输出信息",value="",interactive=False,)
                                with gr.Row():
                                    self.wav2srt_run=gr.Button(value="开始",variant="primary",interactive=True)      
                                    self.wav2srt_terminate=gr.Button(value="终止",variant="secondary",interactive=True)  
                                    self.wav2srt_terminate.click(kill_process,inputs=[self.wav2srt_pid])                                
                                self.wav2srt_send2main=gr.Button(value="发送到主页面",variant="secondary",interactive=True)
                                self.wav2srt_send2main.click(send,inputs=[self.wav2srt_output],outputs=[file_main])
                                self.wav2srt_send2tr=gr.Button(value="发送到翻译",variant="secondary",interactive=True)
                                self.wav2srt_send2tr.click(send,inputs=[self.wav2srt_output],outputs=[file_tr])
        self.wav2srt_run.click(self.run_wav2srt,inputs=[self.wav2srt_input,self.wav2srt_out_dir,self.wav2srt_pydir,self.wav2srt_engine,self.wav2srt_min_length,self.wav2srt_min_interval,self.wav2srt_sil,self.wav2srt_args],outputs=[self.wav2srt_pid,self.wav2srt_output_status,self.wav2srt_output],max_batch_size=2)
        return available
    

    def run_wav2srt(self,inputs,out_dir,pydir,engine,min_length,min_interval,max_sil_kept,args):
        if self.config.server_mode:
            pydir=""
            out_dir=""
        if inputs in [None,[]]:
            gr.Warning("请上传音频文件！")
            return -1,"请上传音频文件！",None
        pydir=pydir.strip('"')
        if pydir in [None,"",'Auto']:
            if self.config.gsv_pydir not in [None,""]:
                pydir=self.config.gsv_pydir
            else:
                gr.Warning("请指定解释器！")
                return -1,"请指定解释器！",None
        if out_dir in ['',None,'Default']:
            out_dir=OUT_DIR_DEFAULT
        output_list=[]   
        out_dir=out_dir.strip('"')
        msg=""
        for input in inputs:
            msg+=f"正在进行:{os.path.basename(input.name)}\n"
            output_path=f"{os.path.join(out_dir,os.path.basename(input.name))}.srt"
            command=f'"{pydir}" tools\\wav2srt.py -input_dir "{input.name}" -output_dir "{output_path}" -engine {engine} --min_length {int(min_length)} --min_interval {int(min_interval)} --max_sil_kept {int(max_sil_kept)}  {args}'
            x=rc_bg(command=command,dir=self.config.gsv_dir if self.config.gsv_dir else current_path)
            pid=next(x)
            yield pid,msg,output_list
            exit_code=next(x)
            if exit_code==0:
                msg+=f"任务完成:{os.path.basename(input.name)}\n"
                output_list.append(output_path)                
            else:
                msg+=f"任务出错,终止:{os.path.basename(input.name)}\n"
                break
            yield -1,msg,output_list
        msg+="任务结束\n"
        yield -1,msg,output_list

def send(fp_list):
     return [i.name for i in fp_list] if fp_list is not None else fp_list