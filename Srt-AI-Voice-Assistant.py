import os
import sys
# import inspect

if getattr(sys, "frozen", False):
    current_path = os.path.dirname(sys.executable)
    exe = True
elif __file__:
    current_path = os.path.dirname(__file__)
    exe = False
os.environ["current_path"] = current_path

import requests
import shutil

import gradio as gr
import argparse

import json
import soundfile as sf
import datetime
import time
import concurrent.futures

import Sava_Utils
from Sava_Utils.man.manual import Man
from Sava_Utils.utils import *
from Sava_Utils import logger
from Sava_Utils.settings import Settings
from Sava_Utils.subtitle import Base_subtitle,Subtitle,Subtitles

import Sava_Utils.projects
import Sava_Utils.projects.bv2
import Sava_Utils.projects.gsv
import Sava_Utils.projects.mstts
import Sava_Utils.projects.custom

BV2 = Sava_Utils.projects.bv2.BV2()
GSV = Sava_Utils.projects.gsv.GSV()
MSTTS = Sava_Utils.projects.mstts.MSTTS()
CUSTOM = Sava_Utils.projects.custom.Custom()
Projet_dict={"bv2":BV2,"gsv":GSV,"mstts":MSTTS,"custom":CUSTOM}


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


def custom_api(text):
    raise "需要加载自定义API函数！"

def ms_refresh():#language
    MSTTS.update_cfg(config=config)
    MSTTS.getms_speakers()
    if MSTTS.ms_speaker_info == {}:
        return gr.update(value=None,choices=[],allow_custom_value=False)
    choices = list(MSTTS.ms_speaker_info.keys())
    return gr.update(value=choices[0],choices=choices,allow_custom_value=False)

def display_ms_spk(language):#speaker
    if language in [None,""]:
        return gr.update(value=None,choices=[],allow_custom_value=False)
    choices = list(MSTTS.ms_speaker_info[language].keys())
    return gr.update(value=choices[0],choices=choices,allow_custom_value=False)

def display_style_role(language,speaker):
    if language in [None,""] or speaker in [None,""]:
        return gr.update(value=None,choices=[],allow_custom_value=False),gr.update(value=None,choices=[],allow_custom_value=False)
    try:
        choices1 = ["Default"] + MSTTS.ms_speaker_info[language][speaker]["StyleList"]
    except KeyError:
        choices1=["Default"]        
    try:
        choices2=["Default"] + MSTTS.ms_speaker_info[language][speaker]["RolePlayList"]
    except KeyError:       
        choices2=["Default"]
    return gr.update(value=choices1[0],choices=choices1,allow_custom_value=False),gr.update(value=choices2[0],choices=choices2,allow_custom_value=False),

def generate(*args,proj="",in_file="",sr=None,fps=30,offset=0,max_workers=1):
        #global subtitle_list
        t1 = time.time()
        sr,fps=positive_int(sr,fps)
        if in_file is None:
            gr.Info("请上传字幕文件！")
            return None,"请上传字幕文件！",*load_page(Subtitles()),Subtitles()
        if in_file.name[-4:].lower()==".csv":
            subtitle_list=read_prcsv(in_file.name,fps,offset)
        elif in_file.name[-4:].lower()==".srt":
            subtitle_list=read_srt(in_file.name,offset)
        elif in_file.name[-4:].lower()==".txt":
            subtitle_list=read_txt(in_file.name)
        else:
            gr.Warning("未知的格式，请确保扩展名正确！")
            return None,"未知的格式，请确保扩展名正确！",*load_page(Subtitles()),Subtitles()
        t=datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dirname=os.path.join(current_path,"SAVAdata","temp",t)
        subtitle_list.sort()
        subtitle_list.set_dir(dirname)
        subtitle_list.set_proj(proj)
        Projet_dict[proj].before_gen_action(*args,config=config)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            file_list = list(executor.map(lambda x: save(x[0], **x[1]),[(args, {'proj': proj, 'text': i.text, 'dir': dirname, 'subid': i.index}) for i in subtitle_list]))
        sr,audio = subtitle_list.audio_join(sr=sr)
        os.makedirs(os.path.join(current_path,"SAVAdata","output"),exist_ok=True)
        sf.write(os.path.join(current_path,"SAVAdata","output",f"{t}.wav"), audio, sr)
        t2 = time.time()
        m, s = divmod(t2-t1, 60)
        use_time="%02d:%02d"%(m, s)
        file_list=[i for i in file_list if i is not None]
        if len(file_list)!=len(subtitle_list):
            return (sr,audio),f'完成,但某些字幕的合成出现了错误,请查看控制台的提示信息。所用时间:{use_time}',*load_page(subtitle_list),subtitle_list
        return (sr,audio),f'完成！所用时间:{use_time}',*load_page(subtitle_list),subtitle_list

