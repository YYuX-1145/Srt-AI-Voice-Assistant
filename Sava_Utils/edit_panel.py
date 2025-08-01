import gradio as gr
import os
import pickle
import re
import builtins
import traceback
import time
from io import StringIO
from . import i18n
from .subtitle import Subtitles, Subtitle
from .tts_engines import TTS_UI_LOADER
import Sava_Utils

current_path = os.environ.get("current_path")


def load_page(subtitle_list, target_index=1):
    length = len(subtitle_list)
    if target_index > 1:
        value = min(target_index, ((length - 1) // Sava_Utils.config.num_edit_rows) * Sava_Utils.config.num_edit_rows + 1)
    else:
        value = target_index
    return gr.update(minimum=1, maximum=length if length > 0 else 1, interactive=True, value=value), *show_page(value, subtitle_list)


BTN_VISIBLE_DICT = TTS_UI_LOADER.get_btn_visible_dict()
NUM_PROJ = len(TTS_UI_LOADER.components)


def show_page(page_start, subtitle_list: Subtitles):
    ret = []
    length = len(subtitle_list)
    pageend = page_start + Sava_Utils.config.num_edit_rows
    if pageend > length:
        pageend = length + 1
    btn = BTN_VISIBLE_DICT[subtitle_list.proj]
    for i in range(page_start - 1, pageend - 1):
        subtitle = subtitle_list[i]
        ret.append(gr.update(value=i, visible=False))
        ret.append(gr.update(value=subtitle.index, interactive=False, visible=True))
        ret.append(gr.update(value=subtitle.get_srt_time(), interactive=True, visible=True))
        ret.append(gr.update(value=f"{subtitle.text}", interactive=True, visible=True))
        ret.append(gr.update(value=f"{subtitle.speaker}", interactive=False, visible=True))
        ret.append(gr.update(value=subtitle.get_state(), interactive=False, visible=True))
        ret += btn
    for i in range(Sava_Utils.config.num_edit_rows - pageend + page_start):
        ret.append(gr.update(value=-1, visible=False))
        ret.append(gr.update(value=-1, interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
        ret.append(gr.update(value="None", interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
        ret += btn
    ret += btn  # all regen btn
    return ret


def load_single_line(subtitle_list: Subtitles, index):  # with page slider
    ret = [gr.update()]
    i = int(index)
    if i >= 0 and i < len(subtitle_list):
        subtitle = subtitle_list[i]
        ret.append(gr.update(value=i, visible=False))
        ret.append(gr.update(value=subtitle.index, interactive=False, visible=True))
        ret.append(gr.update(value=subtitle.get_srt_time(), interactive=True, visible=True))
        ret.append(gr.update(value=f"{subtitle.text}", interactive=True, visible=True))
        ret.append(gr.update(value=f"{subtitle.speaker}", interactive=False, visible=True))
        ret.append(gr.update(value=subtitle.get_state(), interactive=False, visible=True))
    else:
        ret.append(gr.update(value=-1, visible=False))
        ret.append(gr.update(value=-1, interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
        ret.append(gr.update(value="None", interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
    return ret


def play_audio(idx, subtitle_list: Subtitles):
    yield None
    i = int(idx)
    if i == -1 or not subtitle_list.dir:
        gr.Info(i18n('Not available!'))
    else:
        p = os.path.join(subtitle_list.get_abs_dir(), f"{subtitle_list[i].index}.wav")
        if os.path.exists(p):
            time.sleep(0.05)
            yield p
        else:
            gr.Info(i18n('Not available!'))


def refworklist():
    try:
        assert not Sava_Utils.config.server_mode
        return os.listdir(os.path.join(current_path, "SAVAdata", "workspaces"))
    except:
        return []


def getworklist(value=None):
    if not Sava_Utils.config.server_mode:
        workspaces_list_choices = refworklist()
        c = workspaces_list_choices if len(workspaces_list_choices) > 0 else [""]
        return gr.update(choices=c, value=value if value else c[-1])
    else:
        c = [value] if value else [""]
        return gr.update(choices=c, value=c[0])


def refspklist():
    try:
        return ["None", *os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))]
    except:
        return ["None"]


def getspklist(value="None"):
    speaker_list_choices = refspklist()
    return gr.update(choices=speaker_list_choices, value=value if len(speaker_list_choices) > 1 else "None")


def load_workspace(dirname):
    try:
        if dirname in ["", [], None]:
            raise Exception(i18n('Must not be empty!'))
        with open(os.path.join(current_path, "SAVAdata", "workspaces", dirname, "st.pkl"), 'rb') as f:
            subtitles:Subtitles = pickle.load(f)
            subtitles.dir = dirname
            if subtitles.proj not in BTN_VISIBLE_DICT:
                gr.Warning(f"TTS Engine Not Found: {subtitles.proj}")
                subtitles.proj = None
        return subtitles, *load_page(subtitles)
    except Exception as e:
        gr.Warning(f"Error: {str(e)}")
        return Subtitles(), *load_page(Subtitles())


def delete_subtitle(page, subtitles: Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return *checklist, *load_page(Subtitles())
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    targetlist = []
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and indexlist[i] != -1:
            targetlist.append(int(indexlist[i]))
    if len(targetlist) == 0:
        gr.Info(i18n('No subtitles selected.'))
    targetlist.sort(reverse=True)
    for idx in targetlist:
        subtitles.pop(idx)
    return *[False for i in range(Sava_Utils.config.num_edit_rows)], *load_page(subtitles, target_index=page)


def merge_subtitle(page, subtitles: Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return *checklist, *load_page(Subtitles())
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    targetlist = []
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and indexlist[i] != -1:
            targetlist.append(int(indexlist[i]))
    if (len(targetlist)) > 1:
        max_i = max(targetlist)
        min_i = min(targetlist)
        subtitles[min_i].end_time_raw = subtitles[max_i].end_time_raw
        subtitles[min_i].end_time = subtitles[max_i].end_time
        for i in range(min_i, max_i):
            if subtitles[min_i].text[-1] not in [" ", "\n", "!", ".", "?", "。", "！", "？"]:
                subtitles[min_i].text += ','
            subtitles[min_i].text += subtitles[min_i + 1].text
            subtitles.pop(min_i + 1)
        subtitles[min_i].is_success = None
    else:
        gr.Info(i18n('Please select both the start and end points!'))
    return *[False for i in range(Sava_Utils.config.num_edit_rows)], *load_page(subtitles, target_index=page)


def copy_subtitle(page, subtitles: Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return *checklist, *load_page(Subtitles())
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    targetlist = []
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and indexlist[i] != -1:
            targetlist.append(int(indexlist[i]))
    if len(targetlist) == 0:
        gr.Info(i18n('No subtitles selected.'))
    else:
        for i in reversed(targetlist):
            subtitle = subtitles[i]
            _ = subtitle.index.split('-')
            _.append(0)
            offset = sum(x >= int(_[1]) for x in subtitle.copy_count)
            subtitles.insert(i + offset, subtitles[i].copy())
    return *[False for i in range(Sava_Utils.config.num_edit_rows)], *load_page(subtitles, target_index=page)


def apply_start_end_time(page, subtitles: Subtitles, *args):
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return show_page(page, Subtitles())
    indexlist = [int(i) for i in args[: Sava_Utils.config.num_edit_rows]]
    timelist = args[Sava_Utils.config.num_edit_rows :]
    # for i in range(page-1,min(page+Sava_Utils.config.num_edit_rows-1,len(subtitles)-1)):
    for i, title_index in enumerate(indexlist):
        try:
            if title_index != -1:
                subtitles[title_index].reset_srt_time(timelist[i])
        except ValueError as e:
            gr.Info(str(e))
    subtitles.dump()
    return show_page(page, subtitles)


def apply_spk(speaker, page, subtitles: Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return *checklist, *show_page(page, Subtitles())
    if speaker in ["", "None", []]:
        speaker = None
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    assert len(checklist) == len(indexlist)
    subtitles.default_speaker = speaker
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and int(indexlist[i]) != -1 and subtitles[int(indexlist[i])].speaker != speaker:
            subtitles[int(indexlist[i])].speaker = speaker
            subtitles[int(indexlist[i])].is_success = None
    subtitles.dump()
    return *checklist, *show_page(page, subtitles)


def apply_spkmap2workspace(spk_map: dict, page, subtitles: Subtitles):
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n("There is no subtitle in the current workspace"))
        return show_page(page, Subtitles())
    spk_dict = {key: value for key, value in spk_map.items() if key != value}
    for i in subtitles:
        key = i.speaker if i.speaker else "None"
        if key in spk_dict:
            i.speaker = spk_dict[key]
            i.is_success = None
    gr.Info(i18n('Done!'))
    return show_page(page, subtitles)


def del_spk(name):
    try:
        if Sava_Utils.config.server_mode:
            raise RuntimeError(i18n('This function has been disabled!'))
        assert name not in ["", "None", [], None], i18n('Must not be empty!')
        os.remove(os.path.join(current_path, "SAVAdata", "speakers", name))
        gr.Info(f"{i18n('Delete')}:{name}")
    except Exception as e:
        gr.Warning(f"Error: {str(e)}")
    return getspklist()


def switch_spk_proj(name):
    return BTN_VISIBLE_DICT[name]


def match_text(text: str, target: str | re.Pattern):
    if isinstance(target, str):
        return target in text
    else:
        return target.search(text)


def find_next(subtitles: Subtitles, text_to_find: str, enable_re: bool, page_index: int = 1, *checkbox_list_and_real_index_list):
    checkbox_list = checkbox_list_and_real_index_list[: Sava_Utils.config.num_edit_rows]
    real_index_list = checkbox_list_and_real_index_list[Sava_Utils.config.num_edit_rows :]
    ck = [False for _ in range(Sava_Utils.config.num_edit_rows)]
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return *ck, *load_page(Subtitles())
    if text_to_find == '':
        gr.Warning(i18n('You must enter the text to find.'))
        return *ck, *[gr.update() for _ in range((6 + NUM_PROJ) * Sava_Utils.config.num_edit_rows + 1 + NUM_PROJ)]
    current_index = real_index_list[checkbox_list.index(True)] if any(checkbox_list) else real_index_list[0] - 1
    if enable_re:
        try:
            pat = re.compile(text_to_find)
        except Exception as e:
            gr.Warning(f"Error: {str(e)}")
            return *ck, *load_page(subtitles, 1)
    else:
        pat = text_to_find
    for index in range(current_index + 1, len(subtitles)):
        if match_text(subtitles[index].text, pat):
            next_index = index
            ck[next_index % Sava_Utils.config.num_edit_rows] = True
            target_page = (next_index // Sava_Utils.config.num_edit_rows) * Sava_Utils.config.num_edit_rows + 1
            if target_page == page_index:
                page_content = [gr.update() for _ in range((6 + NUM_PROJ) * Sava_Utils.config.num_edit_rows + 1 + NUM_PROJ)]
            else:
                page_content = load_page(subtitles, target_page)
            return *ck, *page_content
    gr.Info(i18n('No more results'))
    return *ck, *load_page(subtitles, 1)


def find_and_replace(subtitles: Subtitles, find_text_expression: str, target_text: str, exec_code: str, enable_re: bool, page_index: int = 1):
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return load_page(Subtitles())
    if find_text_expression == '':
        gr.Warning(i18n('You must enter the text to find.'))
        return load_page(subtitles, page_index)
    replaced = []
    if enable_re:
        try:
            pat = re.compile(find_text_expression)
            LEN = len(subtitles)
            for i, item in enumerate(reversed(subtitles)):
                index = LEN - i - 1
                item.text, count = pat.subn(target_text, item.text)
                if count != 0:
                    item.is_success = None
                    replaced.insert(0, item.index)
                    if exec_code and Sava_Utils.config.enable_advanced_scripting and not Sava_Utils.config.server_mode:
                        exec(exec_code)
        except Exception as e:
            gr.Warning(f"Error: {str(e)}")
            return load_page(subtitles, page_index)
    else:
        LEN = len(subtitles)
        for i, item in enumerate(reversed(subtitles)):
            index = LEN - i - 1
            x = item.text.replace(find_text_expression, target_text)
            if item.text != x:
                item.text = x
                item.is_success = None
                replaced.insert(0, item.index)
                try:
                    if exec_code and Sava_Utils.config.enable_advanced_scripting and not Sava_Utils.config.server_mode:
                        exec(exec_code)
                except Exception as e:
                    gr.Warning(f"Error: {str(e)}")
                    return load_page(subtitles, page_index)
    gr.Info(f"Found and replaced {len(replaced)} subtitle(s).\n{replaced}")
    return load_page(subtitles, page_index)

SCRIPT_DIR = os.path.join(current_path, "SAVAdata", "scripts")
def ref_script_choices():
    choices = os.listdir(SCRIPT_DIR) if os.path.isdir(SCRIPT_DIR) else []
    choices.insert(0, "")
    return gr.update(choices=choices)


def load_script_content(name: str):
    if name in [None, "", []]:
        gr.Info(i18n('Must not be empty!'))
        return gr.update()
    name = name.strip()
    try:
        with open(os.path.join(SCRIPT_DIR, name), "r", encoding='utf-8') as f:
            ret = f.read()
        return ret
    except Exception as e:
        gr.Warning(str(e))
        return gr.update()


def save_script_content(content: str, name: str):
    if name in [None, "", []]:
        gr.Info(i18n('Must not be empty!'))
        return ref_script_choices()
    name = name.strip()
    try:
        os.makedirs(SCRIPT_DIR, exist_ok=True)
        with open(os.path.join(SCRIPT_DIR, name), "w", encoding='utf-8') as f:
            f.write(content)
        gr.Info(f"{i18n('Saved successfully')}: {name}")
    except Exception as e:
        gr.Warning(str(e))
    return ref_script_choices()


def rm_script(name):
    name = name.strip()
    if name in [None, "", []]:
        gr.Info(i18n('Must not be empty!'))
        return ref_script_choices()
    try:
        os.remove(os.path.join(SCRIPT_DIR, name))
        gr.Info(f"{name} {i18n('was removed successfully.')}")
    except Exception as e:
        gr.Warning(str(e))
    return ref_script_choices()


def run_script(page: int, subtitles: Subtitles, code: str):
    message = ""
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return message, *load_page(Subtitles())
    fg_out = StringIO()

    def print(*args, **kwargs):
        if "file" in kwargs:
            return builtins.print(*args, **kwargs)
        return builtins.print(*args, file=fg_out, **kwargs)

    try:
        exec(code)
        message += fg_out.getvalue()
    except:
        traceback.print_exc(file=fg_out)
        message += '\n' + fg_out.getvalue()
    return message, *load_page(subtitles, target_index=page)
