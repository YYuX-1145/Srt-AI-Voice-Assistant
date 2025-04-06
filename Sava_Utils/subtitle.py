import os
import re
import gradio as gr
import numpy as np
import datetime
import pickle
import shutil
import Sava_Utils
import copy
from . import logger, i18n
from .librosa_load import load_audio

current_path = os.environ.get("current_path")
MAX_TIMESTAMP = 18000
SRT_TIME_Pattern = re.compile(r"\d+:\d+:\d+,\d+")


def compare_index_lt(i1, i2):
    l1 = list(map(int, i1.split("-")))
    l2 = list(map(int, i2.split("-")))
    while len(l1) < len(l2):
        l1.append(0)
    while len(l2) < len(l1):
        l2.append(0)
    return l1 < l2


def to_time(time_raw: float):
    hours, r = divmod(time_raw, 3600)
    minutes, r = divmod(r, 60)
    seconds, milliseconds = divmod(r, 1)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(milliseconds*1000):03d}"


class Base_subtitle:
    def __init__(self, index: int, start_time, end_time, text: str, ntype: str, fps=30):
        self.index: str = str(index)
        self.start_time_raw: str = start_time
        self.end_time_raw: str = end_time
        self.start_time = 0.0
        self.end_time = 0.0
        self.text: str = text.strip()
        # def normalize(self,ntype:str,fps=30):
        if ntype == "prcsv":
            self.start_time = self.to_float_prcsv_time(self.start_time_raw, fps)
            self.end_time = self.to_float_prcsv_time(self.end_time_raw, fps)
        elif ntype == "srt":
            self.start_time = self.to_float_srt_time(self.start_time_raw)
            self.end_time = self.to_float_srt_time(self.end_time_raw)
        else:
            raise ValueError
        # 5h=5*60*60s=18000s
        assert self.start_time < MAX_TIMESTAMP, 'too long'
        assert self.end_time < MAX_TIMESTAMP, 'too long'

    def to_float_prcsv_time(self, time: str, fps: int):
        h, m, s, fs = (time.replace(";", ":")).split(":")  # seconds
        result = int(h) * 3600 + int(m) * 60 + int(s) + round(int(fs) / fps, 2)
        return result

    def to_float_srt_time(self, time: str):
        h, m, s = time.split(":")
        s = s.replace(",", ".")
        result = int(h) * 3600 + int(m) * 60 + round(float(s), 2)
        return result

    def reset_srt_time(self, st, et):
        if SRT_TIME_Pattern.fullmatch(st) and SRT_TIME_Pattern.fullmatch(et):
            start_time_new = self.to_float_srt_time(st)
            end_time_new = self.to_float_srt_time(et)
            if start_time_new < MAX_TIMESTAMP and end_time_new < MAX_TIMESTAMP:
                self.start_time_raw = st
                self.start_time = start_time_new
                self.end_time_raw = et
                self.end_time = end_time_new
            else:
                raise ValueError(f"too long: {st} --> {et}")
        else:
            raise ValueError(f"{i18n('Input format mismatch')}: {st} --> {et}")

    def __str__(self) -> str:
        return f"id:{self.index},start:{self.start_time_raw}({self.start_time}),end:{self.end_time_raw}({self.end_time}),text:{self.text}"

    def __lt__(self, other) -> bool:
        return compare_index_lt(self.index, other.index)


class Subtitle(Base_subtitle):
    def __init__(self, index: int, start_time, end_time, text: str, ntype: str, fps=30, speaker=None):
        super().__init__(index, start_time, end_time, text, ntype, fps)
        self.is_success = None
        self.is_delayed = False
        self.real_st = 0
        self.real_et = 0  # frames
        self.speaker = speaker
        self.copy_count = 0

    def add_offset(self, offset=0):
        self.start_time += offset
        if self.start_time < 0:
            self.start_time = 0.0
        self.end_time += offset
        if self.end_time < 0:
            self.end_time = 0.0

    def get_srt_time(self):
        return f"{to_time(self.start_time)} --> {to_time(self.end_time)}"

    def copy(self):
        x = copy.deepcopy(self)
        self.copy_count += 1
        x.copy_count = 0
        x.index = f"{self.index}-{self.copy_count}"
        x.is_success = None
        return x

    def __str__(self) -> str:
        return f"id:{self.index},start:{self.start_time_raw}({self.start_time}),end:{self.end_time_raw}({self.end_time}),text:{self.text}.State: is_success:{self.is_success},is_delayed:{self.is_delayed}"


