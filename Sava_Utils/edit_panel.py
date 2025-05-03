import gradio as gr
import os
import pickle
import re
from . import i18n
from .subtitle import Subtitles, Subtitle
import Sava_Utils

current_path = os.environ.get("current_path")


def load_page(subtitle_list, target_index=1):
    length = len(subtitle_list)
    if target_index > 1:
        value = min(target_index, ((length - 1) // Sava_Utils.config.num_edit_rows) * Sava_Utils.config.num_edit_rows + 1)
    else:
        value = target_index
    return gr.update(minimum=1, maximum=length if length > 0 else 1, interactive=True, value=value), *show_page(value, subtitle_list)


def show_page(page_start, subtitle_list: Subtitles):
    ret = []
    length = len(subtitle_list)
    pageend = page_start + Sava_Utils.config.num_edit_rows
    if pageend > length:
        pageend = length + 1
    if subtitle_list.proj is not None:
        if subtitle_list.proj == "bv2":
            btn = [gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)]
        elif subtitle_list.proj == "gsv":
            btn = [gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)]
        elif subtitle_list.proj == "mstts":
            btn = [gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)]
        else:
            btn = [gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)]
    else:
        btn = [gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)]
    for i in range(page_start - 1, pageend - 1):
        ret.append(gr.update(value=i, visible=False))
        ret.append(gr.update(value=subtitle_list[i].index, interactive=False, visible=True))
        ret.append(gr.update(value=subtitle_list[i].get_srt_time(), interactive=True, visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].text}", interactive=True, visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].speaker}", interactive=False, visible=True))
        ret.append(gr.update(value=subtitle_list.get_state(i), interactive=False, visible=True))
        ret += btn
    for i in range(Sava_Utils.config.num_edit_rows - pageend + page_start):
        ret.append(gr.update(value=-1, visible=False))
        ret.append(gr.update(value=-1, interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
        ret.append(gr.update(value="None", interactive=False, visible=False))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=False))
        ret += btn
    return ret + btn  # all regen btn*4


def play_audio(idx, subtitle_list):
    i = int(idx)
    p = os.path.join(subtitle_list.get_abs_dir(), f"{subtitle_list[i].index}.wav")
    if i == -1 or not os.path.exists(p):
        gr.Info(i18n('Not available!'))
        return None
    return p


def getworklist(value=None):
    try:
        assert not Sava_Utils.config.server_mode
        c = os.listdir(os.path.join(current_path, "SAVAdata", "temp", "workspaces"))
        return gr.update(choices=c, value=value if value else c[-1])
    except:
        if value:
            c = [value]
        else:
            c = [""]
        return gr.update(choices=c, value=value if value else "")


def getspklist(value="None"):
    try:
        c = ["None", *os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))]
        return gr.update(choices=c, value="None"), gr.update(choices=c, value=value)
    except:
        return gr.update(choices=["None"], value="None"), gr.update(choices=["None"], value="None")


def load_work(dirname):
    try:
        if dirname in ["", [], None]:
            raise Exception(i18n('Must not be empty!'))
        with open(os.path.join(current_path, "SAVAdata", "temp", "workspaces", dirname, "st.pkl"), 'rb') as f:
            subtitles = pickle.load(f)
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
            subtitles.insert(i + 1 + subtitles[i].copy_count, subtitles[i].copy())
        subtitles.sort(i, targetlist[-1] + 1 + subtitles[i].copy_count, partial=True)
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


def apply_spkmap2workspace(speaker_map, page, subtitles: Subtitles):
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n("There is no subtitle in the current workspace"))
        return show_page(page, Subtitles())
    spk_dict = {i[0]: i[-1] for i in speaker_map}
    for i in subtitles:
        try:
            i.speaker = spk_dict[str(i.speaker)]
            i.is_success = None
        except KeyError:    
            pass
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
    if name == "bv2":
        return [gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)]
    elif name == "gsv":
        return [gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)]
    elif name == "mstts":
        return [gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)]
    elif name == "custom":
        return [gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)]
    else:
        raise ""


def find_and_replace(subtitles: Subtitles, find_text_expression: str, target_text: str, exec_code:str, enable_re: bool, page_index:int=1):
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return load_page(Subtitles())
    if find_text_expression == '':
        gr.Warning(i18n('You must enter the text to find.'))
        return load_page(subtitles, page_index)
    replaced=[]
    if enable_re:
        try:
            pat = re.compile(find_text_expression)
            LEN = len(subtitles)
            for i,item in enumerate(reversed(subtitles)):
                index = LEN - i - 1
                item.text, count = pat.subn(target_text, item.text)
                if count != 0:
                    item.is_success = None
                    replaced.insert(0, item.index)
                    if exec_code and not Sava_Utils.config.server_mode:
                        exec(exec_code)
        except Exception as e:
            gr.Warning(f"Error: {str(e)}")
            return load_page(subtitles, page_index)
    else:
        LEN = len(subtitles)
        for i, item in enumerate(reversed(subtitles)):
            index =  LEN - i - 1
            x = item.text.replace(find_text_expression, target_text)
            if item.text != x:
                item.text = x
                item.is_success = None
                replaced.insert(0, item.index)
                try:
                    if exec_code and not Sava_Utils.config.server_mode:
                        exec(exec_code)
                except Exception as e:
                    gr.Warning(f"Error: {str(e)}")
                    return load_page(subtitles, page_index)
    gr.Info(f"Found and replaced {len(replaced)} subtitle(s).\n{replaced}")
    return load_page(subtitles, page_index)
