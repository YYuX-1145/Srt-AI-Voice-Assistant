import gradio as gr
import os
import pickle
from .subtitle import Subtitles,Subtitle
import Sava_Utils

current_path = os.environ.get("current_path")

def load_page(subtitle_list,target_index=1):
    length=len(subtitle_list)
    if length==0:
        gr.Info("上次生成未成功，请先完成生成流程！")
    if target_index > 1:
        value=min(target_index,((length-1)//Sava_Utils.config.num_edit_rows)*Sava_Utils.config.num_edit_rows+1)
    else:
        value=target_index
    return gr.update(minimum=1,maximum=length if length>0 else 1,interactive=True,value=value),*show_page(value,subtitle_list)

def show_page(page_start,subtitle_list:Subtitles):
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
        ret.append(gr.update(value=subtitle_list[i].get_srt_time(),interactive=True,visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].text}",interactive=True,visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].speaker}",interactive=False,visible=True))
        ret.append(gr.update(value=subtitle_list.get_state(i),interactive=False,visible=True))
        ret+=btn
    for i in range(Sava_Utils.config.num_edit_rows - pageend + page_start):
        ret.append(gr.update(value=-1,visible=False))
        ret.append(gr.update(value=-1,interactive=False,visible=True))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=True))
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
        return  *checklist,*load_page(Subtitles())
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    targetlist = []
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and indexlist[i]!=-1:
            targetlist.append(int(indexlist[i]))
    if len(targetlist)==0:
        gr.Info("未选中任何字幕")
    targetlist.sort(reverse=True)
    for idx in targetlist:
        subtitles.pop(idx)
    return *[False for i in range(Sava_Utils.config.num_edit_rows)], *load_page(subtitles,target_index=page)


def merge_subtitle(page,subtitles:Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles) == 0:
        gr.Info("当前没有字幕")
        return *checklist, *load_page(Subtitles())
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    targetlist = []
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and indexlist[i] != -1:
            targetlist.append(int(indexlist[i]))
    if(len(targetlist))>1:
        max_i=max(targetlist)
        min_i=min(targetlist) 
        subtitles[min_i].end_time_raw = subtitles[max_i].end_time_raw
        subtitles[min_i].end_time = subtitles[max_i].end_time
        for i in range(min_i,max_i):
            if subtitles[min_i].text[-1] not in [" ", "\n", "!",".","?","。","！","？"]:
                subtitles[min_i].text+=','
            subtitles[min_i].text += subtitles[min_i+1].text
            subtitles.pop(min_i+1)
    else:
        gr.Info("请选择起点和终点！")
    return *[False for i in range(Sava_Utils.config.num_edit_rows)], *load_page(subtitles, target_index=page)

def copy_subtitle(page,subtitles:Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles) == 0:
        gr.Info("当前没有字幕")
        return *checklist, *load_page(Subtitles())
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    targetlist = []
    for i in range(Sava_Utils.config.num_edit_rows):
        if checklist[i] and indexlist[i] != -1:
            targetlist.append(int(indexlist[i]))
    if len(targetlist)==0:
        gr.Info("未选中任何字幕")
    targetlist.sort(reverse=True)
    for i in targetlist:
        subtitles.insert(i+1+subtitles[i].copy_count,subtitles[i].copy())
    return *[False for i in range(Sava_Utils.config.num_edit_rows)], *load_page(subtitles, target_index=page)


def apply_start_end_time(page,subtitles:Subtitles, *args):
    if subtitles is None or len(subtitles) == 0:
        gr.Info("当前没有字幕")
        return show_page(page,Subtitles())
    indexlist = [int(i) for i in args[ :Sava_Utils.config.num_edit_rows]]
    timelist = args[Sava_Utils.config.num_edit_rows :]
    # for i in range(page-1,min(page+Sava_Utils.config.num_edit_rows-1,len(subtitles)-1)):
    for i,title_index in enumerate(indexlist):
        try:
            if title_index!=-1 and timelist[i]!=subtitles[title_index].get_srt_time():
                st, et = timelist[i].split("-->")
                subtitles[title_index].reset_srt_time(st.strip(),et.strip())
        except ValueError:
            gr.Info(f"输入格式不匹配：{timelist[i]}")
    subtitles.dump()
    return show_page(page, subtitles)


def apply_spk(speaker, page, subtitles: Subtitles, *args):
    checklist = args[: Sava_Utils.config.num_edit_rows]
    if subtitles is None or len(subtitles)==0:
        gr.Info("当前没有字幕")
        return  *checklist,*show_page(page,Subtitles())
    if speaker in ["","None",[]]:
        speaker=None
    indexlist = args[Sava_Utils.config.num_edit_rows :]
    assert len(checklist)==len(indexlist)
    subtitles.default_speaker=speaker
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
    return *checklist,*show_page(page,subtitles)


# def set_default_speaker(speaker,subtitles:Subtitles):
#     if subtitles is None or len(subtitles) == 0:
#         return
#     if speaker in ["", "None", []]:
#         speaker = None
#     subtitles.default_speaker=speaker


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
