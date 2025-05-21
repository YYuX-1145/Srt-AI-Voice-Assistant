import gradio as gr
from ..import i18n
from ..utils import rc_bg,kill_process
from ..base_componment import Base_Componment
import os


current_path = os.environ.get("current_path")
OUT_DIR_DEFAULT=os.path.join(current_path,"SAVAdata","output")


class WAV2SRT(Base_Componment):
    def __init__(self, config):
        self.gsv_pydir = ""
        self.gsv_dir = ""
        super().__init__(config)

    def update_cfg(self, config):
        self.gsv_pydir = config.gsv_pydir
        self.gsv_dir = config.gsv_dir
        super().update_cfg(config)

    def _UI(self, file_main, file_tr):
        available = False
        if os.path.exists(os.path.join(current_path, "tools", "wav2srt.py")):
            available = True
            with gr.TabItem(i18n('Audio/Video Transcribe')):
                with gr.Row():
                    self.wav2srt_pid = gr.State(value=-1)
                    with gr.Column():
                        self.wav2srt_input = gr.File(label=i18n('Upload File'), file_count="multiple", interactive=True)
                        self.wav2srt_out_dir = gr.Textbox(value="Default", label=i18n('Save Path(Folder Path), Default: SAVAdata\\output'), visible=not self.server_mode, interactive=not self.server_mode)
                        self.wav2srt_pydir = gr.Textbox(value='Auto', label=i18n('Python Interpreter Path, align with GSV by default'), visible=not self.server_mode, interactive=not self.server_mode)
                        self.wav2srt_uvr_models = gr.Dropdown(
                            value='None',
                            choices=[
                                'None',
                                'HP2_all_vocals',
                                'model_bs_roformer_ep_317_sdr_12.9755',
                                'onnx_dereverb_By_FoxJoy',
                            ],
                            allow_custom_value=True,
                            label=i18n('Select UVR model. If voice and background noise classification is not needed, keep the option value as None.'),
                        )
                        self.wav2srt_engine = gr.Radio(choices=["funasr", "whisper"], value="funasr", label=i18n('Select ASR model. Funasr supports only Chinese(but much more faster) while Faster-Whisper has multi-language support'), interactive=True)
                        self.wav2srt_min_length = gr.Slider(label=i18n('(ms)Minimum length of each segment'), minimum=0, maximum=10000, step=100, value=3000)
                        self.wav2srt_min_interval = gr.Slider(label=i18n('(ms)Minium slice interval'), minimum=0, maximum=5000, step=10, value=300)
                        self.wav2srt_sil = gr.Slider(label=i18n('(ms)Maxium silence length'), minimum=0, maximum=2000, step=100, value=1000)
                        self.wav2srt_args = gr.Textbox(value="", label=i18n('Other Parameters'), interactive=True)
                    with gr.Column():
                        gr.Markdown(i18n('WAV2SRT_INFO'))
                        self.wav2srt_output = gr.File(label=i18n('Output File'), file_count="multiple", interactive=False)
                        self.wav2srt_output_status = gr.Textbox(
                            label=i18n('Output Info'),
                            value="",
                            interactive=False,
                        )
                        with gr.Row():
                            self.wav2srt_run = gr.Button(value=i18n('Start'), variant="primary", interactive=True)
                            self.wav2srt_terminate = gr.Button(value=i18n('Stop'), variant="secondary", interactive=True)
                            self.wav2srt_terminate.click(kill_process, inputs=[self.wav2srt_pid])
                        self.wav2srt_send2main = gr.Button(value=i18n('Send output files to Main Page'), variant="secondary", interactive=True)
                        self.wav2srt_send2main.click(send, inputs=[self.wav2srt_output], outputs=[file_main])
                        self.wav2srt_send2tr = gr.Button(value=i18n('Send output files to Translator'), variant="secondary", interactive=True)
                        self.wav2srt_send2tr.click(send, inputs=[self.wav2srt_output], outputs=[file_tr])
                    self.wav2srt_run.click(
                        self.run_wav2srt,
                        inputs=[self.wav2srt_input, self.wav2srt_out_dir, self.wav2srt_pydir, self.wav2srt_uvr_models, self.wav2srt_engine, self.wav2srt_min_length, self.wav2srt_min_interval, self.wav2srt_sil, self.wav2srt_args],
                        outputs=[self.wav2srt_pid, self.wav2srt_output_status, self.wav2srt_output],
                        max_batch_size=2,
                    )
        return available

    def run_wav2srt(self,inputs,out_dir,pydir,uvr_model,engine,min_length,min_interval,max_sil_kept,args):
        if self.server_mode:
            pydir=""
            out_dir=""
        if inputs in [None,[]]:
            gr.Warning(i18n('Please upload audio or video!'))
            return -1,i18n('Please upload audio or video!'),None
        pydir=pydir.strip('"')
        if pydir in [None,"",'Auto']:
            if self.gsv_pydir not in [None,""]:
                pydir=self.gsv_pydir
            else:
                gr.Warning(i18n('Please specify Python Interpreter!'))
                return -1,i18n('Please specify Python Interpreter!'),None
        if out_dir in ['',None,'Default']:
            out_dir=OUT_DIR_DEFAULT
        output_list = []
        out_dir=out_dir.strip('"')
        msg=f"{i18n('Processing')}\n"
        input_str = " ".join([i.name for i in inputs])
        output_dir_str = f' -output_dir "{out_dir}"' if not self.server_mode else ""
        command=f'"{pydir}" tools\\wav2srt.py -input {input_str}{output_dir_str} --uvr_model {uvr_model} -engine {engine} --min_length {int(min_length)} --min_interval {int(min_interval)} --max_sil_kept {int(max_sil_kept)}  {args}'
        x=rc_bg(command=command,dir=self.gsv_dir if self.gsv_dir and os.path.isdir(self.gsv_dir) else current_path)
        pid=next(x)
        yield pid,msg,output_list
        exit_code=next(x)
        if exit_code==0:
            msg+=f"{i18n('Done!')}\n"
            if self.server_mode:
                for i in inputs:
                    output_list.append(os.path.join(os.path.dirname(i.name), f"{os.path.basename(i.name)}.srt"))
                    if uvr_model not in ['None',None,'']:
                        output_list.append(os.path.join(os.path.dirname(i.name), f"instrument_{os.path.basename(i.name)}"))
                        output_list.append(os.path.join(os.path.dirname(i.name), f"vocal_{os.path.basename(i.name)}"))
            else:
                for i in inputs:
                    output_list.append(os.path.join(out_dir, f"{os.path.basename(i.name)}.srt"))
                    if uvr_model not in ['None',None,'']:
                        output_list.append(os.path.join(out_dir, f"instrument_{os.path.basename(i.name)}"))
                        output_list.append(os.path.join(out_dir, f"vocal_{os.path.basename(i.name)}"))
        else:
            msg += f"{i18n('Tasks are terminated due to an error in')}\n"
        ret = []
        for i in output_list:
            if os.path.exists(i):
                ret.append(i)
            else:
                msg += f'failed: {i}'
        msg += f"{i18n('Finished')}\n"
        yield -1,msg,ret


def send(fp_list):
     return [i.name for i in fp_list if i.name.endswith(".srt")] if fp_list is not None else fp_list
