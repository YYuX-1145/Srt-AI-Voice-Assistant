import gradio as gr
import os
from tqdm import tqdm
from .utils import read_prcsv, read_srt, read_txt
from .translator.ollama import Ollama


LANGUAGE = ["中文", "English", "日本語", "한국어", "Français"]
TRANSLATORS = {"ollama": Ollama()}


def start_translation(in_files, language, output_dir, *args, translator=None):
    if len(in_files) == 0:
        gr.Info("请上传字幕文件！")
        return "请上传字幕文件！"
    for in_file in in_files:
        if in_file.name[-4:].lower() == ".csv":
            subtitle_list = read_prcsv(in_file.name, fps=30, offset=0)
        elif in_file.name[-4:].lower() == ".srt":
            subtitle_list = read_srt(in_file.name, offset=0)
        elif in_file.name[-4:].lower() == ".txt":
            subtitle_list = read_txt(in_file.name)
        else:
            gr.Warning("未知的格式，请确保扩展名正确！")
            return "未知的格式，请确保扩展名正确！"
        with tqdm(total=len(subtitle_list), desc=f"正在翻译{in_file.name}"):
            for i in subtitle_list:
                translated_text = TRANSLATORS[translator].api(i.text, *args)
                if translated_text is not None:
                    i.text = translated_text
                else:
                    return "出错，翻译终止"
        subtitle_list.export(
            fp=os.path.join(
                output_dir, f"{in_file.name[:-4]}_translated_to_{language}.srt"
            ),
            open=False,
        )
    return "ok"


class Translation_module:
    def __init__(self):
        self.ui = False
        self.menu = []

    def UI(self):
        if not self.ui:
            self.ui = True
            self._UI()
        else:
            raise "err"

    def _UI(self):
        with gr.TabItem("字幕翻译"):
            with gr.Row():
                with gr.Column():
                    self.translation_upload = gr.File(
                        label="上传字幕(可多个)",
                        file_count="multiple",
                        type="file",
                        file_types=[".srt", ".csv", ".txt"],
                    )
                with gr.Column():
                    self.translation_target_language = gr.Dropdown(
                        label="选择目标语言",
                        choices=LANGUAGE,
                        value=LANGUAGE[1],
                        interactive=True,
                    )
                    self.translator = gr.Radio(
                        label="选择翻译器",
                        choices=[i for i in TRANSLATORS.keys()],
                        value="ollama",
                    )
                    Base_args = [
                    self.translation_upload,
                    self.translation_target_language,
                    self.translator,
                    ]
                    with gr.Column():
                        v = True
                        for i in TRANSLATORS.values():
                            x = gr.Column(i, visible=v)
                            with x:
                                i.getUI(*Base_args)
                            v = False
                        self.menu.append(x)
                self.translation_target_language.change(
                    lambda x: [
                        gr.update(visible=x == i.name) for i in TRANSLATORS.keys()
                    ],
                    inputs=[self.translator],
                    outputs=self.menu,
                )
                with gr.Column():
                    self.result = gr.Text(interactive=False, value="", label="输出信息")
