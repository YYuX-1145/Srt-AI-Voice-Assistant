import requests
import os
import shutil
import librosa
import numpy as np
import webbrowser
import gradio as gr
import argparse
import csv
import json
import logging
import colorlog
import soundfile as sf
import datetime

class subtitle:
    def __init__(self,index, start_time, end_time, text):
        self.index = int(index.strip().replace("\ufeff",""))
        self.start_time = start_time
        self.end_time = end_time
        self.text = text.strip()
    def normalize(self,ntype:str,fps=30):
         if ntype=="prcsv":
              h,m,s,fs=self.start_time.split(";")#seconds
              self.start_time=int(h)*3600+int(m)*60+int(s)+float(format(int(fs)/fps,'.2f'))
              h,m,s,fs=self.end_time.split(";")
              self.end_time=int(h)*3600+int(m)*60+int(s)+float(format(int(fs)/fps,'.2f'))
         elif ntype=="srt":
             h,m,s=self.start_time.split(":")
             s=s.replace(",",".")
             self.start_time=int(h)*3600+int(m)*60+float(format(float(s),'.2f'))
             h,m,s=self.end_time.split(":")
             s=s.replace(",",".")
             self.end_time=int(h)*3600+int(m)*60+float(format(float(s),'.2f'))
         else:
             raise ValueError
         return self
    def __str__(self) -> str:
        return f'id:{self.index},start:{self.start_time},end:{self.end_time},text:{self.text}'

class settings:
    def __init__(self,clear_tmp=False,bv2_pydir=None,gsv_pydir=None,gsv_dra=None,gsv_drt=None,gsv_dtl=None):
        self.clear_tmp=clear_tmp
        self.bv2_pydir=bv2_pydir
        self.gsv_pydir=gsv_pydir
        self.gsv_dra=gsv_dra
        self.gsv_drt=gsv_drt
        self.gsv_dtl=gsv_dtl
    def save(self):
        dict={
            "clear_tmp":self.clear_tmp,
            "bv2_pydir":self.bv2_pydir,
            "gsv_pydir":self.gsv_pydir,
            "gsv_dra":self.gsv_dra,
            "gsv_drt":self.gsv_drt,
            "gsv_dtl":self.gsv_dtl
        }
        os.makedirs(os.path.join("SRTData","configs"),exist_ok=True)
        with open(os.path.join("SRTData","configs","config.json"), 'w', encoding='utf-8') as f:
            json.dump(dict, f, indent=2, ensure_ascii=False) 
    def load(self,d:dict):
        self.clear_tmp=d["clear_tmp"]
        self.bv2_pydir=d["bv2_pydir"]
        self.gsv_pydir=d["gsv_pydir"]
        self.gsv_dra=d["gsv_dra"]
        self.gsv_drt=d["gsv_drt"]
        self.gsv_dtl=d["gsv_dtl"]


def positive_int(*a):
    r=[]
    for x in a:
        if x < 0:
            x=0
        r.append(int(x))
    return r

def bert_vits2_api(text,mid,spk_name,sid,lang,length,noise,noisew,sdp,split,style_text,style_weight,port):
    try:
                API_URL = f'http://127.0.0.1:{port}/voice'
                data_json = {
                    "text": text,
                    "model_id": mid,
                    "speaker_name": spk_name,
                    "speaker_id": sid,
                    "language": lang,
                    "length": length,
                    "noise": noise,
                    "noisew": noisew,
                    "sdp_ratio": sdp,
                    "auto_translate": False,
                    "auto_split": split,
                    "style_text": style_text,
                    "style_weight": style_weight
                }
                #print(data_json)

                response = requests.get(url=API_URL,params=data_json)
                response.raise_for_status()  # 检查响应的状态码
                return response.content
    except Exception as e:
            logger.error(f'bert-vits2推理发生错误，请检查HiyoriUI是否正确运行。报错内容: {e}')