def generate_bv2(*args):
        args,kwargs=BV2.arg_filter(*args)
        return generate(*args,**kwargs)    

def generate_gsv(*args): 
        try:
            args,kwargs=GSV.arg_filter(*args)
        except Exception as e:
            return None,str(e),*load_page(Subtitles()),Subtitles()
        return generate(*args,**kwargs)

def generate_mstts(*args):
    try:
        args,kwargs=MSTTS.arg_filter(*args)
    except Exception as e:
        return None,str(e),*load_page(Subtitles()),Subtitles()              
    return generate(*args,**kwargs)

def generate_custom(*args):
    try:
        args,kwargs=CUSTOM.arg_filter(*args)
    except Exception as e:
        return None,str(e),*load_page(Subtitles()),Subtitles()
    return generate(args,**kwargs)

def save(args,proj:str=None,text:str=None,dir:str=None,subid:int=None):
    audio = Projet_dict[proj].save_action(*args,text=text)
    if audio is not None:
        if audio[:4] == b'RIFF' and audio[8:12] == b'WAVE':
            # sr=int.from_bytes(audio[24:28],'little')
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
    dir=os.path.join(current_path,"SAVAdata","temp")
    if os.path.exists(dir):
        shutil.rmtree(dir)
        logger.info("成功清除缓存！")
        gr.Info("成功清除缓存！")
    else:
        logger.info("目前没有缓存！")
        gr.Info("目前没有缓存！")

def save_settngs(server_port,clear_tmp,min_interval,num_edit_rows,theme,bv2_pydir,bv2_dir,gsv_pydir,gsv_dir,bv2_args,gsv_args,ms_region,ms_key):
    global config
    current_edit_rows=config.num_edit_rows
    config=Settings(server_port=server_port,theme=theme,clear_tmp=clear_tmp,min_interval=min_interval,num_edit_rows=num_edit_rows,bv2_pydir=bv2_pydir.strip('"'),bv2_dir=bv2_dir.strip('"'),gsv_pydir=gsv_pydir.strip('"'),gsv_dir=gsv_dir.strip('"'),bv2_args=bv2_args,gsv_args=gsv_args,ms_region=ms_region,ms_key=ms_key)
    config.save()
    MSTTS.update_cfg(config=config)
    if config.num_edit_rows!=current_edit_rows:
        config.num_edit_rows=current_edit_rows
        logger.info("更改字幕栏数需要重启生效")
        gr.Info("更改字幕栏数需要重启生效")
    logger.info("成功保存设置！")
    gr.Info("成功保存设置！")
    return config.server_port,config.clear_tmp,config.theme,config.bv2_pydir,config.bv2_dir,config.gsv_pydir,config.gsv_dir,config.bv2_args,config.gsv_args,config.ms_region,config.ms_key

def load_cfg():
    global config 
    config_path=os.path.join(current_path,"SAVAdata","config.json")
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
        gr.Warning("请前往设置页面指定环境路径并保存!")
        return "请前往设置页面指定环境路径并保存!"    
    command=f'"{config.bv2_pydir}" "{os.path.join(config.bv2_dir,"hiyoriUI.py")}" {config.bv2_args}'
    run_command(command=command,dir=config.bv2_dir)
    time.sleep(0.1)
    return "HiyoriUI已启动，请确保其配置文件无误"

