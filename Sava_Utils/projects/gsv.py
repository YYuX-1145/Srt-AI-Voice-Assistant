from .base import Projet
import requests
import gradio as gr
from ..utils import positive_int
from .. import logger
import os
import hashlib
import soundfile as sf
import time
import json

current_path=os.environ.get("current_path")

dict_language = {
    "中文": "all_zh",
    "粤语": "all_yue",
    "英文": "en",
    "日文": "all_ja",
    "韩文": "all_ko",
    "中英混合": "zh",
    "粤英混合": "yue",
    "日英混合": "ja",
    "韩英混合": "ko",
    "多语种混合": "auto",  # 多语种启动切分识别语种
    "多语种混合(粤语)": "auto_yue",
}
cut_method = {
    "不切": "cut0",
    "凑四句一切": "cut1",
    "凑50字一切": "cut2",
    "按中文句号。切": "cut3",
    "按英文句号.切": "cut4",
    "按标点符号切": "cut5",
}

def temp_ra(a: tuple):
    sr, wav = a
    name = hashlib.md5(wav.tobytes()).hexdigest() + ".wav"
    os.makedirs(os.path.join(current_path, "SAVAdata", "temp"), exist_ok=True)
    dir = os.path.join(current_path, "SAVAdata", "temp", name)
    if not os.path.exists(dir):
        sf.write(dir, wav, sr)
    return dir

def temp_aux_ra(a:bytes):
    name = hashlib.md5(a).hexdigest() + ".wav"
    os.makedirs(os.path.join(current_path, "SAVAdata", "temp"), exist_ok=True)
    dir = os.path.join(current_path, "SAVAdata", "temp", name)
    if not os.path.exists(dir):
        with open(dir,'wb') as f:
            f.write(a)
    return dir

