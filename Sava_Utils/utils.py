import os
import time
import subprocess
from . import logger
import gradio as gr
import csv
import re
from .subtitle import Base_subtitle, Subtitle, Subtitles,to_time

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

def run_command(command, dir):
    command = f'start cmd /k "{command}"'
    subprocess.Popen(command, cwd=dir, shell=True)
    logger.info(f"执行命令:" + command)
    time.sleep(0.1)

def file_show(file):
    if file is None:
        return ""
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
    sentences = re.split(r'(?<=[.!?。！？])|\n', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    subtitle_list = Subtitles()
    idx=1
    for s in sentences:
        subtitle_list.append(Subtitle(idx,to_time(REF_DUR * idx - REF_DUR), to_time(REF_DUR * idx), s, ntype="srt"))
        idx+=1
    return subtitle_list
