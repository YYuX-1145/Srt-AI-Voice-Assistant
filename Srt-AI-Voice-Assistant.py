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
import soundfile as sf
import datetime
import time
import subprocess
import concurrent.futures
import sys
readme="""
# Srt-AI-Voice-Assistant
`Srt-AI-Voice-Assistant`是一个便捷的，通过API调用Bert-VITS2-HiyoriUI和GPT-SoVITS为上传的.srt字幕文件生成音频的工具。
当前的代码不够完善，如遇到bug或者有什么建议，可以在 https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/issues 上反馈  


0323：
[请注意]：你现在正在使用测试版本，只适配fast-inference分支的测试API，更新的API文件见仓库（仅用于测试，分支合并后有可能会发生变动）！

0316功能更新：  
1.支持启动API服务，请在设置中填写并保存  
2.支持GSV模型切换（*重要！你可能需要拉取代码更新api.py）  
3.支持保存GSV提示音频和模型预设  

0311修复更新：  
1.offset可以为负值  
2.部分函数改为传不定参（可能有疏忽产生bug，要即时反馈，也可使用0308旧版），为接下来的新功能做准备  

"""



log_colors = {
    'DEBUG': 'white',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',}
logger = logging.getLogger()
logger.setLevel(logging.INFO)
try:
    import colorlog    
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
    fmt='%(log_color)s[%(levelname)s][%(asctime)s]:%(funcName)s: %(message)s',
    datefmt='%Y-%m-%d_%H:%M:%S',
    log_colors=log_colors
))
    logger.addHandler(handler)    
