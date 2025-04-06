import os
import time
import subprocess
from . import logger, i18n
from .librosa_load import get_rms
import gradio as gr
import numpy as np
import csv
import re
import shutil
import platform
import Sava_Utils

current_path = os.environ.get("current_path")
LABELED_TXT_PATTERN = re.compile(r'^([^:：]{1,20})[:：](.+)')


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


def clear_cache():
    dir = os.path.join(current_path, "SAVAdata", "temp")
    if os.path.exists(dir):
        shutil.rmtree(dir)
        logger.info(i18n('Temporary files cleared successfully!'))
        gr.Info(i18n('Temporary files cleared successfully!'))
    else:
        logger.info(i18n('There are no temporary files.'))
        gr.Info(i18n('There are no temporary files.'))


def rc_open_window(command, dir=current_path):
    command = f'start cmd /k "{command}"'
    subprocess.Popen(command, cwd=dir, shell=True)
    logger.info(f"{i18n('Execute command')}:{command}")
    time.sleep(0.1)


def rc_bg(command, dir=current_path, get_id=True):
    process = subprocess.Popen(command, cwd=dir, shell=True)
    logger.info(f"{i18n('Execute command')}:{command}")
    if get_id:
        yield process.pid
    yield process.wait()


system = platform.system()


def kill_process(pid):
    if pid < 0:
        gr.Info(i18n('No running processes'))
        return None
    if system == "Windows":
        command = f"taskkill /t /f /pid {pid}"
    else:
        command = f"pkill --parent {pid} && kill {pid} "  # not tested on real machine yet!!!
    subprocess.run(command, shell=True)
    logger.info(f"{i18n('Execute command')}:{command}")
    gr.Info(i18n('Process terminated.'))


def file_show(files):
    if files in [None, []]:
        return ""
    if len(files) > 1:
        return i18n('<Multiple Files>')
    else:
        file = files[0]
    try:
        with open(file.name, "r", encoding="utf-8") as f:
            text = f.read()
        return text
    except Exception as error:
        return error


from .subtitle import Base_subtitle, Subtitle, Subtitles
from .edit_panel import *


def read_srt(filename, offset):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            file = f.readlines()
        subtitle_list = Subtitles()
        indexlist = []
        filelength = len(file)
        pattern = re.compile(r"\d+")
        for i in range(0, filelength):
            if " --> " in file[i]:
                if pattern.fullmatch(file[i - 1].strip().replace("\ufeff", "")):
                    indexlist.append(i)  # get line id
        listlength = len(indexlist)
        id = 1
        for i in range(0, listlength - 1):
            st, et = file[indexlist[i]].split(" --> ")
            # id = int(file[indexlist[i] - 1].strip().replace("\ufeff", ""))
            text = "".join(file[x] for x in range(indexlist[i] + 1, indexlist[i + 1] - 2))
            st = Subtitle(id, st, et, text, ntype="srt")
            st.add_offset(offset=offset)
            subtitle_list.append(st)
            id += 1
        st, et = file[indexlist[-1]].split(" --> ")
        # id = int(file[indexlist[-1] - 1].strip().replace("\ufeff", ""))
        text = "".join(file[x] for x in range(indexlist[-1] + 1, filelength))
        st = Subtitle(id, st, et, text, ntype="srt")
        st.add_offset(offset=offset)
        subtitle_list.append(st)
    except Exception as e:
        err = f"{i18n('Failed to read file')}: {str(e)}"
        logger.error(err)
        gr.Warning(err)
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
    except Exception as e:
        err = f"{i18n('Failed to read file')}: {str(e)}"
        logger.error(err)
        gr.Warning(err)
    return subtitle_list