class GSV(Projet):
    def __init__(self):
        self.gsv_fallback=False
        self.presets_list=['None']
        self.current_sovits_model=""
        self.current_gpt_model=""
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
            # print(data_json)
            response = requests.post(url=API_URL, json=data_json)
            response.raise_for_status()
            return response.content
        except Exception as e:
            err = f"GPT-SoVITS推理发生错误，请检查API服务是否正确运行。报错内容: {e}  "
            try:
                err+=f"返回信息：{response.json()}"
            except:
                pass
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

    def _UI(self):
        self.language2 = gr.Dropdown(choices=dict_language.keys(), value="中英混合", label="Language",interactive=True,allow_custom_value=False)
        with gr.Row():
            self.refer_audio=gr.Audio(label="主参考音频")
            self.aux_ref_audio = gr.File(label="辅参考音频(可选多个，或不选)",file_count="multiple",type="binary")
        with gr.Row():
            self.refer_text=gr.Textbox(label="参考音频文本",value="",placeholder="不填视为开启无参考文本模式，建议搭配微调的模型")
            self.refer_lang = gr.Dropdown(choices=dict_language.keys(), value='中文', label="参考音频语言",interactive=True,allow_custom_value=False)
        with gr.Accordion("模型切换",open=False):
            self.sovits_path=gr.Textbox(value="",label="Sovits模型路径",interactive=True)
            self.gpt_path=gr.Textbox(value="",label="GPT模型路径",interactive=True)
            self.switch_gsvmodel_btn=gr.Button(value="切换模型",variant="primary")
        with gr.Row():
            self.sampling_rate2=gr.Number(label="采样率",value=32000,visible=True,interactive=True)
            self.api_port2=gr.Number(label="API Port",value=9880,visible=True,interactive=True)
        with gr.Accordion("高级合成参数",open=False):
            self.batch_size = gr.Slider(minimum=1,maximum=200,step=1,label="batch_size",value=20,interactive=True)
            self.batch_threshold = gr.Slider(minimum=0,maximum=1,step=0.01,label="batch_threshold",value=0.75,interactive=True)
            self.fragment_interval = gr.Slider(minimum=0.01,maximum=1,step=0.01,label="分段间隔(秒)",value=0.3,interactive=True)
            self.speed_factor = gr.Slider(minimum=0.25,maximum=4,step=0.05,label="speed_factor",value=1.0,interactive=True)
            self.top_k = gr.Slider(minimum=1,maximum=100,step=1,label="top_k",value=5,interactive=True)
            self.top_p = gr.Slider(minimum=0,maximum=1,step=0.05,label="top_p",value=1,interactive=True)
            self.temperature = gr.Slider(minimum=0,maximum=1,step=0.05,label="temperature",value=1,interactive=True)
            self.repetition_penalty = gr.Slider(minimum=0,maximum=2,step=0.05,label="repetition_penalty",value=1.35,interactive=True)
            self.split_bucket = gr.Checkbox(label="数据分桶", value=True, interactive=True, show_label=True)
            self.how_to_cut = gr.Radio(label="怎么切",choices=["不切","凑四句一切","凑50字一切","按中文句号。切","按英文句号.切","按标点符号切"],value="凑四句一切",interactive=True)
        with gr.Accordion("预设", open=False):
            self.choose_presets = gr.Dropdown(label="",value="None",choices=self.presets_list,interactive=True,allow_custom_value=True,)
            self.desc_presets = gr.Textbox(label="", placeholder="描述信息，可选", interactive=True)
            with gr.Row():
                self.save_presets_btn = gr.Button(value="保存预设", variant="primary")
                self.refresh_presets_btn = gr.Button(value="刷新", variant="secondary")
            self.save_presets_btn.click(
                self.save_preset,
                inputs=[
                    self.choose_presets,
                    self.desc_presets,
                    self.refer_audio,
                    self.aux_ref_audio,
                    self.refer_text,
                    self.refer_lang,
                    self.sovits_path,
                    self.gpt_path,
                ],
                outputs=[],
            )
        with gr.Row():
            self.gen_btn2=gr.Button(value="生成",variant="primary",visible=True)    

        self.refresh_presets_btn.click(self.refresh_presets_list, outputs=[self.choose_presets])
        self.switch_gsvmodel_btn.click(self.switch_gsvmodel,inputs=[self.sovits_path,self.gpt_path,self.api_port2],outputs=[]) 
        self.choose_presets.change(self.load_preset,inputs=[self.choose_presets,self.api_port2],outputs=[self.sovits_path,self.gpt_path,self.desc_presets,self.refer_audio,self.aux_ref_audio,self.refer_text,self.refer_lang])
        GSV_ARGS = [
            self.sampling_rate2,
            self.language2,
            self.api_port2,
            self.refer_audio,
            self.aux_ref_audio,
            self.refer_text,
            self.refer_lang,
            self.batch_size,
            self.batch_threshold,
            self.fragment_interval,
            self.speed_factor,
            self.top_k,
            self.top_p,
            self.temperature,
            self.repetition_penalty,
            self.split_bucket,
            self.how_to_cut,
            self.gpt_path,
            self.sovits_path
        ]
        return GSV_ARGS

    def arg_filter(self,*args):
        in_file,fps,offset,max_workers,sr,language,port,refer_audio,aux_ref_audio,refer_text,refer_lang,batch_size,batch_threshold,fragment_interval,speed_factor,top_k,top_p,temperature,repetition_penalty,split_bucket,text_split_method,gpt_path,sovits_path=args
        if refer_audio is None:
            gr.Warning("你必须指定参考音频")
            raise Exception("你必须指定参考音频")
        refer_audio_path=temp_ra(refer_audio)
        aux_ref_audio_path=[temp_aux_ra(i) for i in aux_ref_audio] if aux_ref_audio is not None else []      
        pargs=(dict_language[language],port,refer_audio_path,aux_ref_audio_path,refer_text,dict_language[refer_lang],batch_size,batch_threshold,fragment_interval,speed_factor,top_k,top_p,temperature,repetition_penalty,split_bucket,cut_method[text_split_method])
        kwargs={'in_file':in_file,'sr':sr,'fps':fps,'offset':offset,'proj':"gsv",'max_workers':max_workers}
        return pargs,kwargs

    def load_preset(self,name,port):
        try:
            if name=='None'or not os.path.exists(os.path.join(current_path,"SAVAdata","presets",name)):
                return gr.update(),gr.update(),gr.update(label="",value="",placeholder="描述信息，可选",interactive=True),gr.update(),gr.update(),gr.update(),gr.update(),gr.update()
            data=json.load(open(os.path.join(current_path,"SAVAdata","presets",name,"info.json"), encoding="utf-8"))
            if "auxiliary_audios" not in list(data.keys()):
                data["auxiliary_audios"] = None
            if data["sovits_path"] !="" and data["gpt_path"] != "":
                if not self.switch_gsvmodel(sovits_path=data["sovits_path"],gpt_path=data["gpt_path"],port=port,force=False):
                    gr.Warning("模型切换失败")
            if not os.path.exists(data["reference_audio_path"]) and os.path.exists(os.path.join(current_path,"SAVAdata","presets",name,"reference_audio.wav")):
                data["reference_audio_path"]=os.path.join(current_path,"SAVAdata","presets",name,"reference_audio.wav")
            if data["auxiliary_audios"] is not None:                   
                aux_audio=[os.path.join(current_path,"SAVAdata","presets",name,i) for i in data["auxiliary_audios"] if os.path.exists(os.path.join(current_path,"SAVAdata","presets",name,i))]
                if len(aux_audio)!=len(data["auxiliary_audios"]):
                    gr.Warning("辅助参考音频存在丢失！")
                data["auxiliary_audios"]=aux_audio
            gr.Info("预设加载完毕")
            return data["sovits_path"],data["gpt_path"],data["description"],data["reference_audio_path"],data["auxiliary_audios"],data["reference_audio_text"],data["reference_audio_lang"]
        except Exception as e:
            gr.Warning(f"加载失败:{e}")
            return gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update()

    def switch_gsvmodel(self,sovits_path,gpt_path,port,force=True):
        if not force and sovits_path==self.current_sovits_model and gpt_path==self.current_gpt_model:
            gr.Info("当前未切换模型,若需要强制切换请手动点击按钮")
            return True
        if sovits_path=="" or gpt_path=="":
            if force:
                gr.Info("请指定模型路径！")
            return False
        gr.Info("正在切换模型...")
        try:        
            data_json={
            "sovits_model_path": sovits_path.strip('"'),
            "gpt_model_path": gpt_path.strip('"'),
            } 
            for x in data_json.values(): 
                if not os.path.isfile(x):
                    gr.Warning("模型路径可能无效，会导致切换错误！")
                if os.path.isdir(x):
                    raise gr.Error("你错误地填写了文件夹路径！！！")
            # print(data_json)
            port=int(port)
            if self.gsv_fallback:
                API_URL=f'http://127.0.0.1:{port}/set_model/'
                response = requests.post(url=API_URL,json=data_json)
                response.raise_for_status()
            else:
                API_URL = f'http://127.0.0.1:{port}/set_gpt_weights'
                response = requests.get(url=API_URL, params={"weights_path":data_json["gpt_model_path"]})
                response.raise_for_status()
                API_URL = f'http://127.0.0.1:{port}/set_sovits_weights'
                response = requests.get(url=API_URL, params={"weights_path":data_json["sovits_model_path"]})
                response.raise_for_status()
            self.current_sovits_model = sovits_path
            self.current_gpt_model = gpt_path
            gr.Info("模型已切换")
            logger.info(f"模型已切换：{data_json}")
            return True
        except Exception as e:
            err=f'GPT-SoVITS切换模型发生错误。报错内容: {e}'
            try:
                err+=f"返回信息：{response.json()}"
            except:
                pass
            gr.Warning(err)
            logger.error(err)
            return False

    def refresh_presets_list(self):
        self.presets_list=['None']
        try:
            preset_dir=os.path.join(current_path,"SAVAdata","presets")
            if os.path.isdir(preset_dir):
                self.presets_list+=[i for i in os.listdir(preset_dir) if os.path.isdir(os.path.join(preset_dir,i))]
            else:
                logger.info("当前没有预设")
        except Exception as e:
            self.presets_list = ["None"]
            err=f"刷新预设失败：{e}"
            logger.error(err)
            gr.Warning(err)
        time.sleep(0.1)
        return gr.update(value="None", choices=self.presets_list)

    def save_preset(self,name,description,ra,ara,rt,rl,sovits_path,gpt_path):
        try:
            if name=="None" or name=="":
                gr.Info("请输入名称!")
                # return "请输入名称"
            if ra is None:
                gr.Info("请上传参考音频!")
                # return "请上传参考音频"
            dir=os.path.join(current_path,"SAVAdata","presets",name)
            os.makedirs(dir,exist_ok=True)
            idx=1
            aux_list=[]
            if ara not in [None,[]]:
                for i in ara:
                    try:
                        with open(os.path.join(dir, f"aux_{idx}.wav"), "wb") as f:
                            f.write(i)             
                        aux_list.append(f"aux_{idx}.wav")
                        idx+=1
                    except Exception as ex:
                        print(ex)
                        continue
            data={"name":name,
                "description":description,
                "reference_audio_path":os.path.join(dir,"reference_audio.wav"),
                "reference_audio_text":rt,
                "auxiliary_audios":aux_list if len(aux_list)!=0 else None,
                "reference_audio_lang":rl,
                "sovits_path":sovits_path.strip('"'),
                "gpt_path":gpt_path.strip('"')
                }
            sr,wav=ra
            sf.write(os.path.join(dir,"reference_audio.wav"), wav, sr)
            with open(os.path.join(dir,"info.json"), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False) 
            time.sleep(0.1)
            gr.Info("预设保存成功")
            # return "预设保存成功"
        except Exception as e:
            gr.Warning(f"出错：{e}")
            # return f"出错：{e}"
