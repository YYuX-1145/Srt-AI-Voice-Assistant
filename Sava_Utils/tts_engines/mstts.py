from . import TTSProjet
from ..settings import Settings, Shared_Option
import os
import re
import json
import requests
import gradio as gr
from .. import logger, i18n
from xml.etree import ElementTree

current_path = os.environ.get("current_path")
SERVER_Regions = [
    'southafricanorth',
    'eastasia',
    'southeastasia',
    'australiaeast',
    'centralindia',
    'japaneast',
    'japanwest',
    'koreacentral',
    'canadacentral',
    'northeurope',
    'westeurope',
    'francecentral',
    'germanywestcentral',
    'norwayeast',
    'swedencentral',
    'switzerlandnorth',
    'switzerlandwest',
    'uksouth',
    'uaenorth',
    'brazilsouth',
    'qatarcentral',
    'centralus',
    'eastus',
    'eastus2',
    'northcentralus',
    'southcentralus',
    'westcentralus',
    'westus',
    'westus2',
    'westus3',
]


class MSTTS(TTSProjet):
    def __init__(self):
        self.ms_speaker_info = {}
        self.cfg_ms_region = ""
        self.cfg_ms_key = ""
        self.ms_lang_option = ""
        super().__init__("Azure-TTS(Microsoft)", title="Azure-TTS(Microsoft)")

    def update_cfg(self, config):
        self.cfg_ms_region = config.query("ms_region")
        self.cfg_ms_key = config.query("ms_key")
        self.ms_lang_option = config.query("ms_lang_option")
        super().update_cfg(config)

    def register_settings(self):
        options = []
        options.append(
            Shared_Option(
                "ms_region",
                "eastasia",
                gr.Dropdown,
                allow_custom_value=True,
                choices=SERVER_Regions,
                label="Server Region",
                interactive=True,
            )
        )
        options.append(
            Shared_Option(
                "ms_key",
                "",
                gr.Textbox,
                lambda v, c: v.strip(),
                label=i18n('API=KEY Warning: Key is stored in plaintext. DO NOT send the key to others or share your configuration file!'),
                interactive=True,
                type="password",
            )
        )
        options.append(
            Shared_Option(
                "ms_lang_option",
                "",
                gr.Textbox,
                label=i18n('Select required languages, separated by commas or spaces.'),
                interactive=True,
                placeholder="zh en",
            )
        )
        return options

    def getms_speakers(self):
        if not os.path.exists(os.path.join(current_path, "SAVAdata", "ms_speaker_info_raw.json")):
            try:
                assert self.cfg_ms_key, i18n('Please fill in your key to get MSTTS speaker list.')
                headers = {"Ocp-Apim-Subscription-Key": self.cfg_ms_key}
                url = f"https://{self.cfg_ms_region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
                data = requests.get(url=url, headers=headers)
                data.raise_for_status()
                info = json.loads(data.content)
                with open(os.path.join(current_path, "SAVAdata", "ms_speaker_info_raw.json"), "w", encoding="utf-8") as f:
                    json.dump(info, f, indent=2, ensure_ascii=False)
            except Exception as e:
                err = f"{i18n('Can not get speaker list of MSTTS. Details')}: {e}"
                gr.Warning(err)
                logger.warning(err)
                self.ms_speaker_info = {}
                return None
        dataraw = json.load(open(os.path.join(current_path, "SAVAdata", "ms_speaker_info_raw.json"), encoding="utf-8"))  # list
        classified_info = {}
        target_language = re.split(r'(?<=[,，])| ', self.ms_lang_option)
        target_language = [x.strip() for x in target_language if x.strip()]
        if len(target_language) == 0:
            target_language = [""]
        for i in dataraw:
            if any(lan in i["Locale"] for lan in target_language):
                if i["Locale"] not in classified_info:
                    classified_info[i["Locale"]] = {}
                classified_info[i["Locale"]][i["LocalName"]] = i
        with open(os.path.join("SAVAdata", "ms_speaker_info.json"), "w", encoding="utf-8") as f:
            json.dump(classified_info, f, indent=2, ensure_ascii=False)
        self.ms_speaker_info = json.load(open(os.path.join("SAVAdata", "ms_speaker_info.json"), encoding="utf-8"))

    def api(self, language, speaker, style, role, rate, pitch, text, **kwargs):
        xml_body = ElementTree.Element("speak", version="1.0")
        xml_body.set("xml:lang", "en-US")
        voice = ElementTree.SubElement(xml_body, "voice")
        voice.set("name", self.ms_speaker_info[language][speaker]["ShortName"])  # Short name
        express = ElementTree.SubElement(voice, "express-as")
        express.set("style", style)
        express.set("role", role)
        prosody = ElementTree.SubElement(express, "prosody")
        prosody.set("rate", f"{int((rate - 1) * 100)}%")
        prosody.set("pitch", f"{int((pitch- 1) * 100)}%")
        prosody.text = text
        body = ElementTree.tostring(xml_body)
        try:
            assert self.cfg_ms_key, i18n('Please fill in your key!')
            headers = {
                "Ocp-Apim-Subscription-Key": self.cfg_ms_key,
                "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm",
                "Content-Type": "application/ssml+xml",
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
            err = f"Error: {e}"
            logger.error(err)
            return None

    def _UI(self):
        self.ms_refresh()
        with gr.Column():
            self.ms_refresh_btn = gr.Button(value=i18n('Refresh speakers list'), variant="secondary")
            if self.ms_speaker_info == {}:
                self.ms_languages = gr.Dropdown(label=i18n('Choose Language'), value=None, choices=[], allow_custom_value=False, interactive=True)
                self.ms_speaker = gr.Dropdown(label=i18n('Choose Your Speaker'), value=None, choices=[], allow_custom_value=False, interactive=True)
            else:
                choices = list(self.ms_speaker_info.keys())
                self.ms_languages = gr.Dropdown(label=i18n('Choose Language'), value=choices[0], choices=choices, allow_custom_value=False, interactive=True)
                choices = list(self.ms_speaker_info[choices[0]].keys())
                self.ms_speaker = gr.Dropdown(label=i18n('Choose Your Speaker'), value=None, choices=choices, allow_custom_value=False, interactive=True)
                del choices
            with gr.Row():
                self.ms_style = gr.Dropdown(label=i18n('Style'), value=None, choices=[], allow_custom_value=False, interactive=True)
                self.ms_role = gr.Dropdown(label=i18n('Role'), value=None, choices=[], allow_custom_value=False, interactive=True)
            self.ms_speed = gr.Slider(minimum=0.2, maximum=2, step=0.01, label=i18n('Speed'), value=1, interactive=True)
            self.ms_pitch = gr.Slider(minimum=0.5, maximum=1.5, step=0.01, label=i18n('Pitch'), value=1, interactive=True)
            gr.Markdown(value=i18n('MSTTS_NOTICE'))
            self.gen_btn = gr.Button(value=i18n('Generate Audio'), variant="primary", visible=True)
            self.ms_refresh_btn.click(self.ms_refresh, outputs=[self.ms_languages])
            self.ms_languages.change(self.display_ms_spk, inputs=[self.ms_languages], outputs=[self.ms_speaker])
            self.ms_speaker.change(self.display_style_role, inputs=[self.ms_languages, self.ms_speaker], outputs=[self.ms_style, self.ms_role])
            MSTTS_ARGS = [self.ms_languages, self.ms_speaker, self.ms_style, self.ms_role, self.ms_speed, self.ms_pitch]
        return MSTTS_ARGS

    def save_action(self, *args, text: str = None):
        language, speaker, style, role, rate, pitch = args
        audio = self.api(language, speaker, style, role, rate, pitch, text)
        return audio

    def arg_filter(self, *args):
        ms_language, ms_speaker, ms_style, ms_role, ms_speed, ms_pitch = args
        if ms_speaker in [None, "", []]:
            gr.Info(i18n('Please Select Your Speaker!'))
            raise Exception(i18n('Please Select Your Speaker!'))
        if self.cfg_ms_key == "":
            gr.Warning(i18n('Please fill in your key!'))
            raise Exception(i18n('Please fill in your key!'))
        pargs = (ms_language, ms_speaker, ms_style, ms_role, ms_speed, ms_pitch)
        return pargs

    def ms_refresh(self):  # language
        self.getms_speakers()
        if self.ms_speaker_info == {}:
            return gr.update(value=None, choices=[], allow_custom_value=False)
        choices = list(self.ms_speaker_info.keys())
        return gr.update(value=choices[0], choices=choices, allow_custom_value=False)

    def display_ms_spk(self, language):  # speaker
        if language in [None, ""]:
            return gr.update(value=None, choices=[], allow_custom_value=False)
        choices = list(self.ms_speaker_info[language].keys())
        return gr.update(value=choices[0], choices=choices, allow_custom_value=False)

    def display_style_role(self, language, speaker):
        if language in [None, ""] or speaker in [None, ""]:
            return gr.update(value=None, choices=[], allow_custom_value=False), gr.update(value=None, choices=[], allow_custom_value=False)
        choices1 = ["Default"] + self.ms_speaker_info[language][speaker].get("StyleList", [])
        choices2 = ["Default"] + self.ms_speaker_info[language][speaker].get("RolePlayList", [])
        return (gr.update(value=choices1[0], choices=choices1, allow_custom_value=False), gr.update(value=choices2[0], choices=choices2, allow_custom_value=False))
