import gradio as gr
from .. import i18n
from ..utils import rc_bg, kill_process, basename_no_ext,fix_null,logger
from ..base_componment import Base_Componment
import os
import subprocess
import platform
if platform.system() != "Windows":
    import shlex
current_path = os.environ.get("current_path")
OUT_DIR_DEFAULT = os.path.join(current_path, "SAVAdata", "output")


def flatten(lst):
    for item in lst:
        if item is None:
            continue
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


class WAV2SRT(Base_Componment):
    def __init__(self, config):
        self.gsv_pydir = ""
        self.gsv_dir = ""
        super().__init__(config)

    def update_cfg(self, config):
        self.gsv_pydir = config.gsv_pydir
        self.gsv_dir = config.gsv_dir
        super().update_cfg(config)

    def _UI(self, file_main, worklist, TR_MODULE):
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
                                'HP5_only_main_vocal',
                                'model_bs_roformer_ep_317_sdr_12.9755',
                                'onnx_dereverb_By_FoxJoy',
                            ],
                            allow_custom_value=not self.server_mode,
                            label=i18n('Select UVR model. If vocal separation is not needed, set the value to None.'),
                        )
                        self.wav2srt_engine = gr.Radio(choices=["whisper", "funasr"], value="whisper", label=i18n('Select ASR model. Funasr supports only Chinese(but much more faster) while Faster-Whisper has multi-language support'), interactive=True)
                        self.wav2srt_whisper_size = gr.Radio(choices=["small", "medium", "large-v3-turbo"], value="large-v3-turbo", label=i18n('Whisper Size'), interactive=True)
                        self.wav2srt_engine.change(lambda x: gr.update(visible=x == "whisper"), inputs=[self.wav2srt_engine], outputs=[self.wav2srt_whisper_size])
                        self.wav2srt_min_length = gr.Slider(label=i18n('(ms)Minimum length of each segment'), minimum=0, maximum=10000, step=100, value=3000)
                        self.wav2srt_min_interval = gr.Slider(label=i18n('(ms)Minium slice interval'), minimum=0, maximum=5000, step=10, value=300)
                        self.wav2srt_sil = gr.Slider(label=i18n('(ms)Maxium silence length'), minimum=0, maximum=1000, step=50, value=500)
                        # self.wav2srt_args = gr.Textbox(value="", label=i18n('Other Parameters'), interactive=True)
                    with gr.Column():
                        gr.Markdown(i18n('WAV2SRT_INFO'))
                        with gr.Accordion(i18n('Video Merge Tool'), open=False):
                            with gr.Group():
                                with gr.Row():
                                    self.video_merge_inputvid = gr.Dropdown(label=i18n('Original video path'), choices=[('None', 'None')], interactive=True, allow_custom_value=not self.server_mode)
                                    self.video_merge_sub = gr.Dropdown(label=i18n('Hard subtitles (optional)'), choices=[('None', 'None')], interactive=True, allow_custom_value=not self.server_mode)
                                with gr.Row():
                                    self.video_merge_inst = gr.Dropdown(label=i18n('Background audio (optional, override the original video audio)'), choices=[('None', 'None')], interactive=True, allow_custom_value=not self.server_mode)
                                    self.inst_vol = gr.Slider(label=i18n('Volume'), minimum=0, maximum=2, value=1, step=0.1, interactive=True)
                                with gr.Row():
                                    self.video_merge_audio = gr.Dropdown(label=i18n('Dubbed audio path'), choices=[('None', 'None')], interactive=True, allow_custom_value=not self.server_mode)
                                    self.audio_vol = gr.Slider(label=i18n('Volume'), minimum=0, maximum=2, value=1, step=0.1, interactive=True)
                            with gr.Row():
                                self.merge_video_btn = gr.Button(value=i18n('Start Merging Video'), variant='primary')
                                self.merge_video_ref_btn = gr.Button(value='🔄️', variant='secondary')
                        self.wav2srt_output = gr.File(label=i18n('Output File'), file_count="multiple", interactive=False)
                        self.wav2srt_output_status = gr.Textbox(label=i18n('Output Info'), value="", interactive=False)
                        with gr.Row():
                            self.wav2srt_run = gr.Button(value=i18n('Start'), variant="primary", interactive=True)
                            self.wav2srt_terminate = gr.Button(value=i18n('Stop'), variant="secondary", interactive=True)
                            self.wav2srt_terminate.click(kill_process, inputs=[self.wav2srt_pid])
                        self.wav2srt_send2main = gr.Button(value=i18n('Send output files to Main Page'), variant="secondary", interactive=True)
                        self.wav2srt_send2main.click(send, inputs=[self.wav2srt_output], outputs=[file_main])
                        self.wav2srt_send2tr = gr.Button(value=i18n('Send output files to Translator'), variant="secondary", interactive=True)
                        self.wav2srt_send2tr.click(send, inputs=[self.wav2srt_output], outputs=[TR_MODULE.translation_upload])
                    self.merge_video_ref_btn.click(
                        self.refresh_merge_vid,
                        inputs=[worklist, self.wav2srt_input, self.wav2srt_output, TR_MODULE.translation_output, file_main],
                        outputs=[self.video_merge_inputvid, self.video_merge_sub, self.video_merge_inst, self.video_merge_audio],
                    )
                    self.merge_video_btn.click(
                        self.run_merge_vid,
                        inputs=[self.wav2srt_output, self.video_merge_inputvid, self.video_merge_sub, self.video_merge_inst, self.inst_vol, self.video_merge_audio, self.audio_vol],
                        outputs=[self.wav2srt_output_status, self.wav2srt_output],
                    )
                    self.wav2srt_run.click(
                        self.run_wav2srt,
                        inputs=[self.wav2srt_input, self.wav2srt_out_dir, self.wav2srt_pydir, self.wav2srt_uvr_models, self.wav2srt_engine, self.wav2srt_whisper_size, self.wav2srt_min_length, self.wav2srt_min_interval, self.wav2srt_sil],
                        outputs=[self.wav2srt_pid, self.wav2srt_output_status, self.wav2srt_output],
                        concurrency_limit=1,
                    )
        return available

    def run_wav2srt(self, inputs, out_dir, pydir, uvr_model, engine, whisper_size, min_length, min_interval, max_sil_kept, args):
        if self.server_mode:
            pydir = ""
            out_dir = ""
        if inputs in [None, []]:
            gr.Warning(i18n('Please upload audio or video!'))
            return -1, i18n('Please upload audio or video!'), None
        if not self.server_mode and len(set(basename_no_ext(i.name) for i in inputs)) != len(inputs):
            gr.Warning(i18n('Uploading files with the same name is not allowed.'))
            return -1, i18n('Uploading files with the same name is not allowed.'), None
        pydir = pydir.strip('"')
        if pydir in [None, "", 'Auto']:
            if self.gsv_pydir not in [None, ""]:
                pydir = self.gsv_pydir
            else:
                gr.Warning(i18n('Please specify Python Interpreter!'))
                return -1, i18n('Please specify Python Interpreter!'), None
        if out_dir in ['', None, 'Default']:
            out_dir = OUT_DIR_DEFAULT
        output_list = []
        out_dir = out_dir.strip('"')
        os.makedirs(out_dir, exist_ok=True)
        msg = f"{i18n('Processing')}\n"
        input_str = '"' + '" "'.join([i.name for i in inputs]) + '"'
        output_dir_str = f' -output_dir "{out_dir}"' if not self.server_mode else ""
        command = f'"{pydir}" tools/wav2srt.py -input {input_str}{output_dir_str} --uvr_model {uvr_model} -engine {engine} --whisper_size {whisper_size} --min_length {int(min_length)} --min_interval {int(min_interval)} --max_sil_kept {int(max_sil_kept)}'
        process = rc_bg(command=command, dir=self.gsv_dir if self.gsv_dir and os.path.isdir(self.gsv_dir) else current_path)
        pid = process.pid
        yield pid, msg, output_list
        progress_line = ''
        for line in process.stdout:
            if r"it/s" in line or r"s/it" in line:
                progress_line = line
            elif line.strip():
                msg += line
            if progress_line:
                yield pid, msg + '\n' + progress_line, output_list
            else:
                yield pid, msg, output_list
        process.communicate()
        yield -1, msg, output_list
        exit_code = process.returncode
        if exit_code == 0:
            msg += f"{i18n('Done!')}\n"
            if self.server_mode:
                for i in inputs:
                    output_list.append(os.path.join(os.path.dirname(i.name), f"{basename_no_ext(i.name)}.srt"))
                    if uvr_model not in ['None', None, '']:
                        output_list.append(os.path.join(os.path.dirname(i.name), f"instrument_{basename_no_ext(i.name)}.wav"))
                        output_list.append(os.path.join(os.path.dirname(i.name), f"vocal_{basename_no_ext(i.name)}.wav"))
            else:
                for i in inputs:
                    output_list.append(os.path.join(out_dir, f"{basename_no_ext(i.name)}.srt"))
                    if uvr_model not in ['None', None, '']:
                        output_list.append(os.path.join(out_dir, f"instrument_{basename_no_ext(i.name)}.wav"))
                        output_list.append(os.path.join(out_dir, f"vocal_{basename_no_ext(i.name)}.wav"))
        else:
            msg += f"{i18n('Tasks are terminated due to an error in')}\n"
        ret = []
        for i in output_list:
            if os.path.exists(i):
                ret.append(i)
            else:
                msg += f'failed: {i}\n'
        msg += f"{i18n('Finished')}\n"
        yield -1, msg, ret

    def refresh_merge_vid(self, current_audio, *args):  # *args: this_i,this_o,tr_o,main_i
        vid_list = [('None', 'None')]
        sub_list = [('None', 'None')]
        bg_list = [('None', 'None')]
        db_list = [('None', 'None')]
        for file in flatten(args):
            ext = os.path.splitext(file.name)[1].lower()
            if ext in ['.mp4', '.flv', '.mkv', '.mov', '.webm']:
                vid_list.append((os.path.basename(file.name), file.name))
            elif os.path.basename(file.name).startswith("instrument_") and ext == '.wav':
                bg_list.append((os.path.basename(file.name), file.name))
            elif ext == '.srt':
                sub_list.append((os.path.basename(file.name), file.name))
        current_audio_path = ''
        if current_audio and os.path.exists(os.path.join(OUT_DIR_DEFAULT, f'{current_audio}.wav')):
            current_audio_path = os.path.join(OUT_DIR_DEFAULT, f'{current_audio}.wav')
        if self.server_mode and current_audio_path:
            db_list = [(f'{current_audio}.wav', current_audio_path)]
        elif not self.server_mode:
            db_list += [(i, os.path.join(OUT_DIR_DEFAULT, i)) for i in os.listdir(OUT_DIR_DEFAULT) if i.endswith('.wav')]
        return (
            gr.update(choices=vid_list, value=vid_list[-1][1]),
            gr.update(choices=sub_list, value=sub_list[-1][1]),
            gr.update(choices=bg_list, value=bg_list[-1][1]),
            gr.update(choices=db_list, value=current_audio_path if current_audio_path else db_list[-1][1]),
        )

    def run_merge_vid(self, file_list: list, video: str, sub: str, bg: str, bg_vol: float, db: str, db_vol: float):
        if file_list is None:
            file_list = []
        video = video.strip('"')
        sub = sub.strip('"')
        bg = bg.strip('"')
        db = db.strip('"')            
        video, sub, bg, db = fix_null(video, sub, bg, db)
        if video is None or (sub is None and db is None):
            gr.Info(i18n('You must specify the original video along with audio or subtitles.'))
            return None,file_list
        input_args = ['-i', video]
        filter_complex = []
        map_args = []
        audio_inputs = []
        audio_filters = []
        index = 1
        vf_filter = ''
        if sub:
            sub_path = sub.replace('\\', '/').replace(':', '\\:')
            vf_filter = f"subtitles='{sub_path}'"
        if bg:
            input_args += ['-i', bg]
            audio_inputs.append(f'[{index}:a]volume={bg_vol}[bg]')
            index += 1
        if db:
            input_args += ['-i', db]
            audio_inputs.append(f'[{index}:a]volume={db_vol}[db]')
            index += 1
        if bg and db:
            audio_filters += audio_inputs
            audio_filters.append('[bg][db]amix=inputs=2:duration=longest[aout]')
            map_args += ['-map', '0:v', '-map', '[aout]']
        elif bg:
            audio_filters += audio_inputs
            audio_filters.append('[db]anull[aout]')
            map_args += ['-map', '0:v', '-map', '[aout]']
        elif db:
            audio_filters += audio_inputs
            map_args += ['-map', '0:v', '-map', '[db]']

        if vf_filter and audio_filters:
            filter_complex = ['-filter_complex', f"{';'.join(audio_filters)};[0:v]{vf_filter}[vout]"]
            map_args[map_args.index('0:v')] = '[vout]'
        elif vf_filter:
            filter_complex = ['-vf', vf_filter]
        elif audio_filters:
            filter_complex = ['-filter_complex', ';'.join(audio_filters)]

        if self.server_mode:
            output = os.path.join(os.path.dirname(video), f'merged_{os.path.basename(video)}')
        else:
            output = os.path.join(OUT_DIR_DEFAULT, f'merged_{os.path.basename(video)}')

        cmd = ['ffmpeg', '-y'] + input_args + filter_complex + map_args + ['-c:v', 'h264_nvenc' if platform.system() == "Windows" else "libx264", '-c:a', 'aac', output]
        logger.info(f"{i18n('Execute command')}:{cmd}")

        try:
            if platform.system() == "Windows":
                p = subprocess.run(cmd, cwd=current_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True, encoding='utf-8')
            else:
                p = subprocess.run(' '.join(shlex.quote(c) for c in cmd), cwd=current_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True, encoding='utf-8')
            file_list.append(output)
            msg = 'OK'
        except:
            gr.Warning('Failed to run ffmpeg')
            msg = p.stdout
        return msg, file_list


def send(fp_list):
    return [i.name for i in fp_list if i.name.endswith(".srt")] if fp_list is not None else fp_list