except ImportError:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter=logging.Formatter('[%(levelname)s][%(asctime)s]:%(funcName)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("彩色提示信息不可用，可选择安装依赖：colorlog")

class subtitle:
    def __init__(self,index:int, start_time, end_time, text:str):
        self.index = int(index)
        self.start_time = start_time
        self.end_time = end_time
        self.text = text.strip()
    def normalize(self,ntype:str,fps=30):
         if ntype=="prcsv":
              h,m,s,fs=(self.start_time.replace(';',':')).split(":")#seconds
              self.start_time=int(h)*3600+int(m)*60+int(s)+round(int(fs)/fps,2)
              h,m,s,fs=(self.end_time.replace(';',':')).split(":")
              self.end_time=int(h)*3600+int(m)*60+int(s)+round(int(fs)/fps,2)
         elif ntype=="srt":
             h,m,s=self.start_time.split(":")
             s=s.replace(",",".")
             self.start_time=int(h)*3600+int(m)*60+round(float(s),2)
             h,m,s=self.end_time.split(":")
             s=s.replace(",",".")
             self.end_time=int(h)*3600+int(m)*60+round(float(s),2)
         else:
             raise ValueError
    def add_offset(self,offset=0):
        self.start_time+=offset
        if self.start_time<0:
            self.start_time=0
        self.end_time+=offset
        if self.end_time<0:
            self.end_time=0
    def __str__(self) -> str:
        return f'id:{self.index},start:{self.start_time},end:{self.end_time},text:{self.text}'

class Settings:
    def __init__(self,server_port:int=6661,theme:str="default",clear_tmp:bool=False,bv2_pydir:str="",gsv_pydir:str="",bv2_dir:str="",gsv_dir:str="",bv2_args:str="",gsv_args:str=""):
        self.server_port=int(server_port)
        self.theme=theme
        self.clear_tmp=clear_tmp
        self.bv2_pydir=bv2_pydir
        self.gsv_pydir=gsv_pydir
        self.bv2_dir=bv2_dir
        self.gsv_dir=gsv_dir
        self.bv2_args=bv2_args
        self.gsv_args=gsv_args
        if bv2_pydir!="":
            if bv2_dir=="":
                self.bv2_dir=os.path.dirname(os.path.dirname(bv2_pydir))
        if gsv_pydir!="":        
            if gsv_dir=="":   
                self.gsv_dir=os.path.dirname(os.path.dirname(gsv_pydir))
    def to_dict(self):
        return self.__dict__        
    def save(self):
        dict= self.to_dict()
        os.makedirs(os.path.join("SAVAdata"),exist_ok=True)
        with open(os.path.join("SAVAdata","config.json"), 'w', encoding='utf-8') as f:
            json.dump(dict, f, indent=2, ensure_ascii=False) 
    @classmethod
    def from_dict(cls, dict):
        return cls(**dict)

# https://huggingface.co/datasets/freddyaboulton/gradio-theme-subdomains/resolve/main/subdomains.json
gradio_hf_hub_themes = [
    "default",
    "base",
    "glass",
    "soft",
    "gradio/monochrome",
    "gradio/seafoam",    
    "gradio/dracula_test",
    "abidlabs/dracula_test",
    "abidlabs/Lime",
    "abidlabs/pakistan",
    "Ama434/neutral-barlow",
    "dawood/microsoft_windows",
    "finlaymacklon/smooth_slate",
    "Franklisi/darkmode",
    "freddyaboulton/dracula_revamped",
    "freddyaboulton/test-blue",
    "gstaff/xkcd",
    "Insuz/Mocha",
    "Insuz/SimpleIndigo",
    "JohnSmith9982/small_and_pretty",
    "nota-ai/theme",
    "nuttea/Softblue",
    "ParityError/Anime",
    "reilnuud/polite",
    "remilia/Ghostly",
    "rottenlittlecreature/Moon_Goblin",
    "step-3-profit/Midnight-Deep",
    "Taithrah/Minimal",
    "ysharma/huggingface",
    "ysharma/steampunk",
    "NoCrypt/miku"
]

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
                print(data_json)

                response = requests.get(url=API_URL,params=data_json)
                response.raise_for_status()  # 检查响应的状态码
                return response.content
    except Exception as e:
            logger.error(f'bert-vits2推理发生错误，请检查HiyoriUI是否正确运行。报错内容: {e}')
            return None


def gsv_api(port,**kwargs):
    try:
        '''
        data_json={
        "refer_wav_path": ra,
        "prompt_text": prompt_text,
        "prompt_language": prompt_language,
        "text": text,
        "text_language": text_language
    }   '''
        data_json=kwargs
        print(data_json)
        API_URL = f'http://127.0.0.1:{port}'
        response = requests.get(url=API_URL,params=data_json)
        response.raise_for_status()  # 检查响应的状态码
        return response.content
    except Exception as e:
        logger.error(f'GPT-SoVITS推理发生错误，请检查API服务是否正确运行。报错内容: {e}')
        return None

def file_show(file):
    if file is None:
        return ""
    try:
      with open(file.name, "r", encoding="utf-8") as f:
         text = f.read()
      return text
    except Exception as error:
        return error

def temp_ra(a:tuple):
    sr,wav=a
    os.makedirs(os.path.join("SAVAdata","temp"),exist_ok=True)
    sf.write(os.path.join("SAVAdata","temp","tmp_reference_audio.wav"), wav, sr)



def generate(*args,proj,in_file,sr,fps,offset,max_workers):
        t1 = time.time()
        sr,fps=positive_int(sr,fps)
        audiolist=[]
        if in_file is None:
            return None,"请上传字幕文件！"
        if in_file.name.endswith(".csv"):
           subtitle_list=read_prcsv(in_file.name,fps,offset)
        elif in_file.name.endswith(".srt"):
            subtitle_list=read_srt(in_file.name,offset)
        else:
            return None,"未知的格式，请确保扩展名正确！"
        ptr=0
        t=datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dirname=os.path.join("SAVAdata","temp",t)
        os.makedirs(dirname,exist_ok=True)
        print(max_workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            file_list = list(executor.map(lambda x: save(x[0], **x[1]),[[args, {'proj': proj, 'text': i.text, 'dir': dirname, 'subid': i.index}] for i in subtitle_list]))
        file_list=[i for i in file_list if i is not None]
        for i in subtitle_list:
            start_frame=int(i.start_time*sr)
            if ptr<start_frame:
                silence_len=start_frame-ptr
                audiolist.append(np.zeros(silence_len))
                ptr+=silence_len
            elif ptr>start_frame:
                logger.warning(f"序号为{i.index},内容为:{i.text} 的字幕由于之前的音频过长而被延迟")                   
            f_path=os.path.join(dirname,f"{i.index}.wav")
            if f_path in file_list:
                wav, _ = librosa.load(f_path, sr=sr)
                dur=wav.shape[-1]             #frames
                ptr+=dur
                audiolist.append(wav)
        audio=np.concatenate(audiolist)
        assert len(file_list)!=0,"所有的字幕合成都出错了，请检查API服务！"
        os.makedirs(os.path.join("SAVAdata","output"),exist_ok=True)
        sf.write(os.path.join("SAVAdata","output",f"{t}.wav"), audio, sr)
        t2 = time.time()
        m, s = divmod(t2-t1, 60)
        use_time="%02d:%02d"%(m, s)
        if len(file_list)!=len(subtitle_list):
            return (sr,audio),f'完成,但某些字幕的合成出现了错误,请查看控制台的提示信息。所用时间:{use_time}'
        return (sr,audio),f'完成！所用时间:{use_time}'

def generate_bv2(in_file,sr,fps,offset,language,port,max_workers,mid,spkid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale):
        return generate(language,port,mid,spkid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale,in_file=in_file,sr=sr,fps=fps,offset=offset,proj="bv2",max_workers=max_workers)    
def generate_gsv(in_file,sr,fps,offset,language,port,max_workers,refer_audio,refer_text,refer_lang,batch_size,fragment_interval,speed_factor,top_k,top_p,temperature,split_bucket,text_split_method):
        refer_audio_path=os.path.realpath(os.path.join("SAVAdata","temp","tmp_reference_audio.wav"))    
        if refer_audio is None or refer_text == "":
            return None,"你必须指定参考音频和文本"                
        temp_ra(refer_audio)         
        return generate(language,port,refer_audio_path,refer_text,refer_lang,batch_size,fragment_interval,speed_factor,top_k,top_p,temperature,split_bucket,text_split_method,in_file=in_file,sr=sr,fps=fps,offset=offset,proj="gsv",max_workers=max_workers)

def read_srt(filename,offset):
    with open(filename,"r",encoding="utf-8") as f:
        file=f.readlines()
    subtitle_list=[]
    indexlist=[]
    filelength=len(file)
    for i in range(0,filelength):
        if " --> " in file[i]:
            is_st=True
            for char in file[i-1].strip().replace("\ufeff",""):
                if char not in ['0','1','2','3','4','5','6','7','8','9']:
                    is_st=False
                    break
            if is_st:
                indexlist.append(i) #get line id
    listlength=len(indexlist)
    for i in range(0,listlength-1):
        st,et=file[indexlist[i]].split(" --> ")
        id=int(file[indexlist[i]-1].strip().replace("\ufeff",""))
        text=""
        for x in range(indexlist[i]+1,indexlist[i+1]-2):
            text+=file[x]
        st=subtitle(id,st,et,text)
        st.normalize(ntype="srt")
        st.add_offset(offset=offset)
        subtitle_list.append(st)
    st,et=file[indexlist[-1]].split(" --> ")
    id=file[indexlist[-1]-1]
    text=""
    for x in range(indexlist[-1]+1,filelength):
        text+=file[x]
    st=subtitle(id,st,et,text)
    st.normalize(ntype="srt")
    st.add_offset(offset=offset)
    subtitle_list.append(st)
    return subtitle_list

def run_command(command,dir):
    command=f'start cmd /k "{command}"'
    subprocess.Popen(command,cwd=dir,shell=True)
    logger.info(f'执行命令:'+command)
    time.sleep(0.1)

def read_prcsv(filename,fps,offset):
    try:           
        with open(filename,"r",encoding="utf-8",newline='') as csvfile:
            reader = list(csv.reader(csvfile))
            lenth=len(reader)
            subtitle_list=[]
            stid=1  
            for index in range(1,lenth):
             if reader[index]==[]:
                  continue
             st=subtitle(stid,reader[index][0],reader[index][1],reader[index][2])
             st.normalize(ntype="prcsv",fps=fps)
             st.add_offset(offset=offset)
             subtitle_list.append(st)
             stid+=1
            return subtitle_list
        #            
    except Exception as e:
         logger.error(f"读取字幕文件出错：{str(e)}")

def save(args,proj:str=None,text:str=None,dir:str=None,subid:int=None):
    if proj=="bv2":
        language,port,mid,sid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale=args
        sid,port,mid=positive_int(sid,port,mid)
        if speaker_name is not None and speaker_name!="":
            audio = bert_vits2_api(text=text,mid=mid,spk_name=speaker_name,sid=None,lang=language,length=length_scale,noise=noise_scale,noisew=noise_scale_w,sdp=sdp_ratio,split=False,style_text=None,style_weight=0,port=port)
        else:
            audio = bert_vits2_api(text=text,mid=mid,spk_name=None,sid=sid,lang=language,length=length_scale,noise=noise_scale,noisew=noise_scale_w,sdp=sdp_ratio,split=False,style_text=None,style_weight=0,port=port)
    elif proj=="gsv":
        text_language,port,refer_wav_path,prompt_text,prompt_language,batch_size,fragment_interval,speed_factor,top_k,top_p,temperature,split_bucket,text_split_method=args
        port=positive_int(port)[0]
        audio = gsv_api(port,text=text,text_language=text_language,refer_wav_path=refer_wav_path,prompt_text=prompt_text,prompt_language=prompt_language,batch_size=batch_size,fragment_interval=fragment_interval,speed_factor=speed_factor,top_k=top_k,top_p=top_p,temperature=temperature,split_bucket=split_bucket,text_split_method=text_split_method)
    if audio is not None:
            if audio[:4] == b'RIFF' and audio[8:12] == b'WAVE':
                filepath=os.path.join(dir,f"{subid}.wav")
                with open(filepath,'wb') as file:
                    file.write(audio)
                    return filepath            
            else:
                data=json.loads(audio)
                logger.error(f"出错字幕id：{subid},接收报错数据为：{str(data)}")
                return None
    else:
        logger.error(f"出错字幕id：{subid}")
        return None
    


def switch_spk(choice):
    if choice=="输入id":
        return gr.update(label="说话人ID",value=0,visible=True,interactive=True),gr.update(label="说话人名称",visible=False,value="",interactive=True)
    else:
        return gr.update(label="说话人ID",value=0,visible=False,interactive=True),gr.update(label="说话人名称",visible=True,value="",interactive=True)
        
def cls_cache():
    dir=os.path.join("SAVAdata","temp")
    if os.path.exists(dir):
        shutil.rmtree(dir)
        logger.info("成功清除缓存！")
    else:
        logger.info("目前没有缓存！")

def save_settngs(server_port,clear_tmp,theme,bv2_pydir,bv2_dir,gsv_pydir,gsv_dir,bv2_args,gsv_args):
    global config
    config=Settings(server_port=server_port,theme=theme,clear_tmp=clear_tmp,bv2_pydir=bv2_pydir.strip('"'),bv2_dir=bv2_dir.strip('"'),gsv_pydir=gsv_pydir.strip('"'),gsv_dir=gsv_dir.strip('"'),bv2_args=bv2_args,gsv_args=gsv_args)
    config.save()
    logger.info("已经保存了设置")
    return config.server_port,config.clear_tmp,config.theme,config.bv2_pydir,config.bv2_dir,config.gsv_pydir,config.gsv_dir,config.bv2_args,config.gsv_args

def load_cfg():
    global config    
    config_path=os.path.join("SAVAdata","config.json")
    if os.path.exists(config_path):        
        try:
            config=Settings.from_dict(json.load(open(config_path, encoding="utf-8")))          
        except Exception as e:
            config=Settings()
            logger.warning(f"用户设置加载失败，恢复默认设置！{e}")
    else:
        config=Settings()
        logger.info("当前没有自定义设置")

def start_hiyoriui():
    global config
    if config.bv2_pydir=="":
        return "请前往设置页面指定环境路径并保存!"    
    command=f'"{config.bv2_pydir}" "{os.path.join(config.bv2_dir,"hiyoriUI.py")}" {config.bv2_args}'
    run_command(command=command,dir=config.bv2_dir)
    time.sleep(0.1)
    return "HiyoriUI已启动，请确保其配置文件无误"

def start_gsv():
    global config
    if config.gsv_pydir=="":
        return "请前往设置页面指定环境路径并保存!"
    command=f'"{config.gsv_pydir}" "{os.path.join(config.gsv_dir,"GPT_SoVITS","api_simple.py")}" {config.gsv_args}'
    run_command(command=command,dir=config.gsv_dir)
    time.sleep(0.1)
    return "GSV-API服务已启动，请确保其配置文件无误"

def save_preset(name,description,ra,rt,rl,sovits_path,gpt_path):
    try:
        if name=="None" or name=="":
            return "请输入名称"
        if ra is None:
            return "请上传参考音频"
        dir=os.path.join("SAVAdata","presets",name)
        os.makedirs(dir,exist_ok=True)
        data={"name":name,
              "description":description,
              "reference_audio_path":os.path.join(dir,"reference_audio.wav"),
              "reference_audio_text":rt,
              "reference_audio_lang":rl,
              "sovits_path":sovits_path.strip('"'),
              "gpt_path":gpt_path.strip('"')
              }
        sr,wav=ra
        sf.write(os.path.join(dir,"reference_audio.wav"), wav, sr)
        with open(os.path.join(dir,"info.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False) 
        time.sleep(0.1)
        return "预设保存成功"
    except Exception as e:
        return f"出错：{e}"

def load_preset(name,port):
    try:
        global current_sovits_model
        global current_gpt_model
        if name=='None'or not os.path.exists(os.path.join("SAVAdata","presets",name)):
            return gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update()
        data=json.load(open(os.path.join("SAVAdata","presets",name,"info.json"), encoding="utf-8"))
        if data["sovits_path"] !="" and data["gpt_path"] != "":
            if data["sovits_path"]==current_sovits_model and data["gpt_path"]==current_gpt_model:
               switch=False
               time.sleep(0.1)
            else:
               assert switch_gsvmodel(sovits_path=data["sovits_path"],gpt_path=data["gpt_path"],port=port)=='模型切换成功',"模型切换失败"
               current_sovits_model=data["sovits_path"]
               current_gpt_model=data["gpt_path"]
               switch=True
        return data["sovits_path"],data["gpt_path"],data["description"],data["reference_audio_path"],data["reference_audio_text"],data["reference_audio_lang"],"预设加载成功" if switch else "预设加载成功,无需切换模型,若需要强制切换请手动点击按钮"
    except Exception as e:
        return gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),f"加载失败:{e}"

def switch_gsvmodel(sovits_path,gpt_path,port):
    if sovits_path=="" or gpt_path=="":
        return "请指定模型路径！"
    try:
        data_json={
        "sovits_model_path": sovits_path.strip('"'),
        "gpt_model_path": gpt_path.strip('"'),
    }   
        print(data_json)
        port=int(port)
        API_URL = f'http://127.0.0.1:{port}/set_model'
        response = requests.post(url=API_URL,json=data_json)
        response.raise_for_status()
        #print(response.content)
        logger.info(f"模型已切换：{data_json.values()}")
        return '模型切换成功'
    except Exception as e:
        err=f'GPT-SoVITS切换模型发生错误。报错内容: {e}'
        logger.error(err)
        return err

def refresh_presets_list():
    global presets_list
    presets_list=['None']
    try:
        presets_list+=[i for i in os.listdir(os.path.join("SAVAdata","presets")) if os.path.isdir(os.path.join("SAVAdata","presets",i))]
    except Exception as e:
        presets_list=['None']
        logger.error(f"刷新预设失败：{e}")
    time.sleep(0.1)
    return gr.update(value="None",choices=presets_list)

def restart():
    os.execl(sys.executable,f'"{sys.executable}"',f'"{os.path.abspath(__file__)}"')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-p", "--server_port",type=int,help="server_port")
    parser.add_argument('-share', dest='share', action="store_true", default=False, help="set share True")
    args, unknown = parser.parse_known_args()
    
    refresh_presets_list()
    current_sovits_model=None
    current_gpt_model=None   
    load_cfg()
    if config.clear_tmp:
        cls_cache()                 
    if args.server_port is None:
        server_port=config.server_port
    else:
        server_port=args.server_port

    with gr.Blocks(title="Srt-AI-Voice-Assistant-WebUI",theme=config.theme) as app:
        gr.Markdown(value="版本240324dev，支持HiyoriUI和GPT-SoVITS-FastInference分支")
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
                                language1 = gr.Dropdown(choices=['ZH','JP','EN','AUTO'], value='ZH', label="Language",interactive=True,allow_custom_value=False)
                                with gr.Accordion(label="参数",open=False):
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
                        language2 = gr.Dropdown(choices=["中文","日文","英文","中英混合","日英混合","多语种混合"], value="中英混合", label="Language",interactive=True,allow_custom_value=False)
                        refer_audio=gr.Audio(label="参考音频")
                        with gr.Row():
                            refer_text=gr.Textbox(label="参考音频文本")
                            refer_lang = gr.Dropdown(choices=["中文","日文","英文","中英混合","日英混合","多语种混合"], value='中文', label="参考音频语言",interactive=True,allow_custom_value=False)
                        with gr.Accordion("模型切换",open=False):
                            sovits_path=gr.Textbox(value="",label="Sovits模型路径",interactive=True)
                            gpt_path=gr.Textbox(value="",label="GPT模型路径",interactive=True)
                            switch_gsvmodel_btn=gr.Button(value="切换模型",variant="primary")
                        with gr.Row():
                            sampling_rate2=gr.Number(label="采样率",value=32000,visible=True,interactive=True)
                            api_port2=gr.Number(label="API Port",value=9880,visible=True,interactive=True)
                        with gr.Accordion("高级合成参数",open=False):
                            batch_size = gr.Slider(minimum=1,maximum=200,step=1,label="batch_size",value=20,interactive=True)
                            fragment_interval = gr.Slider(minimum=0.01,maximum=1,step=0.01,label="分段间隔(秒)",value=0.3,interactive=True)
                            speed_factor = gr.Slider(minimum=0.25,maximum=4,step=0.05,label="speed_factor",value=1.0,interactive=True)
                            top_k = gr.Slider(minimum=1,maximum=100,step=1,label="top_k",value=5,interactive=True)
                            top_p = gr.Slider(minimum=0,maximum=1,step=0.05,label="top_p",value=1,interactive=True)
                            temperature = gr.Slider(minimum=0,maximum=1,step=0.05,label="temperature",value=1,interactive=True)
                            split_bucket = gr.Checkbox(label="数据分桶", value=True, interactive=True, show_label=True)
                            how_to_cut = gr.Radio(label="怎么切",choices=["不切","凑四句一切","凑50字一切","按中文句号。切","按英文句号.切","按标点符号切"],
                                                 value="凑四句一切",interactive=True)
                        with gr.Accordion("预设",open=False):
                            choose_presets=gr.Dropdown(label="",value='None',choices=presets_list,interactive=True,allow_custom_value=True)
                            desc_presets=gr.Textbox(label="",placeholder="描述信息，可选",interactive=True)
                            with gr.Row():
                                save_presets_btn=gr.Button(value="保存预设",variant="primary")
                                refresh_presets_btn=gr.Button(value="刷新",variant="secondary")
                        with gr.Row():
                            gen_btn2=gr.Button(value="生成",variant="primary",visible=True)
                                                   

                    with gr.Column():                  
                       fps=gr.Number(label="Pr项目帧速率,仅适用于Pr导出的csv文件",value=30,visible=True,interactive=True,minimum=1)
                       workers=gr.Number(label="调取合成线程数(高于1时请增加api的workers数量)",value=1,visible=True,interactive=True,minimum=1)
                       offset=gr.Slider(minimum=-6, maximum=6, value=0, step=0.1, label="语音时间偏移(秒) 延后或提前所有语音的时间")
                       input_file = gr.File(label="上传文件",file_types=['.csv','.srt'],file_count='single') # works well in gradio==3.38                 
                       gen_textbox_output_text=gr.Textbox(label="输出信息", placeholder="点击处理按钮",interactive=False)
                       audio_output = gr.Audio(label="Output Audio")
                       with gr.Accordion("启动服务"):
                           gr.Markdown(value="请先在设置中应用项目路径")
                           start_hiyoriui_btn=gr.Button(value="启动HiyoriUI")
                           start_gsv_btn=gr.Button(value="启动GPT-SoVITS")               
            with gr.TabItem("设置"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("点击应用后，这些设置才会生效。")
                        server_port_set=gr.Number(label="本程序所使用的端口，重启生效。当冲突无法启动时，使用参数-p来指定启动端口",value=config.server_port)
                        clear_cache=gr.Checkbox(label="每次启动时清除缓存",value=config.clear_tmp,interactive=True)
                        theme = gr.Dropdown(choices=gradio_hf_hub_themes, value=config.theme, label="选择主题，重启后生效，部分主题可能需要科学上网",interactive=True)
                        cls_cache_btn=gr.Button(value="立即清除缓存",variant="primary")
                        with gr.Group():
                            gr.Markdown(value="BV2")
                            bv2_pydir_input=gr.Textbox(label="设置BV2环境路径",interactive=True,value=config.bv2_pydir)
                            bv2_dir_input=gr.Textbox(label="设置BV2项目路径,使用整合包可不填",interactive=True,value=config.bv2_dir)
                            bv2_args=gr.Textbox(label="设置BV2启动参数",interactive=True,value=config.bv2_args)
                        with gr.Group():
                            gr.Markdown(value="GSV")
                            gsv_pydir_input=gr.Textbox(label="设置GSV环境路径",interactive=True,value=config.gsv_pydir)
                            gsv_dir_input=gr.Textbox(label="设置GSV项目路径,使用整合包可不填",interactive=True,value=config.gsv_dir)
                            gsv_args=gr.Textbox(label="设置GSV-API启动参数",interactive=True,value=config.gsv_args)        
                        save_settings_btn=gr.Button(value="应用并保存当前设置",variant="primary")
                        restart_btn=gr.Button(value="重启UI",variant="stop")
                    with gr.Column():
                        gr.Markdown(value=readme)


        input_file.change(file_show,inputs=[input_file],outputs=[textbox_intput_text])
        spkchoser.change(switch_spk,inputs=[spkchoser],outputs=[spkid,speaker_name])
        gen_btn1.click(generate_bv2,inputs=[input_file,sampling_rate1,fps,offset,language1,api_port1,workers,model_id,spkid,speaker_name,sdp_ratio,noise_scale,noise_scale_w,length_scale],outputs=[audio_output,gen_textbox_output_text])
        gen_btn2.click(generate_gsv,inputs=[input_file,sampling_rate2,fps,offset,language2,api_port2,workers,refer_audio,refer_text,refer_lang,batch_size,fragment_interval,speed_factor,top_k,top_p,temperature,split_bucket,how_to_cut],outputs=[audio_output,gen_textbox_output_text])
        cls_cache_btn.click(cls_cache,inputs=[],outputs=[])
        start_hiyoriui_btn.click(start_hiyoriui,outputs=[gen_textbox_output_text])
        start_gsv_btn.click(start_gsv,outputs=[gen_textbox_output_text])
        switch_gsvmodel_btn.click(switch_gsvmodel,inputs=[sovits_path,gpt_path,api_port2],outputs=[gen_textbox_output_text])
        save_settings_btn.click(save_settngs,inputs=[server_port_set,clear_cache,theme,bv2_pydir_input,bv2_dir_input,gsv_pydir_input,gsv_dir_input,bv2_args,gsv_args],outputs=[server_port_set,clear_cache,theme,bv2_pydir_input,bv2_dir_input,gsv_pydir_input,gsv_dir_input,bv2_args,gsv_args])
        restart_btn.click(restart)

        save_presets_btn.click(save_preset,inputs=[choose_presets,desc_presets,refer_audio,refer_text,refer_lang,sovits_path,gpt_path],outputs=[gen_textbox_output_text])
        choose_presets.change(load_preset,inputs=[choose_presets,api_port2],outputs=[sovits_path,gpt_path,desc_presets,refer_audio,refer_text,refer_lang,gen_textbox_output_text])
        refresh_presets_btn.click(refresh_presets_list,outputs=[choose_presets])
    webbrowser.open(f"http://127.0.0.1:{server_port}")
    app.launch(share=args.share,server_port=server_port)
