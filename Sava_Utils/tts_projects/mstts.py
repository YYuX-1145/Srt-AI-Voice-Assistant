from . import TTSProjet
import os
import re
import json
import requests
import gradio as gr
from .. import logger
from xml.etree import ElementTree

current_path = os.environ.get("current_path")

class MSTTS(TTSProjet):
    def __init__(self):
        super().__init__("mstts")
        self.ms_access_token=None
        self.ms_speaker_info=None
        self.cfg_ms_region=None
        self.cfg_ms_key = None
        self.ms_lang_option = ""

    def update_cfg(self,config):
        self.cfg_ms_region=config.ms_region
        self.cfg_ms_key = config.ms_key
        self.ms_lang_option=config.ms_lang_option

    def getms_speakers(self):
        #if not os.path.exists(os.path.join(current_path,"SAVAdata", "ms_speaker_info.json")):
            if not os.path.exists(os.path.join(current_path,"SAVAdata", "ms_speaker_info_raw.json")):
                try:
                    assert self.cfg_ms_key not in [None,""], "please fill in your key to get MSTTS speaker list."
                    headers = {"Ocp-Apim-Subscription-Key": self.cfg_ms_key}
                    url = f"https://{self.cfg_ms_region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
                    data = requests.get(url=url, headers=headers)
                    data.raise_for_status()
                    info = json.loads(data.content)
                    with open(os.path.join(current_path,"SAVAdata", "ms_speaker_info_raw.json"),"w",encoding="utf-8",) as f:
                        json.dump(info, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    err = f"无法下载微软TTS说话人列表。报错内容: {e}"
                    gr.Warning(err)
                    logger.error(err)
                    self.ms_speaker_info = {}
                    return None
            dataraw = json.load(open(os.path.join(current_path,"SAVAdata", "ms_speaker_info_raw.json"), encoding="utf-8"))  # list
            classified_info = {}
            #target_language=["zh","ja","en","ko","fr"]
            target_language=re.split(r'(?<=[,，])| ',self.ms_lang_option)
            target_language=[x.strip() for x in target_language if x.strip()]
            if len(target_language)==0:
                target_language=[""]
            for i in dataraw:
                if any(lan in i["Locale"] for lan in target_language):
                    if i["Locale"] not in classified_info.keys():
                        classified_info[i["Locale"]] = {}
                    classified_info[i["Locale"]][i["LocalName"]] = i
            with open(os.path.join("SAVAdata", "ms_speaker_info.json"), "w", encoding="utf-8") as f:
                json.dump(classified_info, f, indent=2, ensure_ascii=False)
            self.ms_speaker_info = json.load(open(os.path.join("SAVAdata", "ms_speaker_info.json"), encoding="utf-8"))

    def getms_token(self):
        fetch_token_url = (
        f"https://{self.cfg_ms_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        )
        headers = {"Ocp-Apim-Subscription-Key": self.cfg_ms_key}
        try:
            response = requests.post(fetch_token_url, headers=headers)
            response.raise_for_status()
            self.ms_access_token = str(response.text)
        except Exception as e:
            err = f"获取微软token出错，检查密钥、服务器状态和网络连接。报错内容: {e}"
            gr.Warning(err)
            logger.error(err)
            self.ms_access_token = None

    def api(self, language, speaker, style, role, rate, pitch, text, **kwargs):
        xml_body = ElementTree.Element("speak", version="1.0")
        xml_body.set("xmlns", "http://www.w3.org/2001/10/synthesis")
        xml_body.set("xmlns:mstts", "https://www.w3.org/2001/mstts")
        xml_body.set("xml:lang", "zh-CN")
        voice = ElementTree.SubElement(xml_body, "voice")
        voice.set("name", self.ms_speaker_info[language][speaker]["ShortName"])  # Short name
        express = ElementTree.SubElement(voice, "express-as")
        express.set("style", style)
        express.set("role", role)
        prosody = ElementTree.SubElement(express, "prosody")
        prosody.set("rate", f"{int(100-rate*100)}%")
        prosody.set("pitch", f"{int(100-pitch*100)}%")
        prosody.text = text
        body = ElementTree.tostring(xml_body)
        try:
            if self.ms_access_token is None:
                self.getms_token()
                assert self.ms_access_token is not None, "获取微软token出错"
            headers = {
            "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm",
            "Content-Type": "application/ssml+xml",
            "Authorization": "Bearer " + self.ms_access_token,
            "User-Agent": "py_sava",
            }
            response = requests.post(
                url=f"https://{self.cfg_ms_region}.tts.speech.microsoft.com/cognitiveservices/v1",
                headers=headers,
                data=body,
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            err = f"微软TTS出错，检查密钥、服务器状态和网络连接。报错内容: {e}"
            logger.error(err)
            return None

    def _UI(self):
        with gr.Column():
            self.ms_refresh_btn=gr.Button(value="刷新说话人列表",variant="secondary")
            if self.ms_speaker_info == {}:
                self.ms_languages=gr.Dropdown(label="选择语言",value=None,choices=[],allow_custom_value=False,interactive=True)
                self.ms_speaker=gr.Dropdown(label="选择说话人",value=None,choices=[],allow_custom_value=False,interactive=True)
            else:
                choices = list(self.ms_speaker_info.keys())
                self.ms_languages=gr.Dropdown(label="选择语言",value=choices[0],choices=choices,allow_custom_value=False,interactive=True)
                choices = list(self.ms_speaker_info[choices[0]].keys())
                self.ms_speaker=gr.Dropdown(label="选择说话人",value=None,choices=choices,allow_custom_value=False,interactive=True)
                del choices
            with gr.Row():
                self.ms_style=gr.Dropdown(label="说话风格",value=None,choices=[],allow_custom_value=False,interactive=True)
                self.ms_role=gr.Dropdown(label="角色扮演",value=None,choices=[],allow_custom_value=False,interactive=True)
            self.ms_speed = gr.Slider(minimum=0.2,maximum=2,step=0.01,label="语速",value=1,interactive=True)
            self.ms_pitch = gr.Slider(minimum=0.5,maximum=1.5,step=0.01,label="音调",value=1,interactive=True)
            gr.Markdown(value="""使用微软TTS需要联网，请先前往设置页填入服务区和密钥才可以使用。请注意每个月的免费额度。""")
            gr.Markdown(value="""[【关于获取密钥：打开链接后请仔细阅读 先决条件 】](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech)""")                               
            self.gen_btn3=gr.Button(value="生成",variant="primary",visible=True)
            self.ms_refresh_btn.click(self.ms_refresh, outputs=[self.ms_languages])
            self.ms_languages.change(self.display_ms_spk,inputs=[self.ms_languages],outputs=[self.ms_speaker])
            self.ms_speaker.change(self.display_style_role,inputs=[self.ms_languages,self.ms_speaker],outputs=[self.ms_style,self.ms_role])  
            MSTTS_ARGS=[self.ms_languages,self.ms_speaker,self.ms_style,self.ms_role,self.ms_speed,self.ms_pitch]  
        return MSTTS_ARGS  

    def save_action(self, *args, text: str = None):
        language, speaker, style, role, rate, pitch = args
        audio = self.api(language, speaker, style, role, rate, pitch, text)
        return audio

    def before_gen_action(self,*args,**kwargs):
        self.update_cfg(kwargs.get("config"))
        if self.ms_access_token is None:
            self.getms_token()
            assert self.ms_access_token is not None,"获取微软token出错"

    def arg_filter(self,*args):
        input_file,fps,offset,workers,ms_language,ms_speaker,ms_style,ms_role,ms_speed,ms_pitch=args        
        if ms_speaker in [None,"",[]]:
            gr.Info("请选择说话人")
            raise Exception("请选择说话人")
        if self.cfg_ms_key=="": 
            gr.Warning("请配置密钥!")
            raise Exception("请配置密钥")
        pargs=(ms_language,ms_speaker,ms_style,ms_role,ms_speed,ms_pitch)
        kwargs={'in_file':input_file,'sr':None,'fps':fps,'offset':offset,'proj':"mstts",'max_workers':workers}
        return pargs,kwargs

    def ms_refresh(self):  # language
        self.getms_speakers()
        if self.ms_speaker_info == {}:
            return gr.update(value=None, choices=[], allow_custom_value=False)
        choices = list(self.ms_speaker_info.keys())
        return gr.update(value=choices[0], choices=choices, allow_custom_value=False)

    def display_ms_spk(self,language):  # speaker
        if language in [None, ""]:
            return gr.update(value=None, choices=[], allow_custom_value=False)
        choices = list(self.ms_speaker_info[language].keys())
        return gr.update(value=choices[0], choices=choices, allow_custom_value=False)

    def display_style_role(self,language, speaker):
        if language in [None, ""] or speaker in [None, ""]:
            return gr.update(value=None, choices=[], allow_custom_value=False), gr.update(value=None, choices=[], allow_custom_value=False )
        try:
            choices1 = ["Default"] + self.ms_speaker_info[language][speaker]["StyleList"]
        except KeyError:
            choices1 = ["Default"]
        try:
            choices2 = ["Default"] + self.ms_speaker_info[language][speaker]["RolePlayList"]
        except KeyError:
            choices2 = ["Default"]
        return (gr.update(value=choices1[0], choices=choices1, allow_custom_value=False),gr.update(value=choices2[0], choices=choices2, allow_custom_value=False))
