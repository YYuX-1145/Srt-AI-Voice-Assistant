import requests
import gradio as gr
import os
from . import *


class BV2(TTSProjet):
    def __init__(self):
        super().__init__("Bert-VITS2", None, title="Bert-VITS2-HiyoriUI")

    def update_cfg(self, config: Settings):
        self.bv2_dir = config.query("bv2_dir")
        self.bv2_pydir = config.query("bv2_pydir")
        super().update_cfg(config)

    def api(self, text, mid, spk_name, sid, lang, length, noise, noisew, sdp, emotion, split, style_text, style_weight, port):
        try:
            API_URL = f'http://127.0.0.1:{port}/voice'
            data_json = {"model_id": mid, "speaker_name": spk_name, "speaker_id": sid, "language": lang, "length": length, "noise": noise, "noisew": noisew, "sdp_ratio": sdp, "emotion": emotion, "auto_translate": False, "auto_split": split, "style_text": style_text, "style_weight": style_weight, "text": text}
            # print(data_json)
            response = requests.get(url=API_URL, params=data_json)
            response.raise_for_status()
            return response.content
        except Exception as e:
            err = f"{i18n('An error has occurred. Please check if the API is running correctly. Details')}:{e}"
            logger.error(err)
            return None

    def save_action(self, *args, text: str = None):
        language, port, mid, sid, speaker_name, sdp_ratio, noise_scale, noise_scale_w, length_scale, emotion_text = args
        sid, port, mid = utils.positive_int(sid, port, mid)
        if speaker_name is not None and speaker_name != "":
            audio = self.api(text=text, mid=mid, spk_name=speaker_name, sid=None, lang=language, length=length_scale, noise=noise_scale, noisew=noise_scale_w, sdp=sdp_ratio, split=False, style_text=None, style_weight=0, port=port, emotion=emotion_text)
        else:
            audio = self.api(text=text, mid=mid, spk_name=None, sid=sid, lang=language, length=length_scale, noise=noise_scale, noisew=noise_scale_w, sdp=sdp_ratio, split=False, style_text=None, style_weight=0, port=port, emotion=emotion_text)
        return audio

    def switch_spk(self, choice):
        if choice == "Speaker_ID":
            return gr.update(label="Speaker_ID", value=0, visible=True, interactive=True), gr.update(label="Speaker_Name", visible=False, value="", interactive=True)
        else:
            return gr.update(label="Speaker_ID", value=0, visible=False, interactive=True), gr.update(label="Speaker_Name", visible=True, value="", interactive=True)

    def register_settings(self):
        options = []

        def auto_env_detect(bv2_pydir: str, config: Settings):
            bv2_pydir = bv2_pydir.strip('"')
            if bv2_pydir != "":
                if os.path.isfile(bv2_pydir):
                    bv2_pydir = os.path.abspath(bv2_pydir)
                elif bv2_pydir == 'python':
                    pass
                else:
                    gr.Warning(f"{i18n('Error, Invalid Path')}:{bv2_pydir}")
                    bv2_pydir = ""
            else:
                if os.path.isfile(os.path.join(current_path, "venv\\python.exe")) and "BERT" in current_path.upper():
                    bv2_pydir = os.path.join(current_path, "venv\\python.exe")
                    logger.info(f"{i18n('Env detected')}: GPT-SoVITS")
                else:
                    bv2_pydir = ""
            ###################
            if bv2_pydir != "" and config.query("bv2_dir", "") == "":
                config.shared_opts["bv2_dir"] = os.path.dirname(os.path.dirname(bv2_pydir))
            return bv2_pydir

        options.append(
            Shared_Options(
                "bv2_pydir",
                "",
                gr.Textbox,
                auto_env_detect,
                label=i18n('Python Interpreter Path for BV2'),
                interactive=True,
            )
        )
        options.append(
            Shared_Options(
                "bv2_dir",
                "",
                gr.Textbox,
                lambda v, c: v.strip('"'),
                label=i18n('Root Path of BV2'),
                interactive=True,
            )
        )
        options.append(
            Shared_Options(
                "gsv_args",
                "",
                gr.Textbox,
                label=i18n('Start Parameters'),
                interactive=True,
            )
        )
        return options

    def _UI(self):
        with gr.Row():
            with gr.Column():
                self.spkchoser = gr.Radio(label=i18n('Select Speaker ID or Speaker Name'), choices=['Speaker_ID', 'Speaker_Name'], value="Speaker_ID")
                with gr.Row():
                    self.model_id = gr.Number(label="Model_id", value=0, visible=True, interactive=True)
                    self.spkid = gr.Number(label="Speaker_ID", value=0, visible=True, interactive=True)
                    self.speaker_name = gr.Textbox(label="Speaker_Name", visible=False, interactive=True)
                self.language1 = gr.Dropdown(choices=['ZH', 'JP', 'EN', 'AUTO'], value='ZH', label="Language", interactive=True, allow_custom_value=False)
                with gr.Accordion(label=i18n('Advanced Parameters'), open=False):
                    self.sdp_ratio = gr.Slider(minimum=0, maximum=1, value=0.2, step=0.1, label="SDP Ratio")
                    self.noise_scale = gr.Slider(minimum=0.1, maximum=2, value=0.6, step=0.1, label="Noise Scale")
                    self.noise_scale_w = gr.Slider(minimum=0.1, maximum=2, value=0.8, step=0.1, label="Noise Scale W")
                    self.length_scale = gr.Slider(minimum=0.1, maximum=2, value=1, step=0.1, label="Length Scale")
                    self.emo_text = gr.Textbox(label="text prompt", interactive=True, value="")
                with gr.Row():
                    self.api_port1 = gr.Number(label="API Port", value=5000, visible=not self.server_mode, interactive=not self.server_mode)
        self.spkchoser.change(self.switch_spk, inputs=[self.spkchoser], outputs=[self.spkid, self.speaker_name])
        self.gen_btn = gr.Button(value=i18n('Generate Audio'), variant="primary", visible=True)
        BV2_ARGS = [
            self.language1,
            self.api_port1,
            self.model_id,
            self.spkid,
            self.speaker_name,
            self.sdp_ratio,
            self.noise_scale,
            self.noise_scale_w,
            self.length_scale,
            self.emo_text,
        ]
        return BV2_ARGS

    def arg_filter(self, *args):
        in_file, fps, offset, max_workers, language, port, mid, spkid, speaker_name, sdp_ratio, noise_scale, noise_scale_w, length_scale, emo_text = args
        pargs = (language, port, mid, spkid, speaker_name, sdp_ratio, noise_scale, noise_scale_w, length_scale, emo_text)
        kwargs = {'in_files': in_file, 'fps': fps, 'offset': offset, 'proj': "bv2", 'max_workers': max_workers}
        return pargs, kwargs