def gsv_api(ra,text,prompt_text,prompt_language,text_language,port):
    try:
        data_json={
        "refer_wav_path": ra,
        "prompt_text": prompt_text,
        "prompt_language": prompt_language,
        "text": text,
        "text_language": text_language
    }   
        API_URL = f'http://127.0.0.1:{port}'
        response = requests.get(url=API_URL,params=data_json)
        response.raise_for_status()  # 检查响应的状态码
        return response.content
    except Exception as e:
        logger.error(f'GPT-SoVITS推理发生错误，请检查API服务是否正确运行。报错内容: {e}')

def file_show(file):
    try:
      with open(file.name, "r", encoding="utf-8") as file:
         text = file.read()
      return gr.TextArea(value=text,interactive=False)
    except Exception as error:
        return gr.TextArea(value=error,interactive=False)

def temp_ra(a:tuple):
    sr,wav=a
    os.makedirs(os.path.join("SRTdata","temp"),exist_ok=True)
    sf.write(os.path.join("SRTdata","temp","tmp_reference_audio.wav"), wav, sr)



def generate(proj,in_file,sr,fps,language,port,mid,spkid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale,refer_audio,refer_text,refer_lang):
        if in_file is None:
            return None,"请上传文件！"
    #try:
        sr,fps,mid,spkid,port=positive_int(sr,fps,mid,spkid,port)
        audiolist=[]
        if in_file.name.endswith(".csv"):
           subtitle_list=read_prcsv(in_file.name,fps)
        elif in_file.name.endswith(".srt"):
            subtitle_list=read_srt(in_file.name)
        else:
            return None,"未知的格式，请确保扩展名正确！"
        ptr=0
        t=datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dirname=os.path.join("SRTdata","temp",t)
        os.makedirs(dirname,exist_ok=True)
        for i in subtitle_list:
            start_frame=int(i.start_time*sr)
            if ptr<start_frame:
                silence_len=start_frame-ptr
                audiolist.append(np.zeros(silence_len))
                ptr+=silence_len
            elif ptr>start_frame:
                logger.warning(f"{i.index}由于之前的音频过长而被延迟")
            refer_audio=os.path.realpath(os.path.join("SRTdata","temp","tmp_reference_audio.wav"))
            
            f_path=save(proj,dirname,i.index,i.text,language,port,mid,spkid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale,refer_audio,refer_text,refer_lang)
            if f_path is not None:
                wav, _ = librosa.load(f_path, sr=sr)
                dur=wav.shape[-1]             #frames
                ptr+=dur
                audiolist.append(wav)
        audio=np.concatenate(audiolist)
        os.makedirs(os.path.join("SRTdata","output"),exist_ok=True)
        sf.write(os.path.join("SRTdata","output",f"{t}.wav"), audio, sr)
        return (sr,audio),"完成！"
 
def read_srt(filename):
    with open(filename,"r",encoding="utf-8") as f:
        file=f.readlines()
    subtitle_list=[]
    indexlist=[]
    filelength=len(file)
    for i in range(0,filelength):
        if " --> " in file[i]:
            for char in file[i-1]:
                if char not in [0,1,2,3,4,5,6,7,8,9]:
                    continue
            indexlist.append(i) #get line id
    listlength=len(indexlist)
    for i in range(0,listlength-1):
        st,et=file[indexlist[i]].split(" --> ")
        id=file[indexlist[i]-1]
        text=""
        for x in range(indexlist[i]+1,indexlist[i+1]-2):
            text+=file[x]
        subtitle_list.append(subtitle(id,st,et,text).normalize(ntype="srt"))
    st,et=file[indexlist[-1]].split(" --> ")
    id=file[indexlist[-1]-1]
    text=""
    for x in range(indexlist[-1]+1,filelength):
        text+=file[x]
    subtitle_list.append(subtitle(id,st,et,text).normalize(ntype="srt"))    
    return subtitle_list




def read_prcsv(filename,fps):
    try:           
        with open(filename,"r",encoding="utf-8") as csvfile:
            reader = list(csv.reader(csvfile))
            lenth=len(reader)
            subtitle_list=[]
            stid=0  
            for index in range(1,lenth):
             if reader[index]==[]:
                  continue
             subtitle_list.append(subtitle(stid,reader[index][0],reader[index][1],reader[index][2]).normalize("prcsv",fps))
             stid+=1
            return subtitle_list
        #            
    except Exception as e:
         logger.error(f"读取字幕文件出错：{str(e)}")

