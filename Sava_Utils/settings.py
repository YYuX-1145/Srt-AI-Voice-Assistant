import os
import gradio as gr
import json
from .logger import logger

current_path = os.environ.get("current_path")

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