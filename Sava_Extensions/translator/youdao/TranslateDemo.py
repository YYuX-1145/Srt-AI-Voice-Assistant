import requests
from tqdm import tqdm
import json
import gradio as gr
import traceback
from .utils.AuthV3Util import addAuthParams

from . import *


LANGUAGE_map = {"中文": "zh-CHS", "English": "en", "日本語": "ja", "한국어": "ko", "Français": "fr"}


# 修改自官方示例
# modified from official code demo
class Youdao(Traducteur):

    def __init__(self, config=None):
        self.app_key = ""
        self.app_secret = ""
        super().__init__(i18n("Youdao"), config)

    def update_cfg(self, config):
        self.app_key = config.query("yd_app_key", "")
        self.app_secret = config.query("yd_app_secret", "")
        super().update_cfg(config)

    def register_settings(self):
        options = []
        options.append(
            Shared_Option(
                "yd_app_key",
                "",
                gr.Textbox,
                lambda x, _: x.strip(),
                label=i18n('APP_KEY'),
                interactive=True,
            )
        )
        options.append(
            Shared_Option(
                "yd_app_secret",
                "",
                gr.Textbox,
                lambda x, _: x.strip(),
                label=i18n('APP_SECRET'),
                interactive=True,
                type="password",
            )
        )
        return options

    def _UI(*args, **kwargs):
        return []

    def api(self, tasks, target_lang, interrupt_flag, *args, file_name: str = "", **kwargs) -> list[str] | tuple[list[str], str]:
        assert self.app_key
        assert self.app_secret
        ret = []
        for task in tqdm(tasks, desc=f"{i18n('Translating')}: {file_name}", total=len(tasks)):
            if interrupt_flag.is_set():
                return []
            header = {'Content-Type': 'application/x-www-form-urlencoded'}
            text = "\n\n".join(task)
            # 当然你也可以一条一条无上下文地翻译
            # Also, you can choose to translate sentence by sentence with context
            data = {'q': text, 'from': 'auto', 'to': LANGUAGE_map[target_lang]}
            addAuthParams(self.app_key, self.app_secret, data)
            try:
                response = requests.post('https://openapi.youdao.com/api', data, header)
                response.raise_for_status()
                result = json.loads(response.content)
                print(result)
                ret += result["translation"][0].split("\n\n")
            except:
                traceback.print_exc()
                raise
                for _ in range(len(task)):
                    ret.append("")
        return ret


# # 您的应用ID
# APP_KEY = ''
# # 您的应用密钥
# APP_SECRET = ''


# def createRequest():
#     '''
#     note: 将下列变量替换为需要请求的参数
#     '''
#     q = '待翻译文本'
#     lang_from = 'auto'
#     lang_to = '目标语言语种'

#     data = {'q': q, 'from': lang_from, 'to': lang_to}

#     addAuthParams(APP_KEY, APP_SECRET, data)

#     header = {'Content-Type': 'application/x-www-form-urlencoded'}
#     res = doCall('https://openapi.youdao.com/api', header, data, 'post')
#     print(str(res.content, 'utf-8'))


# def doCall(url, header, params, method):
#     if 'get' == method:
#         return requests.get(url, params)
#     elif 'post' == method:
#         return requests.post(url, params, header)

# # 网易有道智云翻译服务api调用demo
# # api接口: https://openapi.youdao.com/api
# if __name__ == '__main__':
#     createRequest()
