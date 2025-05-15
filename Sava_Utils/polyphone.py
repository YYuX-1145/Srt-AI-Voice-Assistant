from .base_componment import Base_Componment
from . import i18n
import gradio as gr
import re
import numpy as np
import os

PATH = {"ZH": "GPT_SoVITS/text/g2pw/polyphonic.rep", "EN": "GPT_SoVITS/text/engdict-hot.rep"}
CACHE = {"ZH": "GPT_SoVITS/text/g2pw/polyphonic.pickle", "EN": "GPT_SoVITS/text/engdict_cache.pickle"}

ZH_SINGLE_PY_PATTERN = re.compile(r"[a-z]+[1-5]")
ZH_FORMAT_PATTERN = re.compile(r"^[a-z]+[1-5](?:\s+[a-z]+[1-5])*$")
# Raw: 一丝不苟: ['yi1', 'si1', 'bu4', 'gou3']
# Userinput: yi1 si1 bu4 gou3
EN_FORMAT_PATTERN = re.compile(r"^[A-Z]+[0-2]{0,1}(?:\s+[A-Z]+[0-2]{0,1})*$")
# CHATGPT CH AE1 T JH IY1 P IY1 T IY1
PATTERN = {"ZH": ZH_FORMAT_PATTERN, "EN": EN_FORMAT_PATTERN}


def read_fn_zh(x: str):
    key, content_raw = x.split(":")
    items = ZH_SINGLE_PY_PATTERN.findall(content_raw)
    result = ' '.join(items)
    return key.strip(), result
READ_FN = {"ZH": read_fn_zh, "EN": lambda x: [i.strip() for i in x.split(' ', 1)]}
WRITE_FN = {"ZH": lambda x, y: f"{x}: {str(y.split())}\n", "EN": lambda x, y: f"{x} {y}\n"}


class Polyphone(Base_Componment):
    def __init__(self, config):
        super().__init__(config)

    def update_cfg(self, config):
        self.gsv_dir = config.gsv_dir
        return super().update_cfg(config)

    def _UI(self, *args):
        with gr.TabItem(i18n('Polyphone Editor')):
            if self.server_mode:
                gr.Markdown(i18n('This function has been disabled!'))
                return
            gr.Markdown(i18n('POLYPHONE_NOTICE'))
            self.language = gr.Dropdown(label=i18n('Choose Language'), value=list(PATH.keys())[1], choices=list(PATH.keys()), interactive=True)
            self.tab = gr.DataFrame(datatype=["str", "str"], col_count=(2, 'fixed'), type="numpy", interactive=True, show_search='search')
            self.overwrite = gr.Checkbox(value=False, label=i18n('Overwrite instead of Append'))
            self.language.change(lambda: np.array([['', '']], dtype=str), outputs=[self.tab])
            with gr.Row():
                self.readbtn = gr.Button(value=i18n('Read'), variant="primary")
                self.readbtn.click(self.read_file, inputs=[self.language], outputs=[self.tab])
                self.writebtn = gr.Button(value=i18n('Save'), variant="primary")
                self.writebtn.click(self.save_file, inputs=[self.language, self.tab, self.overwrite])

    def read_file(self, lang):
        if self.gsv_dir in [None, ""] or not os.path.isdir(self.gsv_dir):
            gr.Warning(i18n('GSV root path has been not configured or does not exist.'))
            return None
        rows = []
        try:
            with open(os.path.join(self.gsv_dir, PATH[lang]), 'r', encoding='utf-8') as f:
                for line in f:
                    rows.append(READ_FN[lang](line))
        except Exception as e:
            gr.Warning(f"Error: {str(e)}")
        if len(rows) == 0:
            rows.append(['', ''])
        return np.array(rows, dtype=str)

    def save_file(self, lang, map, overwrite):
        try:
            if overwrite:
                content = {}
            else:
                x = self.read_file(lang)
                content = {i[0]: i[-1] for i in x if i[0]}
            for i in map:
                if i[0]:
                    i[-1] = i[-1].strip()
                    if PATTERN[lang].match(i[-1]):
                        content[i[0]] = i[-1]
                    else:
                        gr.Info(f"{i18n('Input format mismatch')}: {i[-1]}")
            with open(os.path.join(self.gsv_dir, PATH[lang]), 'w', encoding='utf-8') as f:
                for key, value in content.items():
                    f.write(WRITE_FN[lang](key, value))
            cachedir = os.path.join(self.gsv_dir, CACHE[lang])
            if os.path.isfile(cachedir):
                os.remove(cachedir)
            gr.Info(i18n('Done!'))
        except Exception as e:
            gr.Warning(f"Error: {str(e)}")