def save(proj,dir,subid,text,language,port,mid,sid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale,refer_audio,refer_text,refer_lang):
    if proj=="bv2":
        if speaker_name is not None and speaker_name!="":
            audio = bert_vits2_api(text=text,mid=mid,spk_name=speaker_name,sid=None,lang=language,length=length_scale,noise=noise_scale,noisew=noise_scale_w,sdp=sdp_ratio,split=False,style_text=None,style_weight=0,port=port)
        else:
            audio = bert_vits2_api(text=text,mid=mid,spk_name=None,sid=sid,lang=language,length=length_scale,noise=noise_scale,noisew=noise_scale_w,sdp=sdp_ratio,split=False,style_text=None,style_weight=0,port=port)
    elif proj=="gsv":
        audio = gsv_api(refer_audio,text,refer_text,refer_lang,language,port)
    if audio is not None:
            if audio[:4] == b'RIFF' and audio[8:12] == b'WAVE':
                filepath=os.path.join(dir,f"{subid}.wav")
                with open(filepath,'wb') as file:
                    file.write(audio)
                    return filepath            
            else:
                data=json.loads(audio)
                logger.error(f"出错字幕id：{subid},接收报错数据为：{str(data)}")
    else:
        logger.error(f"出错字幕id：{subid}")
        return None
    


def switch_spk(choice):
    if choice=="输入id":
        return gr.Number(label="说话人ID",value=0,visible=True,interactive=True),gr.Textbox(label="说话人名称",visible=False,value="",interactive=True)
    else:
        return gr.Number(label="说话人ID",value=0,visible=False,interactive=True),gr.Textbox(label="说话人名称",visible=True,value="",interactive=True)
        
def cls_cache():
    dir=os.path.join("SRTdata","temp")
    if os.path.exists(dir):
        shutil.rmtree(dir)
        logger.info("成功清除缓存！")
    else:
        logger.info("目前没有缓存！")

def save_settngs(clear_temp,gsv_dra,gsv_drt,gsv_dtl):
    global config
    if gsv_dra is not None:
        sr,wav=gsv_dra
        gsv_dra=os.path.join("SRTdata","configs","default_reference_audio.wav")
        sf.write(gsv_dra, wav, sr)
    config=settings(clear_tmp=clear_temp,gsv_dra=gsv_dra,gsv_drt=gsv_drt,gsv_dtl=gsv_dtl)
    config.save()
    logger.info("已经保存了设置")

def load_cfg():
    global config
    config=settings()
    config_path=os.path.join("SRTdata","configs","config.json")
    if os.path.exists(config_path):        
        try:
            config.load(json.load(open(config_path, encoding="utf-8")))
            return config.clear_tmp,config.gsv_dra,config.gsv_drt,config.gsv_dtl
        except:
            logger.warning("用户设置加载失败，恢复默认设置！")
    else:
        logger.info("当前没有自定义设置")