def start_gsv():
    global config
    if config.gsv_pydir=="":
        gr.Warning("请前往设置页面指定环境路径并保存!")
        return "请前往设置页面指定环境路径并保存!"
    if os.path.exists(os.path.join(config.gsv_dir,"api_v2.py")):
        apath="api_v2.py"
        GSV.gsv_fallback=False
    else:
        apath="api.py"
        GSV.gsv_fallback=True
        assert os.path.exists(os.path.join(config.gsv_dir,"api.py")),"api文件丢失？？？"
        gr.Warning("api_v2不存在，降级至v1。可能导致兼容问题并且部分功能无法使用。")
        logger.warning("api_v2不存在，降级至v1。可能导致兼容问题并且部分功能无法使用。")

    command=f'"{config.gsv_pydir}" "{os.path.join(config.gsv_dir,apath)}" {config.gsv_args}'
    run_command(command=command,dir=config.gsv_dir)
    time.sleep(0.1)
    return "GSV-API服务已启动，请确保其配置文件无误"

def save_preset(name,description,ra,ara,rt,rl,sovits_path,gpt_path):
    try:
        if name=="None" or name=="":
            gr.Info("请输入名称")
            return "请输入名称"
        if ra is None:
            gr.Info("请上传参考音频")
            return "请上传参考音频"
        dir=os.path.join(current_path,"SAVAdata","presets",name)
        os.makedirs(dir,exist_ok=True)
        aux_ref_audio_path=[i.name for i in ara] if ara is not None else []
        idx=1
        aux_list=[]
        for i in aux_ref_audio_path:
            try:
                shutil.copy(i,os.path.join(dir,f"aux_{idx}.wav"))                
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
        return "预设保存成功"
    except Exception as e:
        gr.Warning(f"出错：{e}")
        return f"出错：{e}"

def load_preset(name,port):
    try:
        global current_sovits_model
        global current_gpt_model
        switch=True
        if name=='None'or not os.path.exists(os.path.join(current_path,"SAVAdata","presets",name)):
            return gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update()
        data=json.load(open(os.path.join(current_path,"SAVAdata","presets",name,"info.json"), encoding="utf-8"))
        if "auxiliary_audios" not in list(data.keys()):
            data["auxiliary_audios"] = None
        if data["sovits_path"] !="" and data["gpt_path"] != "":
            if data["sovits_path"]==current_sovits_model and data["gpt_path"]==current_gpt_model:
               switch=False
               time.sleep(0.1)
            else:
               if switch_gsvmodel(sovits_path=data["sovits_path"],gpt_path=data["gpt_path"],port=port)!='模型切换成功':
                   gr.Warning("模型切换失败")
               current_sovits_model=data["sovits_path"]
               current_gpt_model=data["gpt_path"]
        if not os.path.exists(data["reference_audio_path"]) and os.path.exists(os.path.join(current_path,"SAVAdata","presets",name,"reference_audio.wav")):
            data["reference_audio_path"]=os.path.join(current_path,"SAVAdata","presets",name,"reference_audio.wav")
        if data["auxiliary_audios"] is not None:                   
            aux_audio=[os.path.join(current_path,"SAVAdata","presets",name,i) for i in data["auxiliary_audios"] if os.path.exists(os.path.join(current_path,"SAVAdata","presets",name,i))]
            if len(aux_audio)!=len(data["auxiliary_audios"]):
               gr.Warning("辅助参考音频存在丢失！")
            data["auxiliary_audios"]=aux_audio
        return data["sovits_path"],data["gpt_path"],data["description"],data["reference_audio_path"],data["auxiliary_audios"],data["reference_audio_text"],data["reference_audio_lang"],"预设加载成功" if switch else "预设加载成功,无需切换模型,若需要强制切换请手动点击按钮"
    except Exception as e:
        return gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),gr.update(),f"加载失败:{e}"

def switch_gsvmodel(sovits_path,gpt_path,port):
    if sovits_path=="" or gpt_path=="":
        gr.Info("请指定模型路径！")
        return "请指定模型路径！"
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
        #print(data_json)
        port=int(port)
        if GSV.gsv_fallback:
            API_URL=f'http://127.0.0.1:{port}/set_model/'
            response = requests.post(url=API_URL,json=data_json)
            response.raise_for_status()
        else:
            API_URL = f'http://127.0.0.1:{port}/set_gpt_weights?weights_path={data_json["gpt_model_path"]}'
            response = requests.get(url=API_URL)
            response.raise_for_status()
            API_URL = f'http://127.0.0.1:{port}/set_sovits_weights?weights_path={data_json["sovits_model_path"]}'
            response = requests.get(url=API_URL)
            response.raise_for_status()
        logger.info(f"模型已切换：{data_json}")
        return '模型切换成功'
    except Exception as e:
        err=f'GPT-SoVITS切换模型发生错误。报错内容: {e}'
        gr.Warning(err)
        logger.error(err)
        return err

