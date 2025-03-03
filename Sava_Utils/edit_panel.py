import gradio as gr
import os
import pickle
from .subtitle import Subtitles
import Sava_Utils

current_path = os.environ.get("current_path")

def load_page(subtitle_list,target_index=1):
    length=len(subtitle_list)
    if length==0:
        gr.Info("上次生成未成功，请先完成生成流程！")
    if target_index > 1:
        value=min(target_index,((length-1)//Sava_Utils.config.num_edit_rows) + 1)
    else:
        value=target_index
    return gr.update(minimum=1,maximum=length if length>0 else 1,interactive=True,value=value),*show_page(1,subtitle_list)

def show_page(page_start,subtitle_list):
    ret=[]
    length=len(subtitle_list)
    pageend = page_start + Sava_Utils.config.num_edit_rows
    if pageend>length:
        pageend=length+1
    if subtitle_list.proj is not None:
        if subtitle_list.proj=="bv2":
            btn=[gr.update(visible=True),gr.update(visible=False),gr.update(visible=False),gr.update(visible=False)]
        elif subtitle_list.proj=="gsv":
            btn=[gr.update(visible=False),gr.update(visible=True),gr.update(visible=False),gr.update(visible=False)]
        elif subtitle_list.proj=="mstts":  
            btn=[gr.update(visible=False),gr.update(visible=False),gr.update(visible=True),gr.update(visible=False)]
        else:
            btn=[gr.update(visible=False),gr.update(visible=False),gr.update(visible=False),gr.update(visible=True)]
    else:
        btn=[gr.update(visible=True),gr.update(visible=False),gr.update(visible=False),gr.update(visible=False)]     
    for i in range(page_start-1,pageend-1):
        ret.append(gr.update(value=i,visible=False))
        ret.append(gr.update(value=subtitle_list[i].index,interactive=False,visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].start_time_raw} -> {subtitle_list[i].end_time_raw} | {subtitle_list[i].start_time:.2f} -> {subtitle_list[i].end_time:.2f}",visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].text}",interactive=True,visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].speaker}",interactive=False,visible=True))
        ret.append(gr.update(value=subtitle_list.get_state(i),interactive=False,visible=True))
        ret+=btn
    for i in range(Sava_Utils.config.num_edit_rows - pageend + page_start):
        ret.append(gr.update(value=-1,visible=False))
        ret.append(gr.update(value=-1,interactive=False,visible=True))
        ret.append(gr.update(value="NO INFO",visible=True))
        ret.append(gr.update(value="NO INFO",interactive=False,visible=True))
        ret.append(gr.update(value="None",interactive=False,visible=True))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=True))
        ret+=btn        
    return ret

def play_audio(idx, subtitle_list):
    i = int(idx)
    if i == -1 or not subtitle_list[i].is_success:
        gr.Info("Not available !")
        return None
    return os.path.join(subtitle_list.get_abs_dir(), f"{subtitle_list[i].index}.wav")

def getworklist():
    try:
        c=os.listdir(os.path.join(current_path,"SAVAdata","temp","work"))
        return gr.update(choices=c,value=c[-1])
    except:
        return gr.update(choices=[""])


def getspklist():
    try:
        c = ["None", *os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))]
        return gr.update(choices=c, value="None")
    except:
        return gr.update(choices=["None"],value="None")


def load_work(dirname):
    try:
        if dirname in ["",[],None]:
            raise Exception("路径不得为空！")
        with open(os.path.join(current_path, "SAVAdata", "temp", "work",dirname,"st.pkl"), 'rb') as f:
            subtitles = pickle.load(f)
        return subtitles,*load_page(subtitles)
    except Exception as e:
        gr.Warning(f"出错：{str(e)}")
        return Subtitles(), *load_page(Subtitles())


def delete_subtitle(page, subtitles: Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles)==0:
        gr.Info("当前没有字幕")
        return  *checklist,*load_page(Subtitles()),Subtitles()
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    targetlist = []
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and indexlist[i]!=-1:
            targetlist.append(int(indexlist[i]))
    targetlist.sort(reverse=True)
    for idx in targetlist:
        subtitles.pop(idx)
    return *checklist, *load_page(subtitles,target_index=page), subtitles


def merge_subtitle(page,subtitles:Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles) == 0:
        gr.Info("当前没有字幕")
        return *checklist, *load_page(Subtitles()), Subtitles()
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    targetlist = []
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and indexlist[i] != -1:
            targetlist.append(int(indexlist[i]))
    if(len(targetlist))>1:
        max_i=max(targetlist)
        min_i=min(targetlist)
        for i in range(min_i+1,max_i+1):
            if subtitles[min_i].text[-1] not in [" ", "\n", "!",".","?","。","！","？"]:
                subtitles[min_i].text+=','
            subtitles[min_i].text += subtitles[i].text
            subtitles[min_i].end_time_raw = subtitles[i].end_time_raw
            subtitles[min_i].end_time = subtitles[i].end_time
            subtitles.pop(min_i+1)
    else:
        gr.Info("请选择起点和终点！")
    return *checklist, *load_page(subtitles, target_index=page), subtitles


def apply_spk(speaker, page, subtitles: Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles)==0:
        gr.Info("当前没有字幕")
        return  *checklist,*show_page(page,Subtitles()),Subtitles()
    if speaker in ["","None",[]]:
        speaker=None
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    assert len(checklist)==len(indexlist)
    if speaker is not None and speaker not in subtitles.speakers.keys():
        subtitles.speakers[speaker]=0
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and int(indexlist[i])!=-1:
            if subtitles[int(indexlist[i])].speaker is not None:
                subtitles.speakers[subtitles[int(indexlist[i])].speaker] -= 1
            subtitles[int(indexlist[i])].speaker=speaker
            if speaker is not None:
                subtitles.speakers[speaker] += 1
    subtitles.dump()
    return *checklist,*show_page(page,subtitles),subtitles


def del_spk(name):
    try:
        assert name not in ["", "None", [],None],"不得为空"
        os.remove(os.path.join(current_path, "SAVAdata", "speakers",name))
        gr.Info(f"删除：{name}")
    except Exception as e:
        gr.Warning(f"错误：{str(e)}")
    return getspklist()

def switch_spk_proj(name):
    if name=="bv2":
        return [gr.update(visible=True),gr.update(visible=False),gr.update(visible=False),gr.update(visible=False)]
    elif name=="gsv":
        return [gr.update(visible=False),gr.update(visible=True),gr.update(visible=False),gr.update(visible=False)]
    elif name=="mstts":  
        return [gr.update(visible=False),gr.update(visible=False),gr.update(visible=True),gr.update(visible=False)]
    elif name=="custom":
        return [gr.update(visible=False),gr.update(visible=False),gr.update(visible=False),gr.update(visible=True)]
    else:
        raise ""