if __name__ == "__main__":
    log_colors = {
    'DEBUG': 'white',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',}
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
    fmt='%(log_color)s[%(levelname)s][%(asctime)s]:%(funcName)s: %(message)s',
    datefmt='%Y-%m-%d_%H:%M:%S',
    log_colors=log_colors
))
    logger.addHandler(handler)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-p", "--server_port", default=6660,type=int,help="server_port"
    )
    args, unknown = parser.parse_known_args()
    config=settings()
    load_cfg()   
              

    with gr.Blocks(title="Srt-API-AI语音合成助手") as app:
        with gr.Tabs():
            with gr.TabItem("API合成"):
                with gr.Row():
                    textbox_intput_text = gr.TextArea(label="文件内容展示", value="",interactive=False)
                     
                    with gr.TabItem("Bert-VITS2-HiyoriUI"):
                        with gr.Row():            
                            with gr.Column():
                                proj1=gr.Radio(choices=['bv2'], value="bv2",interactive=False,visible=False)
                                spkchoser=gr.Radio(label="选择说话人id或输入名称", choices=['输入id','输入名称'], value="输入id")
                                with gr.Row():
                                    model_id=gr.Number(label="模型id",value=0,visible=True,interactive=True)
                                    spkid=gr.Number(label="说话人ID",value=0,visible=True,interactive=True)
                                    speaker_name = gr.Textbox(label="说话人名称",visible=False,interactive=True)
                                language1 = gr.Dropdown(choices=['ZH','JP','EN','AUTO'], value='ZH', label="Language",interactive=True)
                                with gr.Accordion(label="参数"):
                                    sdp_ratio = gr.Slider(minimum=0, maximum=1, value=0.2, step=0.1, label="SDP Ratio")
                                    noise_scale = gr.Slider(minimum=0.1, maximum=2, value=0.6, step=0.1, label="Noise Scale")
                                    noise_scale_w = gr.Slider(minimum=0.1, maximum=2, value=0.8, step=0.1, label="Noise Scale W")
                                    length_scale = gr.Slider(minimum=0.1, maximum=2, value=1, step=0.1, label="Length Scale")
                                with gr.Row(): 
                                    sampling_rate1=gr.Number(label="采样率",value=44100,visible=True,interactive=True)                                
                                    api_port1=gr.Number(label="API Port",value=5000,visible=True,interactive=True)
                                gen_btn1 = gr.Button("生成", variant="primary",visible=True)
                    with gr.TabItem("GPT-SoVITS"):
                        proj2=gr.Radio(choices=['gsv'], value="gsv",interactive=False,visible=False)
                        language2 = gr.Dropdown(choices=['zh','ja','en'], value='zh', label="Language",interactive=True)
                        refer_audio=gr.Audio(label="参考音频")
                        with gr.Row():
                            refer_text=gr.Textbox(label="参考音频文本")
                            refer_lang = gr.Dropdown(choices=['zh','ja','en'], value='zh', label="参考音频语言",interactive=True)
                        with gr.Row():
                            sampling_rate2=gr.Number(label="采样率",value=32000,visible=True,interactive=True)
                            api_port2=gr.Number(label="API Port",value=9880,visible=True,interactive=True)
                        with gr.Row():
                            gen_btn2=gr.Button(value="生成",variant="primary",visible=True)
                            load_cfg_btn=gr.Button(value="加载设置",variant="secondary",visible=True)                       

                    with gr.Column():                  
                       fps=gr.Number(label="Pr项目帧速率,仅适用于Pr导出的csv文件",value=30,visible=True,interactive=True,minimum=1)
                       input_file = gr.Files(label="上传文件",file_types=['text'],file_count='single')
                       #sampling_rate1=                   
                       gen_textbox_output_text=gr.Textbox(label="输出信息", placeholder="点击处理按钮",interactive=False)
                       audio_output = gr.Audio(label="Output Audio")
            with gr.TabItem("设置"):
                with gr.Row():
                    clear_cache=gr.Checkbox(label="每次启动时清除缓存",value=False,interactive=True)
                    cls_cache_btn=gr.Button(value="立即清除缓存",variant="primary")
                    save_settings_btn=gr.Button(value="保存当前设置",variant="primary")


        input_file.upload(file_show,inputs=[input_file],outputs=[textbox_intput_text])
        refer_audio.upload(temp_ra,inputs=[refer_audio],outputs=[])
        spkchoser.change(switch_spk,inputs=[spkchoser],outputs=[spkid,speaker_name])
        gen_btn1.click(generate,inputs=[proj1,input_file,sampling_rate1,fps,language1,api_port1,model_id,spkid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale,refer_audio,refer_text,refer_lang],outputs=[audio_output,gen_textbox_output_text])
        gen_btn2.click(generate,inputs=[proj2,input_file,sampling_rate2,fps,language2,api_port2,model_id,spkid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale,refer_audio,refer_text,refer_lang],outputs=[audio_output,gen_textbox_output_text])
        cls_cache_btn.click(cls_cache,inputs=[],outputs=[])
        load_cfg_btn.click(load_cfg,inputs=[],outputs=[clear_cache,refer_audio,refer_text,refer_lang])
        save_settings_btn.click(save_settngs,inputs=[clear_cache,refer_audio,refer_text,refer_lang],outputs=[])
    webbrowser.open(f"http://127.0.0.1:{args.server_port}")
    app.launch(share=False,server_port=args.server_port)