def refresh_presets_list():
    GSV.presets_list=['None']
    try:
        preset_dir=os.path.join(current_path,"SAVAdata","presets")
        if os.path.isdir(preset_dir):
            GSV.presets_list+=[i for i in os.listdir(preset_dir) if os.path.isdir(os.path.join(preset_dir,i))]
        else:
            logger.info("当前没有预设")
    except Exception as e:
        GSV.presets_list = ["None"]
        err=f"刷新预设失败：{e}"
        logger.error(err)
        gr.Warning(err)
    time.sleep(0.1)
    return gr.update(value="None", choices=GSV.presets_list)

def restart():
    gr.Warning("正在重启，如果更改了主题或端口，请关闭当前页面！")
    time.sleep(0.5)
    os.system("cls")
    if not exe:
        os.execl(sys.executable,f'"{sys.executable}"',f'"{os.path.abspath(__file__)}"')
    else:
        run_command(command=f"{sys.executable}",dir=current_path)
        os.system(f"taskkill /PID {os.getpid()} /F")

def remake(*args):
    fp=None
    subtitle_list=args[-1]
    args=args[:-1]
    page=args[0]
    if subtitle_list.proj is None:
        gr.Info("上次生成未成功，请先完成生成流程！")
        return fp,*show_page(page,subtitle_list)
    if int(args[1])==-1:
        gr.Info("Not available !")
        return fp,*show_page(page,subtitle_list)
    page,idx,s_txt=args[:3]
    args=[None,*args]#fill data
    try:
        args,kwargs=Projet_dict[subtitle_list.proj].arg_filter(*args)
    except Exception as e:
        print(e)
        return fp,*show_page(page,subtitle_list)        
    subtitle_list[int(idx)].text=s_txt
    fp=save(args,proj=subtitle_list.proj,text=s_txt,dir=subtitle_list.dir,subid=subtitle_list[int(idx)].index)
    if fp is not None:
        subtitle_list[int(idx)].is_success=True
        gr.Info("重新合成成功！点击重新拼接内容。")
    else:
        subtitle_list[int(idx)].is_success=False
        gr.Warning("重新合成失败！")
    return fp,*show_page(page,subtitle_list),subtitle_list

def recompose(page,subtitle_list):
    if len(subtitle_list)==0:
        gr.Info("上次生成未成功，请先完成生成流程！")
        return None,"上次生成未成功，请先完成生成流程！",*show_page(page,subtitle_list),subtitle_list
    sr,audio=subtitle_list.audio_join(sr=None)
    gr.Info("重新合成完毕！")
    return (sr,audio),"OK",*show_page(page,subtitle_list),subtitle_list

def play_audio(idx,subtitle_list):
    i=int(idx)
    if i==-1 or not subtitle_list[i].is_success:
        gr.Info("Not available !")
        return None
    return os.path.join(subtitle_list.dir,f'{subtitle_list[i].index}.wav')

def load_page(subtitle_list):
    length=len(subtitle_list)
    if length==0:
        gr.Info("上次生成未成功，请先完成生成流程！")
    return gr.update(minimum=1,maximum=length if length>0 else 1,interactive=True,value=1),*show_page(1,subtitle_list)

