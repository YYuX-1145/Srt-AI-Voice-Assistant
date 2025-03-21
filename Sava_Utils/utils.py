import os
import time
import subprocess
from . import logger
import gradio as gr
import csv
import re
import shutil
import platform
import Sava_Utils
from .subtitle import Base_subtitle, Subtitle, Subtitles,to_time
from .edit_panel import *

current_path=os.environ.get("current_path")

def positive_int(*a):
    r = []
    for x in a:
        if x is None:
            r.append(None)
            continue
        if x < 0:
            x = 0
        r.append(int(x))
    return r

def cls_cache():
    dir = os.path.join(current_path, "SAVAdata", "temp")
    if os.path.exists(dir):
        shutil.rmtree(dir)
        logger.info("成功清除临时文件！")
        gr.Info("成功清除临时文件！")
    else:
        logger.info("目前没有临时文件！")
        gr.Info("目前没有临时文件！")

def rc_open_window(command, dir=current_path):
    command = f'start cmd /k "{command}"'
    subprocess.Popen(command, cwd=dir, shell=True)
    logger.info(f"执行命令:{command}")
    time.sleep(0.1)

def rc_bg(command, dir=current_path,get_id=True):
    process = subprocess.Popen(command, cwd=dir, shell=True)
    logger.info(f"执行命令:{command}")
    if get_id:
        yield process.pid
    yield process.wait()

system=platform.system()
def kill_process(pid):
    if pid<0:
        gr.Info("没有运行的进程")
        return None
    if(system=="Windows"):
        command = f"taskkill /t /f /pid {pid}"
    else:
        command= f"pkill --parent {pid} && kill {pid} " # not tested on real machine yet!!!
    subprocess.run(command,shell=True)
    logger.info(f"执行命令:{command}")
    gr.Info("已终止进程")

def file_show(files):
    if files in [None,[]]:
        return ""    
    if len(files)>1:
        return "<多个文件>"
    else:
        file=files[0]
    try:
        with open(file.name, "r", encoding="utf-8") as f:
            text = f.read()
        return text
    except Exception as error:
        return error

def read_srt(filename, offset):
    with open(filename, "r", encoding="utf-8") as f:
        file = f.readlines()
    subtitle_list = Subtitles()
    indexlist = []
    filelength = len(file)
    pattern=re.compile(r"\d+")
    for i in range(0, filelength):
        if " --> " in file[i]:
            if pattern.fullmatch(file[i - 1].strip().replace("\ufeff", "")):
                indexlist.append(i)  # get line id
    listlength = len(indexlist)
    id=1
    for i in range(0, listlength - 1):
        st, et = file[indexlist[i]].split(" --> ")
        # id = int(file[indexlist[i] - 1].strip().replace("\ufeff", ""))
        text = "".join(file[x] for x in range(indexlist[i] + 1, indexlist[i + 1] - 2))
        st = Subtitle(id, st, et, text, ntype="srt")
        st.add_offset(offset=offset)
        subtitle_list.append(st)
        id+=1
    st, et = file[indexlist[-1]].split(" --> ")
    # id = int(file[indexlist[-1] - 1].strip().replace("\ufeff", ""))
    text = "".join(file[x] for x in range(indexlist[-1] + 1, filelength))
    st = Subtitle(id, st, et, text, ntype="srt")
    st.add_offset(offset=offset)
    subtitle_list.append(st)
    return subtitle_list


def read_prcsv(filename, fps, offset):
    try:
        with open(filename, "r", encoding="utf-8", newline="") as csvfile:
            reader = list(csv.reader(csvfile))
            lenth = len(reader)
            subtitle_list = Subtitles()
            stid = 1
            for index in range(1, lenth):
                if reader[index] == []:
                    continue
                st = Subtitle(
                    stid,
                    reader[index][0],
                    reader[index][1],
                    reader[index][2],
                    ntype="prcsv",
                    fps=fps,
                )
                st.add_offset(offset=offset)
                subtitle_list.append(st)
                stid += 1
            return subtitle_list
        #
    except Exception as e:
        err = f"读取字幕文件出错：{str(e)}"
        logger.error(err)
        gr.Warning(err)


def read_txt(filename):
    REF_DUR=2
    with open(filename, "r", encoding="utf-8") as f:
        text=f.read()
    sentences = re.split(r"(?<=[!?。！？])|\n|(?<=[.])(?=\s|$)", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    subtitle_list = Subtitles()
    idx=1
    for s in sentences:
        subtitle_list.append(Subtitle(idx,to_time(REF_DUR * idx - REF_DUR), to_time(REF_DUR * idx), s, ntype="srt"))
        idx+=1
    return subtitle_list

def read_file(file_name, fps, offset):
    if Sava_Utils.config.server_mode:
        assert os.stat(file_name).st_size < 65536,"错误：文件过大"    #64KB
    if file_name[-4:].lower() == ".csv":
        subtitle_list = read_prcsv(file_name, fps, offset)
    elif file_name[-4:].lower() == ".srt":
        subtitle_list = read_srt(file_name, offset)
    elif file_name[-4:].lower() == ".txt":
        subtitle_list = read_txt(file_name)
    else:
        raise ValueError("未知的格式，请确保扩展名正确！")
    assert len(subtitle_list) != 0, "文件为空？？？"
    return subtitle_list

def create_multi_speaker(in_files, fps, offset):
    if in_files in [[],None] or len(in_files)>1:
        gr.Info("创建多角色配音工程只能上传有且只有一个文件！")
        return getworklist(), *load_page(Subtitles()), Subtitles()
    in_file=in_files[0]
    try:
        subtitle_list = read_file(in_file.name, fps, offset)
    except Exception as e:
        what=str(e)
        gr.Warning(what)
        return getworklist(),*load_page(Subtitles()),Subtitles()    
    subtitle_list.set_dir_name(os.path.basename(in_file.name).replace(".", "-"))
    return getworklist(),*load_page(subtitle_list), subtitle_list
