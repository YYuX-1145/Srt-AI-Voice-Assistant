from .base import Projet
import requests
import gradio as gr
from ..utils import positive_int
from .. import logger

class GSV(Projet):
    def __init__(self):
        self.gsv_fallback=False
        super().__init__("gsv")

    def api(self,port,**kwargs):
        try:
            data_json = kwargs
            API_URL = f"http://127.0.0.1:{port}/tts"
            if self.gsv_fallback:
                data_json = {
                "refer_wav_path": kwargs["ref_audio_path"],
                "prompt_text": kwargs["prompt_text"],
                "prompt_language": kwargs["prompt_lang"],
                "text": kwargs["text"],
                "text_language": kwargs["text_lang"],
                "top_k": kwargs["top_k"],
                "top_p": kwargs["top_p"],
                "temperature": kwargs["temperature"],
                "speed": kwargs["speed_factor"],
                }
                API_URL = f"http://127.0.0.1:{port}/"
            #print(data_json)
            response = requests.post(url=API_URL, json=data_json)
            response.raise_for_status()  # 检查响应的状态码
            return response.content
        except Exception as e:
            err = f"GPT-SoVITS推理发生错误，请检查API服务是否正确运行。报错内容: {e}"
            logger.error(err)
            return None
   
    def save_action(self, *args, text: str = None):
        text_language,port,refer_wav_path,aux_refer_wav_path,prompt_text,prompt_language,batch_size,batch_threshold,fragment_interval,speed_factor,top_k,top_p,temperature,repetition_penalty,split_bucket,text_split_method=args
        port = positive_int(port)[0]
        audio = self.api(
            port,
            text=text,
            text_lang=text_language,  ###language->lang
            ref_audio_path=refer_wav_path,  # ref
            aux_ref_audio_paths=aux_refer_wav_path,
            prompt_text=prompt_text,
            prompt_lang=prompt_language,  #
            batch_size=batch_size,
            batch_threshold=batch_threshold,
            fragment_interval=fragment_interval,
            speed_factor=speed_factor,
            top_k=top_k,
            top_p=top_p,
            seed=-1,
            parallel_infer=True,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
            split_bucket=split_bucket,
            text_split_method=text_split_method,
            media_type="wav",
            streaming_mode=False,
        )
        return audio
