from .base import Projet
import requests
import gradio as gr
from ..utils import positive_int
from ..logger import logger

class BV2(Projet):
    def __init__(self):
        super().__init__("bv2")

    def api(
        self,
        text,
        mid,
        spk_name,
        sid,
        lang,
        length,
        noise,
        noisew,
        sdp,
        emotion,
        split,
        style_text,
        style_weight,
        port,
    ):
        try:
            API_URL = f'http://127.0.0.1:{port}/voice'
            data_json = {                    
                    "model_id": mid,
                    "speaker_name": spk_name,
                    "speaker_id": sid,
                    "language": lang,
                    "length": length,
                    "noise": noise,
                    "noisew": noisew,
                    "sdp_ratio": sdp,
                    "emotion":emotion,
                    "auto_translate": False,
                    "auto_split": split,
                    "style_text": style_text,
                    "style_weight": style_weight,                    
                    "text": text
                }
            # print(data_json)
            response = requests.get(url=API_URL,params=data_json)
            response.raise_for_status()  # 检查响应的状态码
            return response.content
        except Exception as e:
            err=f'bert-vits2推理发生错误，请检查HiyoriUI是否正确运行。报错内容: {e}'
            logger.error(err)
            return None
        
    def save_action(self,*args,text:str=None):
        language,port,mid,sid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale,emotion_text=args
        sid,port,mid=positive_int(sid,port,mid)
        if speaker_name is not None and speaker_name!="":
            audio = self.api(text=text,mid=mid,spk_name=speaker_name,sid=None,lang=language,length=length_scale,noise=noise_scale,noisew=noise_scale_w,sdp=sdp_ratio,split=False,style_text=None,style_weight=0,port=port,emotion=emotion_text)
        else:
            audio = self.api(text=text,mid=mid,spk_name=None,sid=sid,lang=language,length=length_scale,noise=noise_scale,noisew=noise_scale_w,sdp=sdp_ratio,split=False,style_text=None,style_weight=0,port=port,emotion=emotion_text)
        return audio
