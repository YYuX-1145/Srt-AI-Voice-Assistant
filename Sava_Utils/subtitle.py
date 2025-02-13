import os
import gradio as gr
import numpy as np
import datetime
import pickle
import shutil
import Sava_Utils
from . import logger
from .librosa_load import load_audio
current_path = os.environ.get("current_path")


def to_time(time_raw: float):
    hours, r = divmod(time_raw, 3600)
    minutes, r = divmod(r, 60)
    seconds, milliseconds = divmod(r, 1)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(milliseconds*1000):03d}"

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
    def __init__(self, index: int, start_time, end_time, text: str, ntype: str, fps=30,speaker=None):
        super().__init__(index, start_time, end_time, text, ntype, fps)
        self.is_success = None
        self.is_delayed = False
        self.real_st=0
        self.real_et=0 #frames
        self.speaker=speaker

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
        self.sr=0
        self.speakers=dict()

    def dump(self):
        assert self.dir is not None
        with open(os.path.join(self.dir,"st.pkl"), 'wb') as f:
            pickle.dump(self, f)

    def set_proj(self, proj: str):
        self.proj = proj

    def set_dir(self, dir: str):
        self.dir = dir
        os.makedirs(dir, exist_ok=True)
        self.dump()

    def audio_join(self, sr=None):  # -> tuple[int,np.array]
        assert self.dir is not None
        # print(self.speakers)
        audiolist = []
        delayed_list = []
        failed_list = []
        fl = [i for i in os.listdir(self.dir) if i.endswith(".wav")]
        if fl == []:
            gr.Warning("还未合成任何字幕！")
            return None
        if sr is None:
            wav, sr = load_audio(os.path.join(self.dir, fl[0]),sr=sr) 
        self.sr=sr
        interval = int(Sava_Utils.config.min_interval*sr)
        del fl        
        ptr = 0
        for id, i in enumerate(self.subtitles):
            start_frame = int(i.start_time * sr)
            if ptr  <= start_frame:
                silence_len = start_frame - ptr
                audiolist.append(np.zeros(silence_len))
                ptr += silence_len
                self.subtitles[id].is_delayed = False
            elif ptr > start_frame:
                self.subtitles[id].is_delayed = True
                delayed_list.append(self.subtitles[id].index)
            f_path = os.path.join(self.dir, f"{i.index}.wav")
            if os.path.exists(f_path):
                wav, sr = load_audio(f_path,sr=sr)
                dur = wav.shape[-1]  # frames
                self.subtitles[id].real_st=ptr
                ptr += dur
                audiolist.append(wav)
                self.subtitles[id].real_et = ptr
                ptr+=interval
                audiolist.append(np.zeros(interval))
                self.subtitles[id].is_success = True
            else:
                failed_list.append(self.subtitles[id].index)
        if delayed_list != []:
            logger.warning(
                f"序号合集为 {delayed_list} 的字幕由于之前的音频过长而被延迟"
            )
            gr.Warning(f"序号合集为 {delayed_list} 的字幕由于之前的音频过长而被延迟")
        if failed_list != []:
            logger.warning(f"序号合集为 {delayed_list} 的字幕合成失败或未合成！")
            gr.Warning(f"序号合集为 {failed_list} 的字幕合成失败或未合成！")
        audio_content = np.concatenate(audiolist)
        self.dump()
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

    def export(self):
        if len(self.subtitles)==0:
            gr.Info("当前没有字幕")
            return None
        idx=0
        srt_content = []
        for i in self.subtitles:
            idx+=1
            start=i.real_st/self.sr
            end=i.real_et/self.sr
            srt_content.append(str(idx)+"\n")
            srt_content.append(f"{to_time(start)} --> {to_time(end)}"+"\n")
            srt_content.append(i.text + "\n")
            srt_content.append("\n")
        t=datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_path=os.path.join(current_path,"SAVAdata","output",f"{t}.srt")
        with open(file_path,"w",encoding="utf-8") as f:
            f.writelines(srt_content)
        os.system(f'explorer /select, {file_path}')
