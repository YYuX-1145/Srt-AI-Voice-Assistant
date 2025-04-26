from .base_componment import Base_Componment
from . import i18n
import gradio as gr
import re
import numpy as np
import os

PATH = {"ZH": "GPT_SoVITS/text/g2pw/polyphonic.rep", "EN": "GPT_SoVITS/text/engdict-hot.rep"}
CACHE = {"ZH": "GPT_SoVITS/text/g2pw/polyphonic.pickle", "EN": "GPT_SoVITS/text/engdict_cache.pickle"}


def read_zh_poly(gsvpath):
    with open(os.path.join(gsvpath,PATH["ZH"]), 'r', encoding='utf-8') as f:
        for lines in f:
            text, pronunciation = lines.strip().split(": ")


class Polyphone(Base_Componment):
    def __init__(self, config):
        super().__init__(config)

    def update_cfg(self, config):
        self.gsv_dir = config.gsv_dir
        return super().update_cfg(config)

    def _UI(self, *args):
        if self.server_mode:
            gr.Markdown(i18n('This function has been disabled!'))
            return
        with gr.TabItem(i18n('Polyphone Editor')):
            self.language = gr.Dropdown(label=i18n('Choose Language'),value=list(PATH.keys())[1], choices=list(PATH.keys()),interactive=True)
            self.tab = gr.DataFrame(datatype=["str", "str"], col_count=(2, 'fixed'), type="numpy", interactive=True)
        with gr.Row():
            self.readbtn = gr.Button(value=i18n('Read Polyphone File'),variant="primary")
            self.readbtn = gr.Button(value=i18n('Write Polyphone File'),variant="primary")
    

    def read_file(self,lang):
        if self.gsv_dir in [None,""]:
            return 
