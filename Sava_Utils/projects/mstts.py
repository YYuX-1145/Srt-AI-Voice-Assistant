from .base import Projet
import os
import json
import requests
import gradio as gr
from .. import logger
from xml.etree import ElementTree

current_path = os.environ.get("current_path")

class MSTTS(Projet):
    def __init__(self):
        super().__init__("mstts")
        self.ms_access_token=None
        self.ms_speaker_info=None
        self.cfg_ms_region=None
        self.cfg_ms_key = None

    def update_cfg(self,config):
        self.cfg_ms_region=config.ms_region
        self.cfg_ms_key = config.ms_key

    def getms_speakers(self):
        if not os.path.exists(os.path.join(current_path,"SAVAdata", "ms_speaker_info.json")):
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
            for i in dataraw:
                if "zh" in i["Locale"]:
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

    def save_action(self, *args, text: str = None):
        language, speaker, style, role, rate, pitch = args
        audio = self.api(language, speaker, style, role, rate, pitch, text)
        return audio

    def before_gen_action(self,*args,**kwargs):
        self.update_cfg(kwargs.get("config"))
        if self.ms_access_token is None:
            self.getms_token()
            assert self.ms_access_token is not None,"获取微软token出错"
