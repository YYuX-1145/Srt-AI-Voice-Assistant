import gradio as gr
import os
import Sava_Utils
from . import i18n,logger
from .utils import read_file
from .base_componment import Base_Componment
from .translator.ollama import Ollama


LANGUAGE = ["中文", "English", "日本語", "한국어", "Français"]
TRANSLATORS = {"ollama": Ollama()}
current_path = os.environ.get("current_path")


def start_translation(in_files, language, batch_size, output_dir, *args, translator=None):
    output_list = []
    message = ""
    if in_files is None:
        gr.Info(i18n('Please upload the subtitle file!'))
        return i18n('Please upload the subtitle file!'), output_list
    for in_file in in_files:
        subtitle_list = read_file(in_file.name)
        tasks = TRANSLATORS[translator].construct_tasks(subtitle_list,int(batch_size))
        try:
            result,msg = TRANSLATORS[translator].api(tasks, language, *args, file_name=os.path.basename(in_file.name))
            if msg:
                message += f"{os.path.basename(in_file.name)}: {msg}\n"
            for sub, txt in zip(subtitle_list, result):
                sub.text = txt
            output_path = os.path.join(output_dir, f"{os.path.basename(in_file.name)[:-4]}_translated_to_{language}.srt")
            subtitle_list.export(fp=output_path, open_explorer=False, raw=True)
            output_list.append(output_path)
        except Exception as e:
            err = f"{i18n('Failed to translate')} {in_file.name} :{str(e)}"
            gr.Warning(err)
            message += err + "\n"
            continue

    # os.system(f'explorer {output_dir}')
    return message.strip() if message else "OK", output_list


class Translation_module(Base_Componment):
    def __init__(self, config):
        self.ui = False
        self.config = config
        self.menu = []

    def update_cfg(self, config):
        self.config = config
        for i in TRANSLATORS.values():
            i.update_cfg(config=config)
        super().update_cfg(config)

    def getUI(self, *args):
        if not self.ui:
            self.ui = True
            self._UI(*args)
        else:
            raise "err"

    def _UI(self, file_main):
        with gr.TabItem(i18n('Subtitle Translation')):
            with gr.Row():
                with gr.Column():
                    self.translation_upload = gr.File(label=i18n('Upload your subtitle files (multiple allowed).'), file_count="multiple", file_types=[".srt", ".csv", ".txt"])
                    self.result = gr.Text(interactive=False, value="", label=i18n('Output Info'))
                    self.translation_output = gr.File(label=i18n('Output File'), file_count="multiple", interactive=False)
                    self.send_btn = gr.Button(value=i18n('Send output files to Main Page'), interactive=True)
                    self.send_btn.click(lambda x: [i.name for i in x] if x is not None else x, inputs=[self.translation_output], outputs=[file_main])
                with gr.Column():
                    self.translation_target_language = gr.Dropdown(label=i18n('Specify Target Language'), choices=LANGUAGE, value=LANGUAGE[1], interactive=True)
                    self.batch_size = gr.Number(label="Batch Size", value=5, minimum=1, interactive=True)
                    self.output_dir = gr.Text(value=os.path.join(current_path, "SAVAdata", "output"), label=i18n('File Output Path'), interactive=not Sava_Utils.config.server_mode, visible=not Sava_Utils.config.server_mode, max_lines=1)
                    self.translator = gr.Radio(label=i18n('Select Translator'), choices=[i for i in TRANSLATORS.keys()], value="ollama")
                    Base_args = [self.translation_upload, self.translation_target_language, self.batch_size, self.output_dir]
                    with gr.Column():
                        v = True
                        for i in TRANSLATORS.keys():
                            x = gr.Column(visible=v)
                            with x:
                                TRANSLATORS[i].update_cfg(config=self.config)
                                TRANSLATORS[i].getUI(*Base_args, output_info=self.result, output_files=self.translation_output)
                            v = False
                        self.menu.append(x)
                self.translation_target_language.change(lambda x: [gr.update(visible=x == i) for i in TRANSLATORS.keys()], inputs=[self.translator], outputs=self.menu)
