from . import TTSProjet
import requests
import gradio as gr
from ..utils import positive_int
from .. import logger
from .. import i18n
import os
import hashlib
import soundfile as sf
import time
import json
import wave
import shutil
import io

current_path = os.environ.get("current_path")

try:
    dict_language: dict = i18n('DICT_LANGUAGE')
    assert type(dict_language) is dict
    cut_method: dict = i18n('CUT_METHOD')
    assert type(cut_method) is dict
except:
    dict_language = {
        "Chinese": "all_zh",
        "Cantonese": "all_yue",
        "English": "en",
        "Japanese": "all_ja",
        "Korean": "all_ko",
        "Chinese-English Mix": "zh",
        "Cantonese-English Mix": "yue",
        "Japanese-English Mix": "ja",
        "Korean-English Mix": "ko",
        "Multi-Language Mix": "auto",
        "Multi-Language Mix (Cantonese)": "auto_yue",
    }
    cut_method = {
        "No cutting": "cut0",
        "Slice once every 4 sentences": "cut1",
        "Slice per 50 characters": "cut2",
        "Slice by Chinese punct": "cut3",
        "Slice by English punct": "cut4",
        "Slice by every punct": "cut5",
    }
dict_language_rev = {val: key for key, val in dict_language.items()}
# cut_method_rev={val:key for key,val in cut_method.items()}


def temp_ra(a: tuple):
    sr, wav = a
    name = hashlib.md5(wav.tobytes()).hexdigest() + ".wav"
    os.makedirs(os.path.join(current_path, "SAVAdata", "temp"), exist_ok=True)
    dir = os.path.join(current_path, "SAVAdata", "temp", name)
    if not os.path.exists(dir):
        sf.write(dir, wav, sr)
    return dir


def temp_aux_ra(a: bytes):
    name = hashlib.md5(a).hexdigest() + ".wav"
    os.makedirs(os.path.join(current_path, "SAVAdata", "temp"), exist_ok=True)
    dir = os.path.join(current_path, "SAVAdata", "temp", name)
    if not os.path.exists(dir):
        with open(dir, 'wb') as f:
            f.write(a)
    return dir


S2_MODEL_PATH = ["SoVITS_weights", "SoVITS_weights_v2", "SoVITS_weights_v3", "SoVITS_weights_v4"]
S2_PRETRAINED = [
    "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth",
    "GPT_SoVITS/pretrained_models/s2Gv3.pth",
    "GPT_SoVITS/pretrained_models/gsv-v4-pretrained/s2Gv4.pth",
]
S1_MODEL_PATH = ["GPT_weights", "GPT_weights_v2", "GPT_weights_v3", "GPT_weights_v4"]
S1_PRETRAINED = [
    "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
    "GPT_SoVITS/pretrained_models/s1v3.ckpt",
]


