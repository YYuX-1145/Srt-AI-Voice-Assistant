import gradio as gr
import os
import copy
import Sava_Utils
from . import i18n, logger
from .subtitle import Subtitle, Subtitles
from .utils import read_file, basename_no_ext
from .base_componment import Base_Componment
from .translator.ollama import Ollama


LANGUAGE = ["中文", "English", "日本語", "한국어", "Français"]
TRANSLATORS = {"ollama": Ollama()}
current_path = os.environ.get("current_path")


def merge_subtitles(subtitles_main: Subtitles, subtitles_tr: Subtitles):
    result = copy.deepcopy(subtitles_main)
    for s_main, s_tr in zip(result, subtitles_tr):
        s_main.text = s_main.text.strip() + "\n" + s_tr.text.strip()
    return result


def start_translation(in_files, language: str, batch_size: float, merge: bool, output_dir: str, interrupt_flag: Sava_Utils.utils.Flag, *args, translator=None):
    output_list = []
    message = ""
    if in_files is None:
        gr.Info(i18n('Please upload the subtitle file!'))
        return i18n('Please upload the subtitle file!'), output_list
    with interrupt_flag:
        for in_file in in_files:
            subtitle_list_ori = read_file(in_file.name)
            subtitle_list_tr = copy.deepcopy(subtitle_list_ori)
            tasks = TRANSLATORS[translator].construct_tasks(subtitle_list_ori, int(batch_size))
            try:
                result, msg = TRANSLATORS[translator].api(tasks, language, interrupt_flag, *args, file_name=os.path.basename(in_file.name))
                if interrupt_flag.is_set():
                    message += i18n('Canceled by user.')
                    break
                if msg:
                    message += f"{os.path.basename(in_file.name)}: {msg}\n"
                for sub, txt in zip(subtitle_list_tr, result):
                    sub.text = txt
                if Sava_Utils.config.server_mode:
                    output_path = os.path.join(os.path.dirname(in_file.name), f"{basename_no_ext(in_file.name)}_translated_to_{language}.srt")
                else:
                    output_path = os.path.join(output_dir, f"{basename_no_ext(in_file.name)}_translated_to_{language}.srt")
                subtitle_list_tr.export(fp=output_path, open_explorer=False, raw=True)
                output_list.append(output_path)
                if merge:
                    s_merged = merge_subtitles(subtitle_list_tr, subtitle_list_ori)
                    op = output_path[:-4] + "_merged.srt"
                    s_merged.export(fp=op, open_explorer=False, raw=True)
                    output_list.append(op)
            except Exception as e:
                err = f"{i18n('Failed to translate')} {os.path.basename(in_file.name)} :{str(e)}"
                gr.Warning(err)
                message += err + "\n"
                continue
    # os.system(f'explorer {output_dir}')
    return message.strip() if message else "OK", output_list


def merge_uploaded_sub(filelist_sup: list, filelist_inf: list, output_dir: str):
    if filelist_sup is None or filelist_inf is None:
        gr.Info(i18n('Please upload the subtitle file!'))
        return None, i18n('Please upload the subtitle file!')
    len_s = len(set(basename_no_ext(i.name) for i in filelist_sup))
    len_i = len(set(basename_no_ext(i.name) for i in filelist_inf))
    if len_s != len(filelist_sup) or len_i != len(filelist_inf):
        gr.Warning(i18n('Uploading files with the same name is not allowed.'))
        return None, i18n('Uploading files with the same name is not allowed.')
    if len(filelist_sup) != len(filelist_inf):
        gr.Warning(i18n('The number of files must match!'))
        return None, i18n('The number of files must match!')
    filelist_sup.sort(key=lambda x: basename_no_ext(x.name).rsplit('_', 3)[0])
    filelist_inf.sort(key=lambda x: basename_no_ext(x.name).rsplit('_', 3)[0])
    ret = []
    try:
        for f1, f2 in zip(filelist_sup, filelist_inf):
            if Sava_Utils.config.server_mode:
                output_path = os.path.join(os.path.dirname(f1.name), f"{basename_no_ext(f1.name)}_merged.srt")
            else:
                output_path = os.path.join(output_dir, f"{basename_no_ext(f1.name)}_merged.srt")
            x = merge_subtitles(read_file(f1.name), read_file(f2.name))
            x.export(fp=output_path, open_explorer=False, raw=True)
            ret.append(output_path)
    except Exception as e:
        errmsg = f"{i18n('An error occurred')}: {str(e)}"
        gr.Warning(errmsg)
        return ret, errmsg
    return ret, "OK"


