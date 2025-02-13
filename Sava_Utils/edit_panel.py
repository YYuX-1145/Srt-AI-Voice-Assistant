import gradio as gr
import os
import pickle
from .subtitle import Subtitles
from . import config

current_path = os.environ.get("current_path")

def load_page(subtitle_list):
    length=len(subtitle_list)
    if length==0:
        gr.Info("上次生成未成功，请先完成生成流程！")
    return gr.update(minimum=1,maximum=length if length>0 else 1,interactive=True,value=1),*show_page(1,subtitle_list)

def show_page(page_start,subtitle_list):
    ret=[]
    length=len(subtitle_list)
    pageend=page_start+config.num_edit_rows
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
    for i in range(config.num_edit_rows-pageend+page_start):
        ret.append(gr.update(value=-1,visible=False))
        ret.append(gr.update(value=-1,interactive=False,visible=True))
        ret.append(gr.update(value="NO INFO",visible=True))
        ret.append(gr.update(value="NO INFO",interactive=False,visible=True))
        ret.append(gr.update(value="None",interactive=False,visible=True))
        ret.append(gr.update(value="NO INFO", interactive=False, visible=True))
        ret+=btn        
    return ret

def getworklist():
    try:
        c=os.listdir(os.path.join(current_path,"SAVAdata","temp","work"))
        return gr.update(choices=c,value=c[0])
    except:
        return gr.update(choices=[""])


def getspklist():
    try:
        c = os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))
        return gr.update(choices=c, value=c[0])
    except:
        return gr.update(choices=[""])


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

def apply_spk(speaker,page,subtitles,*args):
    checklist=args[:config.num_edit_rows]
    if subtitles is None or len(subtitles)==0:
        gr.Info("当前没有字幕")
        return  *checklist,*show_page(page,Subtitles()),Subtitles()
    indexlist = args[config.num_edit_rows :]
    assert len(checklist)==len(indexlist)
    for i in range(config.num_edit_rows):
        if checklist[i] and int(indexlist[i])!=-1:
            subtitles[int(indexlist[i])].speaker=speaker
    return *[False for i in range(config.num_edit_rows)],*show_page(page,subtitles),subtitles

def del_spk(name):
    try:
        os.remove(os.path.join(current_path, "SAVAdata", "speakers",name))
    except Exception as e:
        gr.Warning(f"错误：str(e)")
    return getspklist