def read_txt(filename):
    # REF_DUR = 2
    try:
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
        sentences = re.split(r"(?<=[!?。！？])|\n|(?<=[.])(?=\s|$)", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        subtitle_list = Subtitles()
        idx = 1
        for s in sentences:
            subtitle_list.append(Subtitle(idx, "00:00:00,000", "00:00:00,000", s, ntype="srt"))
            idx += 1
    except Exception as e:
        err = f"{i18n('Failed to read file')}: {str(e)}"
        logger.error(err)
        gr.Warning(err)
    return subtitle_list


def read_labeled_txt(filename: str, spk_dict: dict):
    try:
        idx = 1
        subtitle_list = Subtitles()
        subtitle_list.append(Subtitle(idx, "00:00:00,000", "00:00:00,000", "", ntype="srt"))
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("#") or line.strip() == "":
                    continue
                match = LABELED_TXT_PATTERN.match(line.strip())
                if match:
                    speaker = match.group(1).strip()
                    speaker = spk_dict.get(speaker, speaker)
                    if speaker in ['', 'None']:
                        speaker = None
                    subtitle_list.append(Subtitle(idx, "00:00:00,000", "00:00:00,000", match.group(2).strip(), ntype="srt", speaker=speaker))
                    idx += 1
                    if speaker is not None:
                        if speaker not in list(subtitle_list.speakers.keys()):
                            subtitle_list.speakers[speaker] = 1
                        else:
                            subtitle_list.speakers[speaker] += 1
                else:
                    subtitle_list[-1].text += ',' + line
            if not subtitle_list[0].text:
                subtitle_list.pop(0)
        return subtitle_list
    except Exception as e:
        err = f"{i18n('Failed to read file')}: {str(e)}"
        logger.error(err)
        gr.Warning(err)
    return subtitle_list


def get_speaker_map(in_files):
    if in_files in [[], None] or len(in_files) > 1:
        gr.Info(i18n('Creating a multi-speaker project can only upload one file at a time!'))
        return None, gr.update(choices=None,value=None)
    filename = in_files[0].name
    if filename[-4:].lower() != ".txt":
        gr.Info("labeled texts mode only supports .txt")
        return None, gr.update(choices=None, value=None)
    speakers = set()
    rows = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            match = LABELED_TXT_PATTERN.match(line.strip())
            if match:
                speaker = match.group(1).strip()
                speakers.add(speaker)
        for speaker in speakers:
            rows.append([speaker, 'None'])
    if len(rows)==0:
        rows.append(['',''])
    return np.array(rows, dtype=str), gr.update(choices=list(speakers), value=None)


def modify_spkmap(ori, tar, tab):
    if ori not in [None, "", []]:
        if tar in [None, ""]:
            tar = "None"
        for i in tab:
            if i[0] == ori:
                i[-1] = tar
                break
    return tab


def read_file(file_name, fps, offset):
    if Sava_Utils.config.server_mode:
        assert os.stat(file_name).st_size < 65536, i18n('Error: File too large')  # 64KB
    if file_name[-4:].lower() == ".csv":
        subtitle_list = read_prcsv(file_name, fps, offset)
    elif file_name[-4:].lower() == ".srt":
        subtitle_list = read_srt(file_name, offset)
    elif file_name[-4:].lower() == ".txt":
        subtitle_list = read_txt(file_name)
    else:
        raise ValueError(i18n('Unknown format. Please ensure the extension name is correct!'))
    assert len(subtitle_list) != 0, "Empty file???"
    return subtitle_list


def create_multi_speaker(in_files, speaker_map, fps, offset):
    if in_files in [[], None] or len(in_files) > 1:
        gr.Info(i18n('Creating a multi-speaker project can only upload one file at a time!'))
        return getworklist(), *load_page(Subtitles()), Subtitles()
    in_file = in_files[0]
    try:
        if speaker_map[0][0] == "":
            subtitle_list = read_file(in_file.name, fps, offset)
        else:
            spk_dict = {i[0]: i[-1] for i in speaker_map}
            assert in_file.name[-4:].lower() == ".txt", "labeled texts mode only supports .txt"
            subtitle_list = read_labeled_txt(in_file.name, spk_dict)
            assert len(subtitle_list) != 0, "Empty???"
    except Exception as e:
        what = str(e)
        gr.Warning(what)
        return getworklist(), *load_page(Subtitles()), Subtitles()
    subtitle_list.set_dir_name(os.path.basename(in_file.name).replace(".", "-"))
    return getworklist(), *load_page(subtitle_list), subtitle_list


def remove_silence(audio, sr, padding_begin=0.1, padding_fin=0.2, threshold_db=-27):
    # Padding(sec) is actually margin of safety
    hop_length = 512
    rms_list = get_rms(audio, hop_length=hop_length).squeeze(0)
    threshold = 10 ** (threshold_db / 20.0)
    for i, rms in enumerate(rms_list):
        if rms >= threshold:
            break
    if i == rms_list.shape[-1]:
        print("[debug] remove_silence: failed to find the cutting point")
        return audio
    for j, rms in enumerate(reversed(rms_list)):
        if rms >= threshold:
            break
    cutting_point1 = max(i * hop_length - int(padding_begin * sr), 0)
    cutting_point2 = min((rms_list.shape[-1] - j) * hop_length + int(padding_fin * sr), audio.shape[-1])
    audio = audio[cutting_point1:cutting_point2]
    return audio