class Subtitles:
    def __init__(self, proj: str = None, dir: str = None) -> None:
        self.subtitles: list[Subtitle] = []
        self.proj = proj
        self.dir = dir
        self.sr = 32000
        self.default_speaker = None
        self.speakers = dict()

    def dump(self):
        assert self.dir is not None
        with open(os.path.join(self.get_abs_dir(), "st.pkl"), 'wb') as f:
            pickle.dump(self, f)

    def set_proj(self, proj: str):
        self.proj = proj

    def set_dir_name(self, dir_name: str):
        abspath = os.path.join(current_path, "SAVAdata", "temp", "workspaces", dir_name)
        while os.path.exists(abspath):
            if Sava_Utils.config.overwrite_workspace:
                shutil.rmtree(abspath)
                break
            abspath += "(new)"
        self.dir = os.path.join("SAVAdata", "temp", "workspaces", dir_name)  # relative path
        os.makedirs(abspath, exist_ok=True)
        self.dump()

    def get_abs_dir(self):
        return os.path.join(current_path, self.dir)

    def audio_join(self, sr=None):  # -> tuple[int,np.array]
        assert self.dir is not None
        abs_path = os.path.join(current_path, self.dir)
        # print(self.speakers)
        audiolist = []
        delayed_list = []
        failed_list = []
        fl = [i for i in os.listdir(abs_path) if i.endswith(".wav")]
        if len(fl) == 0:
            gr.Warning(i18n('Subtitles have not been synthesized yet!'))
            return None
        if sr in [None, 0]:
            wav, sr = load_audio(os.path.join(abs_path, fl[0]), sr=sr)
        self.sr = sr
        interval = int(Sava_Utils.config.min_interval * sr)
        del fl
        ptr = 0
        for id, i in enumerate(self.subtitles):
            start_frame = int(i.start_time * sr)
            if ptr <= start_frame:
                silence_len = start_frame - ptr
                audiolist.append(np.zeros(silence_len))
                ptr += silence_len
                self.subtitles[id].is_delayed = False
            elif ptr > start_frame:
                self.subtitles[id].is_delayed = True
                delayed_list.append(self.subtitles[id].index)
            f_path = os.path.join(abs_path, f"{i.index}.wav")
            if os.path.exists(f_path):
                wav, sr = load_audio(f_path, sr=sr)
                dur = wav.shape[-1]  # frames
                self.subtitles[id].real_st = ptr
                ptr += dur
                audiolist.append(wav)
                self.subtitles[id].real_et = ptr
                ptr += interval
                audiolist.append(np.zeros(interval))
                # self.subtitles[id].is_success = True
            else:
                failed_list.append(self.subtitles[id].index)
        if delayed_list != []:
            # logger.warning(f"{i18n('The following subtitles are delayed due to the previous audio being too long.')}:{delayed_list}")
            gr.Warning(f"{i18n('The following subtitles are delayed due to the previous audio being too long.')}:{delayed_list}")
        if failed_list != []:
            logger.warning(f"{i18n('Failed to synthesize the following subtitles or they were not synthesized')}:{failed_list}")
            gr.Warning(f"{i18n('Failed to synthesize the following subtitles or they were not synthesized')}:{failed_list}")
        audio_content = np.concatenate(audiolist)
        self.dump()
        return sr, audio_content

    def get_state(self, idx):
        if self.subtitles[idx].is_success:
            if self.subtitles[idx].is_delayed:
                return "delayed"
            return "ok"
        elif self.subtitles[idx].is_success is None:
            return "None"
        return "failed"

    def append(self, subtitle: Subtitle):
        self.subtitles.append(subtitle)

    def sort(self, begin=0, end=0, partial=False):
        if not partial:
            self.subtitles.sort()
        else:
            if end > len(self.subtitles):
                end = len(self.subtitles)
            self.subtitles[begin:end] = sorted(self.subtitles[begin:end])

    def __iter__(self):
        return iter(self.subtitles)

    def __getitem__(self, index):
        return self.subtitles[index]

    def pop(self, index):
        self.subtitles.pop(index)

    def insert(self, index, item):
        self.subtitles.insert(index, item)

    def __len__(self):
        return len(self.subtitles)

    def export(self, fp=None, open_explorer=True, raw=False):
        if len(self.subtitles) == 0:
            gr.Info(i18n('There is no subtitle in the current workspace'))
            return None
        idx = 0
        srt_content = []
        for i in self.subtitles:
            idx += 1
            if raw or (i.real_st == 0 and i.real_et == 0):
                if SRT_TIME_Pattern.fullmatch(i.start_time_raw) and SRT_TIME_Pattern.fullmatch(i.end_time_raw):
                    start = i.start_time_raw
                    end = i.end_time_raw
                else:
                    start = to_time(i.start_time)
                    end = to_time(i.end_time)
            else:
                start = to_time(i.real_st / self.sr)
                end = to_time(i.real_et / self.sr)
            srt_content.append(str(idx) + "\n")
            srt_content.append(f"{start} --> {end}" + "\n")
            srt_content.append(i.text + "\n")
            srt_content.append("\n")
        if fp is None:
            t = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            file_path = os.path.join(current_path, "SAVAdata", "output", f"{t}.srt")
        else:
            file_path = fp
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(srt_content)
        if open_explorer and not Sava_Utils.config.server_mode:
            os.system(f'explorer /select, {file_path}')
        return [file_path]