class Translation_module(Base_Componment):
    def __init__(self):
        self.ui = False
        self.TRANSLATORS = TRANSLATORS
        self.config = None
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
            self.INTERRUPT_EVENT = gr.State(value=Sava_Utils.utils.Flag())
            with gr.Row():
                with gr.Column():
                    self.translation_upload = gr.File(label=i18n('Upload your subtitle files (multiple allowed).'), file_count="multiple", file_types=[".srt", ".csv", ".txt"])
                    with gr.Accordion(i18n('Subtitle Merge Tool'), open=False):
                        gr.Markdown(value=i18n('When uploading multiple files, the number of files and the filenames must match.'))
                        with gr.Row():
                            self.merge_upload1 = gr.File(label=i18n('Main Subtitle'), file_count="multiple", file_types=[".srt", ".csv", ".txt"])
                            self.merge_upload2 = gr.File(label=i18n('Secondary Subtitle'), file_count="multiple", file_types=[".srt", ".csv", ".txt"])
                        self.merge_btn = gr.Button(value=i18n('Merge'), variant='primary')
                    self.result = gr.Text(interactive=False, value="", label=i18n('Output Info'))
                    self.translation_output = gr.File(label=i18n('Output File'), file_count="multiple", interactive=False)
                    self.send_btn = gr.Button(value=i18n('Send output files to Main Page'), interactive=True)
                    self.send_btn.click(lambda x: [i.name for i in x if not i.name.endswith('_merged.srt')] if x is not None else x, inputs=[self.translation_output], outputs=[file_main])
                with gr.Column():
                    self.translation_target_language = gr.Dropdown(label=i18n('Specify Target Language'), choices=LANGUAGE, value=LANGUAGE[1], interactive=True)
                    self.batch_size = gr.Number(label="Batch Size", value=5, minimum=1, interactive=True)
                    self.merge_sub = gr.Checkbox(label=i18n('Generate merged subtitles'), value=False, interactive=True)
                    self.output_dir = gr.Text(value=os.path.join(current_path, "SAVAdata", "output"), label=i18n('File Output Path'), interactive=not Sava_Utils.config.server_mode, visible=not Sava_Utils.config.server_mode, max_lines=1)
                    self.translator = gr.Radio(label=i18n('Select Translator'), choices=[i for i in TRANSLATORS.keys()], value="ollama")
                    Base_args = [self.translation_upload, self.translation_target_language, self.batch_size, self.merge_sub, self.output_dir, self.INTERRUPT_EVENT]
                    with gr.Column():
                        v = True
                        assert self.config is not None
                        for i in TRANSLATORS.keys():
                            with gr.Column(visible=v) as tr_ui:
                                TRANSLATORS[i].update_cfg(config=self.config)
                                TRANSLATORS[i].getUI(*Base_args, output_info=self.result, output_files=self.translation_output)
                            v = False
                            self.menu.append(tr_ui)
                    stop_btn = gr.Button(value=i18n('Stop'), variant="stop")
                    stop_btn.click(lambda x: gr.Info(x.set()), inputs=[self.INTERRUPT_EVENT])
                self.translator.change(lambda x: [gr.update(visible=x == i) for i in TRANSLATORS.keys()], inputs=[self.translator], outputs=self.menu)
            self.merge_btn.click(merge_uploaded_sub, inputs=[self.merge_upload1, self.merge_upload2, self.output_dir], outputs=[self.translation_output, self.result])
