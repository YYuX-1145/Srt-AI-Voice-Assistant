import numpy as np
import os
import gradio as gr
import soundfile as sf
import json
import time
import subprocess
from .logger import logger

current_path=os.environ.get("current_path")

class Base_subtitle:
    def __init__(self, index: int, start_time, end_time, text: str, ntype: str, fps=30):
        self.index = int(index)
        self.start_time_raw = start_time
        self.end_time_raw = end_time
        self.text = text.strip()
        # def normalize(self,ntype:str,fps=30):
        if ntype == "prcsv":
            h, m, s, fs = (start_time.replace(";", ":")).split(":")  # seconds
            self.start_time = (
                int(h) * 3600 + int(m) * 60 + int(s) + round(int(fs) / fps, 2)
            )
            h, m, s, fs = (end_time.replace(";", ":")).split(":")
            self.end_time = (
                int(h) * 3600 + int(m) * 60 + int(s) + round(int(fs) / fps, 2)
            )
        elif ntype == "srt":
            h, m, s = start_time.split(":")
            s = s.replace(",", ".")
            self.start_time = int(h) * 3600 + int(m) * 60 + round(float(s), 2)
            h, m, s = end_time.split(":")
            s = s.replace(",", ".")
            self.end_time = int(h) * 3600 + int(m) * 60 + round(float(s), 2)
        else:
            raise ValueError

    def __str__(self) -> str:
        return f"id:{self.index},start:{self.start_time_raw}({self.start_time}),end:{self.end_time_raw}({self.end_time}),text:{self.text}"


class Subtitle(Base_subtitle):
    def __init__(self, index: int, start_time, end_time, text: str, ntype: str, fps=30):
        super().__init__(index, start_time, end_time, text, ntype, fps)
        self.is_success = False
        self.is_delayed = False

    def add_offset(self, offset=0):
        self.start_time += offset
        if self.start_time < 0:
            self.start_time = 0
        self.end_time += offset
        if self.end_time < 0:
            self.end_time = 0

    def __str__(self) -> str:
        return f"id:{self.index},start:{self.start_time_raw}({self.start_time}),end:{self.end_time_raw}({self.end_time}),text:{self.text}.State: is_success:{self.is_success},is_delayed:{self.is_delayed}"


class Subtitles:
    def __init__(self, proj: str = None, dir: str = None) -> None:
        self.subtitles = []
        self.proj = proj
        self.dir = dir

    def set_proj(self, proj: str):
        self.proj = proj

    def set_dir(self, dir: str):
        self.dir = dir
        os.makedirs(dir, exist_ok=True)

    def audio_join(self, sr):  # -> tuple[int,np.array]
        assert self.dir is not None
        audiolist = []
        delayed_list = []
        failed_list = []
        ptr = 0
        fl = [i for i in os.listdir(self.dir) if i.endswith(".wav")]
        if fl == []:
            raise gr.Error("所有的字幕合成都出错了，请检查API服务！")
        if sr is None:
            wav, sr = sf.read(os.path.join(self.dir, fl[0]))
        del fl
        for id, i in enumerate(self.subtitles):
            start_frame = int(i.start_time * sr)
            if ptr < start_frame:
                silence_len = start_frame - ptr
                audiolist.append(np.zeros(silence_len))
                ptr += silence_len
                self.subtitles[id].is_delayed = False
            elif ptr > start_frame:
                self.subtitles[id].is_delayed = True
                delayed_list.append(self.subtitles[id].index)
            f_path = os.path.join(self.dir, f"{i.index}.wav")
            if os.path.exists(f_path):
                wav, sr = sf.read(f_path)
                dur = wav.shape[-1]  # frames
                ptr += dur
                audiolist.append(wav)
                self.subtitles[id].is_success = True
            else:
                failed_list.append(self.subtitles[id].index)
        if delayed_list != []:
            logger.warning(
                f"序号合集为 {delayed_list} 的字幕由于之前的音频过长而被延迟"
            )
            gr.Warning(f"序号合集为 {delayed_list} 的字幕由于之前的音频过长而被延迟")
        if failed_list != []:
            logger.warning(f"序号合集为 {delayed_list} 的字幕合成失败！")
            gr.Warning(f"序号合集为 {delayed_list} 的字幕合成失败！")
        audio_content = np.concatenate(audiolist)
        return sr, audio_content

    def get_state(self, idx):
        if self.subtitles[idx].is_delayed:
            return "delayed"
        if self.subtitles[idx].is_success:
            return "ok"
        return "failed"

    def append(self, subtitle: Subtitle):
        self.subtitles.append(subtitle)

    def sort(self):
        self.subtitles.sort(key=lambda x: x.index)

    def __iter__(self):
        return iter(self.subtitles)

    def __getitem__(self, index):
        return self.subtitles[index]

    def __len__(self):
        return len(self.subtitles)

class Settings:
    def __init__(
        self,
        server_port: int = 5001,
        theme: str = "default",
        clear_tmp: bool = False,
        num_edit_rows: int = 7,
        bv2_pydir: str = "",
        gsv_pydir: str = "",
        bv2_dir: str = "",
        gsv_dir: str = "",
        bv2_args: str = "",
        gsv_args: str = "",
        ms_region: str = "eastasia",
        ms_key: str = "",
    ):
        self.server_port = int(server_port)
        self.theme = theme
        self.clear_tmp = clear_tmp
        self.num_edit_rows = int(num_edit_rows)
        self.ms_region = ms_region
        self.ms_key = ms_key
        # detect python envs####
        if bv2_pydir != "":
            if os.path.exists(bv2_pydir):
                self.bv2_pydir = os.path.abspath(bv2_pydir)
            else:
                self.bv2_pydir = ""
                gr.Warning("错误：填写的路径不存在！")
        else:
            if (
                os.path.exists(os.path.join(current_path, "venv\\python.exe"))
                and "VITS2" in current_path.upper()
            ):
                self.bv2_pydir = os.path.join(current_path, "venv\\python.exe")
                logger.info("已检测到Bert-VITS2环境")
            else:
                self.bv2_pydir = ""

        if gsv_pydir != "":
            if os.path.exists(gsv_pydir):
                self.gsv_pydir = os.path.abspath(gsv_pydir)
            else:
                self.gsv_pydir = ""
                gr.Warning("错误：填写的路径不存在！")
        else:
            if (
                os.path.exists(os.path.join(current_path, "runtime\\python.exe"))
                and "GPT" in current_path.upper()
            ):
                self.gsv_pydir = os.path.join(current_path, "runtime\\python.exe")
                logger.info("已检测到GPT-SoVITS环境")
            else:
                self.gsv_pydir = ""
        ###################
        self.bv2_dir = bv2_dir
        self.gsv_dir = gsv_dir
        self.bv2_args = bv2_args
        self.gsv_args = gsv_args
        if self.bv2_pydir != "":
            if bv2_dir == "":
                self.bv2_dir = os.path.dirname(os.path.dirname(self.bv2_pydir))
        if self.gsv_pydir != "":
            if gsv_dir == "":
                self.gsv_dir = os.path.dirname(os.path.dirname(self.gsv_pydir))

    def to_dict(self):
        return self.__dict__

    def save(self):
        dict = self.to_dict()
        os.makedirs(os.path.join(current_path, "SAVAdata"), exist_ok=True)
        with open(
            os.path.join(current_path, "SAVAdata", "config.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(dict, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, dict):
        return cls(**dict)


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