class GSV(TTSProjet):
    def __init__(self, config):
        self.gsv_fallback = False
        self.presets_list = ['None']
        self.current_sovits_model = dict()
        self.current_gpt_model = dict()
        self.refresh_presets_list()
        super().__init__("gsv", config)

    def update_cfg(self, config):
        self.gsv_fallback = config.gsv_fallback
        self.gsv_dir = config.gsv_dir
        super().update_cfg(config)

    def api(self, port, artts_name, **kwargs):
        try:
            if artts_name == "GPT_SoVITS":
                data_json = kwargs
                API_URL = f"http://127.0.0.1:{port}/tts"
                if self.gsv_fallback:
                    data_json = {
                        "refer_wav_path": kwargs["ref_audio_path"],
                        "prompt_text": kwargs["prompt_text"],
                        "prompt_language": kwargs["prompt_lang"],
                        "text": kwargs["text"],
                        "text_language": kwargs["text_lang"],
                        "cut_punc": kwargs["text_split_method"],
                        "top_k": kwargs["top_k"],
                        "top_p": kwargs["top_p"],
                        "temperature": kwargs["temperature"],
                        "speed": kwargs["speed_factor"],
                        "inp_refs": kwargs["aux_ref_audio_paths"],
                        "sample_steps": kwargs["sample_steps"],
                    }
                    API_URL = f"http://127.0.0.1:{port}/"
                #print(data_json)
                response = requests.post(url=API_URL, json=data_json)
                response.raise_for_status()
                return response.content
            else:
                # cosy2
                files = None
                if kwargs["ref_audio_path"] == '':
                    print("使用预训练音色模式...")
                    data_json = {
                        "spk_id": kwargs["prompt_text"],
                        "tts_text": kwargs["text"],
                        "speed": kwargs["speed_factor"],
                    }
                    API_URL = f"http://127.0.0.1:{port}/inference_sft"
                else:
                    print("使用3s克隆模式...")
                    data_json = {"prompt_text": kwargs["prompt_text"], "tts_text": kwargs["text"], "speed": kwargs["speed_factor"]}
                    API_URL = f"http://127.0.0.1:{port}/inference_zero_shot"
                    files = [('prompt_wav', ('prompt_wav', open(kwargs["ref_audio_path"], 'rb'), 'application/octet-stream'))]
                response = requests.request("GET", url=API_URL, data=data_json, files=files, stream=False)
                response.raise_for_status()
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(24000)  # cosy api does not provide sr.
                    wav_file.writeframes(response.content)
                return wav_buffer.getvalue()
        except Exception as e:
            err = f"{i18n('An error has occurred. Please check if the API is running correctly. Details')}: {e}  "
            try:
                err += f"{i18n('Returned Message')}:{response.json()}"
            except:
                pass
            logger.error(err)
            return None

    def save_action(self, *args, text: str = None):
        artts_proj, text_language, port, refer_wav_path, aux_refer_wav_path, prompt_text, prompt_language, batch_size, batch_threshold, fragment_interval, speed_factor, top_k, top_p, temperature, repetition_penalty, sample_steps,parallel_infer, split_bucket, text_split_method, gpt_path, sovits_path = args
        port = positive_int(port)
        audio = self.api(
            port,
            artts_name=artts_proj,
            text=text,
            text_lang=text_language,  ###language->lang
            ref_audio_path=refer_wav_path,  # ref
            aux_ref_audio_paths=aux_refer_wav_path,
            prompt_text=prompt_text,
            prompt_lang=prompt_language,  #
            batch_size=batch_size,
            batch_threshold=batch_threshold,
            fragment_interval=fragment_interval,
            speed_factor=speed_factor,
            top_k=top_k,
            top_p=top_p,
            seed=-1,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
            parallel_infer=parallel_infer,
            split_bucket=split_bucket,
            text_split_method=text_split_method,
            sample_steps = sample_steps,
            media_type="wav",
            streaming_mode=False,
        )
        return audio

    def _UI(self):
        with gr.TabItem("AR-TTS"):
            self.choose_ar_tts = gr.Radio(label=i18n('Select TTS Project'), choices=["GPT_SoVITS", "CosyVoice2"], value="GPT_SoVITS", interactive=not self.server_mode)
            self.language2 = gr.Dropdown(choices=list(dict_language.keys()), value=list(dict_language.keys())[5], label=i18n('Inference text language'), interactive=True, allow_custom_value=False)
            with gr.Accordion(i18n('Reference Audio'), open=True):                
                self.refer_audio = gr.Audio(label=i18n('Main Reference Audio'))
                self.aux_ref_audio = gr.File(label=i18n('Auxiliary Reference Audios'), file_types=['.wav'], file_count="multiple", type="binary")
                with gr.Row():
                    self.refer_text = gr.Textbox(label=i18n('Transcription of Main Reference Audio'), value="", placeholder=i18n('Transcription | Pretrained Speaker (Cosy)'))
                    self.refer_lang = gr.Dropdown(choices=list(dict_language.keys()), value=list(dict_language.keys())[0], label=i18n('Language of Main Reference Audio'), interactive=True, allow_custom_value=False)
            with gr.Accordion(i18n('Switch Models'), open=False, visible=not self.server_mode):
                self.sovits_path = gr.Dropdown(value="", label=f"Sovits {i18n('Model Path')}", interactive=True, allow_custom_value=True, choices=[''])
                self.gpt_path = gr.Dropdown(value="", label=f"GPT {i18n('Model Path')}", interactive=True, allow_custom_value=True, choices=[''])
                with gr.Row():                
                    self.switch_gsvmodel_btn = gr.Button(value=i18n('Switch Models'), variant="primary", scale=4)
                    self.scan_gsvmodel_btn = gr.Button(value=i18n('🔄️'), variant="secondary", scale=1, min_width=60)
                    self.scan_gsvmodel_btn.click(self.find_gsv_models,inputs=[],outputs=[self.sovits_path,self.gpt_path])
            with gr.Row():
                self.api_port2 = gr.Number(label="API Port", value=9880, interactive=not self.server_mode, visible=not self.server_mode)
            # self.choose_ar_tts.change(lambda x:9880 if x=="GPT_SoVITS" else 50000,inputs=[self.choose_ar_tts],outputs=[self.api_port2])
            with gr.Accordion(i18n('Advanced Parameters'), open=False):
                self.batch_size = gr.Slider(minimum=1, maximum=200, step=1, label="batch_size", value=20, interactive=True)
                self.batch_threshold = gr.Slider(minimum=0, maximum=1, step=0.01, label="batch_threshold", value=0.75, interactive=True)
                self.fragment_interval = gr.Slider(minimum=0.01, maximum=1, step=0.01, label=i18n('Fragment Interval(sec)'), value=0.3, interactive=True)
                self.speed_factor = gr.Slider(minimum=0.25, maximum=4, step=0.05, label="speed_factor", value=1.0, interactive=True)
                self.top_k = gr.Slider(minimum=1, maximum=100, step=1, label="top_k", value=5, interactive=True)
                self.top_p = gr.Slider(minimum=0, maximum=1, step=0.05, label="top_p", value=1, interactive=True)
                self.temperature = gr.Slider(minimum=0, maximum=1, step=0.05, label="temperature", value=1, interactive=True)
                self.repetition_penalty = gr.Slider(minimum=0, maximum=2, step=0.05, label="repetition_penalty", value=1.35, interactive=True)
                self.sample_steps = gr.Dropdown(label="Sample_Steps", value='32', choices=['16','32','48','64','96','128'], interactive=True, show_label=True, allow_custom_value=False)
                with gr.Row():
                    self.parallel_infer = gr.Checkbox(label="Parallel_Infer", value=True, interactive=True, show_label=True)
                    self.split_bucket = gr.Checkbox(label="Split_Bucket", value=True, interactive=True, show_label=True)                
                self.how_to_cut = gr.Radio(label=i18n('How to cut'), choices=list(cut_method.keys()), value=list(cut_method.keys())[0], interactive=True)
            with gr.Accordion(i18n('Presets'), open=False):
                self.choose_presets = gr.Dropdown(label="", value="None", choices=self.presets_list, interactive=True, allow_custom_value=True)
                self.desc_presets = gr.Textbox(label="", placeholder=i18n('(Optional) Description'), interactive=True)
                with gr.Row():
                    self.save_presets_btn = gr.Button(value="💾", variant="primary", min_width=60)
                    self.refresh_presets_btn = gr.Button(value="🔄️", variant="secondary", min_width=60)
                    self.del_preset_btn = gr.Button(value="🗑️", variant="stop", min_width=60)
                    self.refresh_presets_btn.click(self.refresh_presets_list, outputs=[self.choose_presets])
                    self.del_preset_btn.click(self.del_preset, inputs=[self.choose_presets], outputs=[self.choose_presets])
                preset_args = [
                    self.choose_presets,
                    self.choose_ar_tts,
                    self.desc_presets,
                    self.api_port2,
                    self.refer_audio,
                    self.refer_text,
                    self.refer_lang,
                    self.aux_ref_audio,
                    self.sovits_path,
                    self.gpt_path,
                ]
                self.save_presets_btn.click(self.save_preset, inputs=preset_args, outputs=[self.choose_presets])
            with gr.Row():
                self.gen_btn2 = gr.Button(value=i18n('Generate Audio'), variant="primary", visible=True)
            self.switch_gsvmodel_btn.click(self.switch_gsvmodel, inputs=[self.sovits_path, self.gpt_path, self.api_port2], outputs=[])
            self.choose_presets.change(self.load_preset, inputs=[self.choose_presets], outputs=preset_args[1:])
        GSV_ARGS = [
            self.choose_ar_tts,
            self.language2,
            self.api_port2,
            self.refer_audio,
            self.aux_ref_audio,
            self.refer_text,
            self.refer_lang,
            self.batch_size,
            self.batch_threshold,
            self.fragment_interval,
            self.speed_factor,
            self.top_k,
            self.top_p,
            self.temperature,
            self.repetition_penalty,
            self.sample_steps,
            self.parallel_infer,
            self.split_bucket,            
            self.how_to_cut,
            self.gpt_path,
            self.sovits_path,
        ]
        return GSV_ARGS

    def arg_filter(self, *args):
        in_file, fps, offset, max_workers, artts_proj, language, port, refer_audio, aux_ref_audio, refer_text, refer_lang, batch_size, batch_threshold, fragment_interval, speed_factor, top_k, top_p, temperature, repetition_penalty, sample_steps, parallel_infer, split_bucket, text_split_method, gpt_path, sovits_path = args
        if artts_proj == "GPT_SoVITS":
            if refer_audio is None:
                gr.Warning(i18n('You must upload Main Reference Audio'))
                raise Exception(i18n('You must upload Main Reference Audio'))
        if refer_audio is not None:
            refer_audio_path = temp_ra(refer_audio)
        else:
            refer_audio_path = ''
        aux_ref_audio_path = [temp_aux_ra(i) for i in aux_ref_audio] if aux_ref_audio is not None else []
        pargs = (artts_proj, dict_language[language], port, refer_audio_path, aux_ref_audio_path, refer_text, dict_language[refer_lang], batch_size, batch_threshold, fragment_interval, speed_factor, top_k, top_p, temperature, repetition_penalty, int(sample_steps),parallel_infer, split_bucket, cut_method[text_split_method], gpt_path, sovits_path)
        kwargs = {'in_files': in_file, 'fps': fps, 'offset': offset, 'proj': "gsv", 'max_workers': max_workers}
        return pargs, kwargs

    def before_gen_action(self, *args, **kwargs):
        if args[0] == 'GPT_SoVITS':
            force = kwargs.get("force", True)
            notify = kwargs.get("notify", False)
            self.switch_gsvmodel(gpt_path=args[-2], sovits_path=args[-1], port=args[2], force=force, notify=notify)

    def save_preset(self, name, artts_name, description, port, ra, ara, rt, rl, sovits_path, gpt_path):
        try:
            if self.server_mode:
                raise RuntimeError(i18n('This function has been disabled!'))
            if name in ["None", None, "", []]:
                gr.Info(i18n('Please enter a valid name!'))
                return
            preset = ARPreset(name, artts_name, description, port, ra, ara, rt, rl, sovits_path, gpt_path)
            preset.save()
            time.sleep(0.1)
            gr.Info(f"{i18n('Preset saved successfully')}:{name}")
        except Exception as e:
            gr.Warning(f"Error: {e}")
        return self.refresh_presets_list(reset=False)

    def load_preset(self, name):
        try:
            if name in ['None', None, "", []] or not os.path.exists(os.path.join(current_path, "SAVAdata", "presets", name)):
                return gr.update(), gr.update(label="", value="", placeholder=i18n('(Optional) Description'), interactive=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

            dir = os.path.join(current_path, "SAVAdata", "presets", name)
            preset = ARPreset.from_dict(json.load(open(os.path.join(dir, "info.json"), encoding="utf-8")))

            if preset.AR_TTS_Project_name == 'GPT_SoVITS' and preset.sovits_path != "" and preset.gpt_path != "":
                if not self.switch_gsvmodel(sovits_path=preset.sovits_path, gpt_path=preset.gpt_path, port=preset.port, force=False):
                    gr.Warning(i18n('Failed to switch model'))
            gr.Info(i18n('Preset has been loaded.'))
            return preset.to_list()[1:]
        except Exception as e:
            gr.Warning(f"Error: {e}")
            return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    def switch_gsvmodel(self, sovits_path, gpt_path, port, force=True, notify=True):
        if self.server_mode:
            if force and notify:
                gr.Warning(i18n('This function has been disabled!'))
            return True
        if port not in self.current_sovits_model:
            self.current_sovits_model[port] = None
        if port not in self.current_gpt_model:
            self.current_gpt_model[port] = None
        if not force and sovits_path == self.current_sovits_model[port] and gpt_path == self.current_gpt_model[port]:
            if notify:
                gr.Info(i18n('Models are not switched. If you need to switch, please manually click the button.'))
            return True
        if sovits_path == "" or gpt_path == "":
            if force and notify:
                gr.Info(i18n('Please specify the model path!'))
            return False
        gr.Info(i18n('Switching Models...'))
        try:
            data_json = {
                "sovits_model_path": sovits_path.strip('"'),
                "gpt_model_path": gpt_path.strip('"'),
            }
            for x in data_json.values():
                if not os.path.isfile(x):
                    gr.Warning(i18n('Model Paths seem to be invalid, which could lead to errors!'))
                if os.path.isdir(x):
                    raise gr.Error(i18n('You have incorrectly entered a folder path!'))
            # print(data_json)
            port = int(port)
            if self.gsv_fallback:
                API_URL = f'http://127.0.0.1:{port}/set_model/'
                response = requests.post(url=API_URL, json=data_json)
                response.raise_for_status()
            else:
                API_URL = f'http://127.0.0.1:{port}/set_gpt_weights'
                response = requests.get(url=API_URL, params={"weights_path": data_json["gpt_model_path"]})
                response.raise_for_status()
                API_URL = f'http://127.0.0.1:{port}/set_sovits_weights'
                response = requests.get(url=API_URL, params={"weights_path": data_json["sovits_model_path"]})
                response.raise_for_status()
            self.current_sovits_model[port] = sovits_path
            self.current_gpt_model[port] = gpt_path
            gr.Info(i18n('Models switched successfully'))
            logger.info(f"{i18n('Models switched successfully')}:{data_json}")
            return True
        except Exception as e:
            err = f"GPT-SoVITS {i18n('Failed to switch model')},{i18n('Error details')}: {e}"
            try:
                err += f"{i18n('error message received')}:{response.json()}"
            except:
                pass
            gr.Warning(err)
            logger.error(err)
            return False

    def find_gsv_models(self):
        if self.gsv_dir in ["", None] or not os.path.isdir(self.gsv_dir):
            gr.Warning(i18n('GSV root path has been not configured or does not exist.'))
            return gr.update(choices=['']), gr.update(choices=[''])
        s1 = ['']
        s2 = ['']
        for item in S2_PRETRAINED:
            m = os.path.join(self.gsv_dir, item)
            if os.path.exists(m):
                s2.append(m)
        for item in S2_MODEL_PATH:
            cd = os.path.join(self.gsv_dir, item)
            if os.path.isdir(cd):
                s2 += [os.path.join(self.gsv_dir, item, i) for i in os.listdir(cd) if i.endswith(".pth")]
        for item in S1_PRETRAINED:
            m = os.path.join(self.gsv_dir, item)
            if os.path.exists(m):
                s1.append(m)
        for item in S1_MODEL_PATH:
            cd = os.path.join(self.gsv_dir, item)
            if os.path.isdir(cd):
                s1 += [os.path.join(self.gsv_dir, item, i) for i in os.listdir(cd) if i.endswith(".ckpt")]
        return gr.update(choices=s2), gr.update(choices=s1)

    def del_preset(self, name):
        try:
            if self.server_mode:
                raise RuntimeError(i18n('This function has been disabled!'))
            if name not in ['', None, "None"]:
                shutil.rmtree(os.path.join(current_path, "SAVAdata", "presets", name))
                gr.Info(f"{i18n('Successfully deleted')}:{name}")
            else:
                gr.Info(i18n('Please select a valid preset!'))
        except Exception as e:
            gr.Warning(f"Error: {str(e)}")
        return self.refresh_presets_list()

    def refresh_presets_list(self, reset=True):
        self.presets_list = ['None']
        try:
            preset_dir = os.path.join(current_path, "SAVAdata", "presets")
            if os.path.isdir(preset_dir):
                self.presets_list += [i for i in os.listdir(preset_dir) if os.path.isdir(os.path.join(preset_dir, i))]
            else:
                logger.info(i18n('No preset available'))
                gr.Info(i18n('No preset available'))
        except Exception as e:
            self.presets_list = ["None"]
            err = f"Error: {e}"
            logger.error(err)
            gr.Warning(err)
        time.sleep(0.1)
        if reset:
            return gr.update(value="None", choices=self.presets_list)
        else:
            return gr.update(choices=self.presets_list)


class ARPreset:
    def __init__(self, name: str = "", AR_TTS_Project_name: str = 'GPT_SoVITS', description: str = "", port: int = 9880, reference_audio_path: tuple = None, reference_audio_text: str = "", reference_audio_lang: str = "", auxiliary_audios: list = [], sovits_path: str = "", gpt_path: str = ""):
        self.name = name
        self.AR_TTS_Project_name = AR_TTS_Project_name
        self.description = description
        self.port = int(port)
        self.reference_audio_path = reference_audio_path
        self.reference_audio_text = reference_audio_text
        self.reference_audio_lang = dict_language[reference_audio_lang] if reference_audio_lang not in dict_language_rev else reference_audio_lang
        self.auxiliary_audios = auxiliary_audios
        self.sovits_path = sovits_path.strip('"')
        self.gpt_path = gpt_path.strip('"')

    def to_list(self):
        val = self.to_dict()
        val["reference_audio_lang"] = dict_language_rev[val["reference_audio_lang"]]
        return [val[x] for x in val.keys()]

    def to_dict(self):
        return self.__dict__

    def save(self):
        dir = os.path.join(current_path, "SAVAdata", "presets", self.name)
        os.makedirs(dir, exist_ok=True)
        if self.reference_audio_path is not None:
            sr, wav = self.reference_audio_path
            sf.write(os.path.join(dir, "reference_audio.wav"), wav, sr)
            self.reference_audio_path = "reference_audio.wav"
        idx = 1
        aux_list = []
        if self.auxiliary_audios not in [None, []]:
            for i in self.auxiliary_audios:
                try:
                    with open(os.path.join(dir, f"aux_{idx}.wav"), "wb") as f:
                        f.write(i)
                    aux_list.append(f"aux_{idx}.wav")
                    idx += 1
                except Exception as ex:
                    print(ex)
                    continue
        self.auxiliary_audios = aux_list
        dic = self.to_dict()
        with open(os.path.join(current_path, "SAVAdata", "presets", self.name, "info.json"), "w", encoding="utf-8") as f:
            json.dump(dic, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, dict):
        x = cls(**dict)
        if x.reference_audio_path and os.path.exists(os.path.join(current_path, "SAVAdata", "presets", x.name, "reference_audio.wav")):
            x.reference_audio_path = os.path.join(current_path, "SAVAdata", "presets", x.name, "reference_audio.wav")
        if x.auxiliary_audios not in [None, []]:
            aux_audio = [os.path.join(current_path, "SAVAdata", "presets", x.name, i) for i in x.auxiliary_audios if os.path.exists(os.path.join(current_path, "SAVAdata", "presets", x.name, i))]
            if len(aux_audio) != len(x.auxiliary_audios):
                gr.Warning(i18n('Partial auxiliary reference audio is missing!'))
            x.auxiliary_audios = aux_audio
        return x
