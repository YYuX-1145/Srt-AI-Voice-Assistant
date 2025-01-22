import os
import gradio as gr
import numpy as np
import soundfile as sf
from .logger import logger

current_path = os.environ.get("current_path")


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