def show_page(page_start,subtitle_list):
    ret=[]
    length=len(subtitle_list)
    pageend=page_start+config.num_edit_rows
    if pageend>length:
        pageend=length+1
    if subtitle_list.proj is not None:
        if subtitle_list.proj=="bv2":
            btn=[gr.update(visible=True),gr.update(visible=False),gr.update(visible=False),gr.update(visible=False)]
        elif subtitle_list.proj=="gsv":
            btn=[gr.update(visible=False),gr.update(visible=True),gr.update(visible=False),gr.update(visible=False)]
        elif subtitle_list.proj=="mstts":  
            btn=[gr.update(visible=False),gr.update(visible=False),gr.update(visible=True),gr.update(visible=False)]
        else:
            btn=[gr.update(visible=False),gr.update(visible=False),gr.update(visible=False),gr.update(visible=True)]
    else:
        btn=[gr.update(visible=True),gr.update(visible=False),gr.update(visible=False),gr.update(visible=False)]     
    for i in range(page_start-1,pageend-1):
        ret.append(gr.update(value=i,visible=False))
        ret.append(gr.update(value=subtitle_list[i].index,visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].start_time_raw} -> {subtitle_list[i].end_time_raw} | {subtitle_list[i].start_time:.2f} -> {subtitle_list[i].end_time:.2f}",visible=True))
        ret.append(gr.update(value=f"{subtitle_list[i].text}",interactive=True,visible=True))
        ret.append(gr.update(value=subtitle_list.get_state(i),visible=True))
        ret+=btn
    for i in range(config.num_edit_rows-pageend+page_start):
        ret.append(gr.update(value=-1,visible=False))
        ret.append(gr.update(value=-1,visible=True))
        ret.append(gr.update(value="NO INFO",visible=True))
        ret.append(gr.update(value="NO INFO",interactive=False,visible=True))
        ret.append(gr.update(value="NO INFO",visible=True))  
        ret+=btn        
    return ret

if __name__ == "__main__":
    Man=Man()
    os.environ['GRADIO_TEMP_DIR'] = os.path.join(current_path,"SAVAdata","temp","gradio")
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-p", "--server_port",type=int,help="server_port")
    parser.add_argument('-share', dest='share', action="store_true", default=False, help="set share True")
    parser.add_argument('-local', dest='local', action="store_true", default=False, help="access on local network")
    args, unknown = parser.parse_known_args()
    refresh_presets_list()
    CUSTOM.refresh_custom_api_list()
    current_sovits_model=None
    current_gpt_model=None   
    load_cfg()
    if config.clear_tmp:
        cls_cache()                 
    if args.server_port is None:
        server_port=config.server_port
    else:
        server_port=args.server_port
    ms_access_token=None
    ms_refresh()
    with gr.Blocks(title="Srt-AI-Voice-Assistant-WebUI",theme=config.theme) as app:
        STATE=gr.State(value=Subtitles())
        gr.Markdown(value=Man.getInfo("title"))
        with gr.Tabs():            
            with gr.TabItem("API合成"):
                with gr.Row():
                    textbox_intput_text = gr.TextArea(label="文件内容展示", value="",interactive=False)                     
                    with gr.TabItem("Bert-VITS2-HiyoriUI"):
                        BV2_ARGS=BV2.getUI()
                        BV2.spkchoser.change(switch_spk,inputs=[BV2.spkchoser],outputs=[BV2.spkid,BV2.speaker_name])
                    with gr.TabItem("GPT-SoVITS"):
                        GSV_ARGS=GSV.getUI()      
                    with gr.TabItem("微软TTS"):
                        MSTTS_ARGS=MSTTS.getUI()
                        MSTTS.ms_refresh_btn.click(ms_refresh, outputs=[MSTTS.ms_languages])
                        MSTTS.ms_languages.change(display_ms_spk,inputs=[MSTTS.ms_languages],outputs=[MSTTS.ms_speaker])
                        MSTTS.ms_speaker.change(display_style_role,inputs=[MSTTS.ms_languages,MSTTS.ms_speaker],outputs=[MSTTS.ms_style,MSTTS.ms_role])    
                    with gr.TabItem("自定义API"):
                        CUSTOM.getUI()
                    with gr.Column():                  
                        fps=gr.Number(label="Pr项目帧速率,仅适用于Pr导出的csv文件",value=30,visible=True,interactive=True,minimum=1)
                        workers=gr.Number(label="调取合成线程数(高于1时请增加api的workers数量,否则不会提速)",value=2,visible=True,interactive=True,minimum=1)
                        offset=gr.Slider(minimum=-6, maximum=6, value=0, step=0.1, label="语音时间偏移(秒) 延后或提前所有语音的时间")
                        input_file = gr.File(label="上传文件",file_types=['.csv','.srt','.txt'],file_count='single')
                        gen_textbox_output_text=gr.Textbox(label="输出信息", placeholder="点击处理按钮",interactive=False)
                        audio_output = gr.Audio(label="Output Audio")
                        with gr.Accordion("启动服务"):
                            gr.Markdown(value="请先在设置中应用项目路径")
                            start_hiyoriui_btn=gr.Button(value="启动HiyoriUI")
                            start_gsv_btn=gr.Button(value="启动GPT-SoVITS")
                        input_file.change(file_show,inputs=[input_file],outputs=[textbox_intput_text])

                with gr.Accordion(label="重新抽卡区域 *Note:完成字幕生成后，即可在本页面对每个字幕重新抽卡。合成参数取决于以上面板参数。请勿在使用本功能时清除缓存。",open=False):
                    with gr.Column():
                        edit_rows=[]
                        with gr.Row():
                            pageloadbtn=gr.Button(value="加载/刷新字幕内容")
                            page_slider=gr.Slider(minimum=1,maximum=1,value=1,label="",step=config.num_edit_rows)
                            audio_player=gr.Audio(label="",value=None,interactive=False,autoplay=True)
                            recompose_btn=gr.Button(value="重新拼接内容")
                            export_btn = gr.Button(value="导出字幕")
                        for x in range(config.num_edit_rows):
                            _=gr.Number(show_label=False,visible=False,value=-1)
                            with gr.Row():
                                edit_rows.append(_)  #real index                             
                                edit_rows.append(gr.Number(scale=0,show_label=False,interactive=False,value=-1,min_width=80))#index(raw)
                                edit_rows.append(gr.Textbox(scale=3,show_label=False,interactive=False,value="NO INFO",max_lines=1))#start time and end time
                                s_txt=gr.Textbox(scale=5,show_label=False,interactive=False,value="NO INFO",max_lines=1)#content
                                edit_rows.append(s_txt)
                                edit_rows.append(gr.Textbox(value="NO INFO",label="状态",show_label=False,interactive=False,scale=1,max_lines=1))#is success or delayed?
                                with gr.Row():
                                    __=gr.Button(value="▶️",scale=1,min_width=60)  
                                    __.click(play_audio,inputs=[_,STATE],outputs=[audio_player])
                                    bv2regenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)  
                                    edit_rows.append(bv2regenbtn)
                                    bv2regenbtn.click(remake,inputs=[page_slider,_,s_txt,*BV2_ARGS,STATE],outputs=[audio_player,*edit_rows,STATE])
                                    gsvregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=True)
                                    edit_rows.append(gsvregenbtn)  
                                    gsvregenbtn.click(remake,inputs=[page_slider,_,s_txt,*GSV_ARGS,STATE],outputs=[audio_player,*edit_rows,STATE])
                                    msttsregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)
                                    edit_rows.append(msttsregenbtn)
                                    msttsregenbtn.click(remake,inputs=[page_slider,_,s_txt,*MSTTS_ARGS,STATE],outputs=[audio_player,*edit_rows,STATE])  
                                    customregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)
                                    edit_rows.append(customregenbtn)      
                                    customregenbtn.click(remake,inputs=[page_slider,_,s_txt,CUSTOM.choose_custom_api,STATE],outputs=[audio_player,*edit_rows,STATE])                         
                        page_slider.change(show_page,inputs=[page_slider,STATE],outputs=edit_rows)       
                        pageloadbtn.click(load_page,inputs=[STATE],outputs=[page_slider,*edit_rows])
                        recompose_btn.click(recompose,inputs=[page_slider,STATE],outputs=[audio_output,gen_textbox_output_text,*edit_rows,STATE])
                        export_btn.click(lambda x:x.export(),inputs=[STATE])
            with gr.TabItem("额外内容"):
                available=False
                from Sava_Utils.extern_extensions.wav2srt import WAV2SRT
                WAV2SRT=WAV2SRT(config=config)
                available=WAV2SRT.UI()
                if not available:
                    gr.Markdown("没有任何扩展，安装后重启生效<br>[获取额外内容](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/tree/main/tools)")
            with gr.TabItem("设置"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("点击应用后，这些设置才会生效。")
                        server_port_set=gr.Number(label="本程序所使用的默认端口，重启生效。5001=自动。当冲突无法启动时，使用参数-p来指定启动端口",value=config.server_port,minimum=5001)
                        clear_cache=gr.Checkbox(label="每次启动时清除缓存",value=config.clear_tmp,interactive=True)
                        min_interval=gr.Slider(label="语音最小间隔(秒)",minimum=0,maximum=3,value=config.min_interval,step=0.1)
                        num_edit_rows=gr.Number(label="重新抽卡页面同时展示的字幕数",minimum=1,maximum=20,value=config.num_edit_rows)                        
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
                        with gr.Group(): 
                            gr.Markdown(value="微软TTS")
                            ms_region=gr.Textbox(label="服务区域",interactive=True,value=config.ms_region)
                            ms_key=gr.Textbox(label="密钥 警告:密钥明文保存，请勿将密钥发送给他人或者分享设置文件！",interactive=True,value=config.ms_key)    
                        save_settings_btn=gr.Button(value="应用并保存当前设置",variant="primary")
                        restart_btn=gr.Button(value="重启UI",variant="stop")
                    with gr.Column():
                        with gr.TabItem("简介和常见错误"):
                            gr.Markdown(value=Man.getInfo("readme"))
                            gr.Markdown(value=Man.getInfo("issues"))
                        with gr.TabItem("帮助"):
                            gr.Markdown(value=Man.getInfo("help"))       

        BV2.gen_btn1.click(generate_bv2,inputs=[input_file,fps,offset,workers,*BV2_ARGS],outputs=[audio_output,gen_textbox_output_text,page_slider,*edit_rows,STATE])
        GSV.gen_btn2.click(generate_gsv,inputs=[input_file,fps,offset,workers,*GSV_ARGS],outputs=[audio_output,gen_textbox_output_text,page_slider,*edit_rows,STATE])
        GSV.save_presets_btn.click(save_preset,inputs=[GSV.choose_presets,GSV.desc_presets,GSV.refer_audio,GSV.aux_ref_audio,GSV.refer_text,GSV.refer_lang,GSV.sovits_path,GSV.gpt_path],outputs=[gen_textbox_output_text])
        GSV.choose_presets.change(load_preset,inputs=[GSV.choose_presets,GSV.api_port2],outputs=[GSV.sovits_path,GSV.gpt_path,GSV.desc_presets,GSV.refer_audio,GSV.aux_ref_audio,GSV.refer_text,GSV.refer_lang,gen_textbox_output_text])
        GSV.refresh_presets_btn.click(refresh_presets_list, outputs=[GSV.choose_presets])
        GSV.switch_gsvmodel_btn.click(switch_gsvmodel,inputs=[GSV.sovits_path,GSV.gpt_path,GSV.api_port2],outputs=[gen_textbox_output_text])  
        MSTTS.gen_btn3.click(generate_mstts,inputs=[input_file,fps,offset,workers,*MSTTS_ARGS],outputs=[audio_output,gen_textbox_output_text,page_slider,*edit_rows,STATE])
        CUSTOM.gen_btn4.click(generate_custom,inputs=[input_file,fps,offset,workers,CUSTOM.choose_custom_api],outputs=[audio_output,gen_textbox_output_text,page_slider,*edit_rows,STATE])
        cls_cache_btn.click(cls_cache,inputs=[],outputs=[])
        start_hiyoriui_btn.click(start_hiyoriui,outputs=[gen_textbox_output_text])
        start_gsv_btn.click(start_gsv,outputs=[gen_textbox_output_text])

        save_settings_btn.click(save_settngs,inputs=[server_port_set,clear_cache,min_interval,num_edit_rows,theme,bv2_pydir_input,bv2_dir_input,gsv_pydir_input,gsv_dir_input,bv2_args,gsv_args,ms_region,ms_key],outputs=[server_port_set,clear_cache,theme,bv2_pydir_input,bv2_dir_input,gsv_pydir_input,gsv_dir_input,bv2_args,gsv_args,ms_region,ms_key])
        restart_btn.click(restart,[],[])

    app.queue().launch(
            share=args.share,
            server_port=server_port if server_port>5001 else None,
            inbrowser=True,
            server_name='0.0.0.0' if args.local else '127.0.0.1'
            )
