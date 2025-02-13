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
from Sava_Utils.edit_panel import *
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
componments=[BV2,GSV,MSTTS,CUSTOM]


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

def generate(*args,proj="",in_file="",sr=None,fps=30,offset=0,max_workers=1):
        #global subtitle_list
        t1 = time.time()
        sr,fps=positive_int(sr,fps)
        if in_file is None:
            gr.Info("请上传字幕文件！")
            return None,"请上传字幕文件！",getworklist(),*load_page(Subtitles()),Subtitles()
        if in_file.name[-4:].lower()==".csv":
            subtitle_list=read_prcsv(in_file.name,fps,offset)
        elif in_file.name[-4:].lower()==".srt":
            subtitle_list=read_srt(in_file.name,offset)
        elif in_file.name[-4:].lower()==".txt":
            subtitle_list=read_txt(in_file.name)
        else:
            gr.Warning("未知的格式，请确保扩展名正确！")
            return None,"未知的格式，请确保扩展名正确！",getworklist(),*load_page(Subtitles()),Subtitles()
        t=datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dirname=os.path.join(current_path,"SAVAdata","temp","work",os.path.basename(in_file.name).replace('.',"-"))
        while os.path.exists(dirname):
            if Sava_Utils.config.overwrite_workspace:
                shutil.rmtree(dirname)
                break
            dirname+="(new)"
        #subtitle_list.sort()
        subtitle_list.set_dir(dirname)
        subtitle_list.set_proj(proj)
        Projet_dict[proj].before_gen_action(*args,config=Sava_Utils.config)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            file_list = list(executor.map(lambda x: save(x[0], **x[1]),[(args, {'proj': proj, 'text': i.text, 'dir': dirname, 'subid': i.index}) for i in subtitle_list]))
        file_list=[i for i in file_list if i is not None]    
        if len(file_list)==0:
            shutil.rmtree(subtitle_list.dir)
            raise gr.Error("所有的字幕合成都出错了，请检查API服务！")
        sr,audio = subtitle_list.audio_join(sr=sr)
        os.makedirs(os.path.join(current_path,"SAVAdata","output"),exist_ok=True)
        sf.write(os.path.join(current_path,"SAVAdata","output",f"{t}.wav"), audio, sr)
        t2 = time.time()
        m, s = divmod(t2-t1, 60)
        use_time="%02d:%02d"%(m, s)        
        if len(file_list)!=len(subtitle_list):
            return (sr,audio),f'完成,但某些字幕的合成出现了错误,请查看控制台的提示信息。所用时间:{use_time}',getworklist(),*load_page(subtitle_list),subtitle_list
        return (sr,audio),f'完成！所用时间:{use_time}',getworklist(),*load_page(subtitle_list),subtitle_list

def generate_bv2(*args):
        args,kwargs=BV2.arg_filter(*args)
        return generate(*args,**kwargs)    

def generate_gsv(*args): 
    try:
        args, kwargs = GSV.arg_filter(*args)
    except Exception as e:
        return None, str(e), getworklist(), *load_page(Subtitles()), Subtitles()
    return generate(*args, **kwargs)

def generate_mstts(*args):
    try:
        args,kwargs=MSTTS.arg_filter(*args)
    except Exception as e:
        return None, str(e), getworklist(), *load_page(Subtitles()), Subtitles()
    return generate(*args,**kwargs)

def generate_custom(*args):
    try:
        args,kwargs=CUSTOM.arg_filter(*args)
    except Exception as e:
        return None, str(e), getworklist(), *load_page(Subtitles()), Subtitles()
    return generate(args,**kwargs)


def gen_multispeaker(subtitles,max_workers):
    for key in list(subtitles.speakers.keys()):
        if subtitles.speakers[key]<=0:
            subtitles.speakers.pop(key)
    for key in subtitles.speakers.keys():
        with open(os.path.join(current_path, "SAVAdata", "speakers",key), 'rb') as f:
            info = pickle.load(f)
            args=info["raw_data"]
            project=info["project"]
            if project=='gsv':
                GSV.switch_gsvmodel(gpt_path=args[-2],sovits_path=args[-1],port=args[6])
            args, kwargs = Projet_dict[project].arg_filter(*args)
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(max_workers)) as executor:
            if len(list(
                executor.map(
                    lambda x: save(x[0], **x[1]),
                    [
                        (
                            args,
                            {
                                "proj": project,
                                "text": i.text,
                                "dir": subtitles.dir,
                                "subid": i.index,
                            },
                        )
                        for i in subtitles
                        if i.speaker == key
                    ],
                )
            )
            )==0:
                raise gr.Error("单一说话人的全部语音合成失败了！")
    audio=subtitles.audio_join()
    gr.Info("合成完毕！")
    return audio,*load_page(subtitles),subtitles


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
        logger.info("成功清除临时文件！")
        gr.Info("成功清除临时文件！")
    else:
        logger.info("目前没有临时文件！")
        gr.Info("目前没有临时文件！")

def save_settngs(server_port,overwrite_workspace,clear_tmp,min_interval,num_edit_rows,theme,bv2_pydir,bv2_dir,gsv_pydir,gsv_dir,bv2_args,gsv_args,ms_region,ms_key):
    global componments
    current_edit_rows=Sava_Utils.config.num_edit_rows
    Sava_Utils.config=Settings(server_port=server_port,theme=theme,overwrite_workspace=overwrite_workspace,clear_tmp=clear_tmp,min_interval=min_interval,num_edit_rows=num_edit_rows,bv2_pydir=bv2_pydir.strip('"'),bv2_dir=bv2_dir.strip('"'),gsv_pydir=gsv_pydir.strip('"'),gsv_dir=gsv_dir.strip('"'),bv2_args=bv2_args,gsv_args=gsv_args,ms_region=ms_region,ms_key=ms_key)
    Sava_Utils.config.save()
    for i in componments:
        i.update_cfg(config=Sava_Utils.config)
    if Sava_Utils.config.num_edit_rows != current_edit_rows:
        Sava_Utils.config.num_edit_rows = current_edit_rows
        logger.info("更改字幕栏数需要重启生效")
        gr.Info("更改字幕栏数需要重启生效")
    logger.info("成功保存设置！")
    gr.Info("成功保存设置！")
    return (
        Sava_Utils.config.server_port,
        Sava_Utils.config.overwrite_workspace,
        Sava_Utils.config.clear_tmp,
        Sava_Utils.config.theme,
        Sava_Utils.config.bv2_pydir,
        Sava_Utils.config.bv2_dir,
        Sava_Utils.config.gsv_pydir,
        Sava_Utils.config.gsv_dir,
        Sava_Utils.config.bv2_args,
        Sava_Utils.config.gsv_args,
        Sava_Utils.config.ms_region,
        Sava_Utils.config.ms_key,
    )

def start_hiyoriui():
    if Sava_Utils.config.bv2_pydir == "":
        gr.Warning("请前往设置页面指定环境路径并保存!")
        return "请前往设置页面指定环境路径并保存!"    
    command = f'"{Sava_Utils.config.bv2_pydir}" "{os.path.join(Sava_Utils.config.bv2_dir,"hiyoriUI.py")}" {Sava_Utils.config.bv2_args}'
    run_command(command=command, dir=Sava_Utils.config.bv2_dir)
    time.sleep(0.1)
    return "HiyoriUI已启动，请确保其配置文件无误"

def start_gsv():
    if Sava_Utils.config.gsv_pydir == "":
        gr.Warning("请前往设置页面指定环境路径并保存!")
        return "请前往设置页面指定环境路径并保存!"
    if os.path.exists(os.path.join(Sava_Utils.config.gsv_dir, "api_v2.py")):
        apath="api_v2.py"
        GSV.gsv_fallback=False
    else:
        apath="api.py"
        GSV.gsv_fallback=True
        assert os.path.exists(
            os.path.join(Sava_Utils.config.gsv_dir, "api.py")
        ), "api文件丢失？？？"
        gr.Warning("api_v2不存在，降级至v1。可能导致兼容问题并且部分功能无法使用。")
        logger.warning("api_v2不存在，降级至v1。可能导致兼容问题并且部分功能无法使用。")

    command = f'"{Sava_Utils.config.gsv_pydir}" "{os.path.join(Sava_Utils.config.gsv_dir,apath)}" {Sava_Utils.config.gsv_args}'
    run_command(command=command, dir=Sava_Utils.config.gsv_dir)
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

def restart():
    gr.Warning("正在重启，如果更改了主题或端口，请关闭当前页面！")
    time.sleep(0.5)
    os.system("cls")
    if not exe:
        os.execl(sys.executable,f'"{sys.executable}"',f'"{os.path.abspath(__file__)}"')
    else:
        try:
            a = os.environ["_PYI_APPLICATION_HOME_DIR"]
            b = os.environ["_PYI_ARCHIVE_FILE"]
            c = os.environ["_PYI_PARENT_PROCESS_LEVEL"]
            os.unsetenv("_PYI_APPLICATION_HOME_DIR")
            os.unsetenv("_PYI_ARCHIVE_FILE")
            os.unsetenv("_PYI_PARENT_PROCESS_LEVEL")
            run_command(command=f"{sys.executable}", dir=current_path)        
            os.environ["_PYI_APPLICATION_HOME_DIR"]=a
            os.environ["_PYI_ARCHIVE_FILE"] = b
            os.environ["_PYI_PARENT_PROCESS_LEVEL"] = c
        except Exception as e:
            gr.Warning(f"出现错误{str(e)}，请手动重启！")
        os.system(f"taskkill /PID {os.getpid()} /F")

def remake(*args):
    fp=None
    subtitle_list=args[-1]
    args=args[:-1]
    page=args[0]    
    if int(args[1])==-1:
        gr.Info("Not available !")
        return fp,*show_page(page,subtitle_list)
    page,idx,s_txt=args[:3]
    if subtitle_list[int(idx)].speaker is not None:
        with open(os.path.join(current_path, "SAVAdata", "speakers",subtitle_list[int(idx)].speaker), 'rb') as f:
            info = pickle.load(f)
            args=info["raw_data"]
            proj=info["project"]
        if proj=='gsv':
            GSV.switch_gsvmodel(gpt_path=args[-2],sovits_path=args[-1],port=args[6])
        args, kwargs = Projet_dict[proj].arg_filter(*args)
    else:
        if subtitle_list.proj is None:
            gr.Info("使用多角色合成时，必须指定说话人！")
            return fp,*show_page(page,subtitle_list)
        args=[None,*args]#fill data
        try:
            proj=subtitle_list.proj
            args,kwargs=Projet_dict[proj].arg_filter(*args)
        except Exception as e:
            # print(e)
            return fp,*show_page(page,subtitle_list)        
    subtitle_list[int(idx)].text=s_txt
    fp=save(args,proj=proj,text=s_txt,dir=subtitle_list.dir,subid=subtitle_list[int(idx)].index)
    if fp is not None:
        subtitle_list[int(idx)].is_success=True
        gr.Info("重新合成成功！点击重新拼接内容。")
    else:
        subtitle_list[int(idx)].is_success=False
        gr.Warning("重新合成失败！")
    return fp,*show_page(page,subtitle_list),subtitle_list

def recompose(page,subtitle_list):
    if subtitle_list is None or len(subtitle_list)==0:
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

def save_spk(name, *args):
    project = "gsv"
    args=[None, None, None, None, *args]
    # catch all arguments
    # process raw data before generating
    try:
        GSV.arg_filter(*args)
        os.makedirs(os.path.join(current_path, "SAVAdata", "speakers"), exist_ok=True)
        with open(os.path.join(current_path, "SAVAdata", "speakers", name), "wb") as f:
            pickle.dump({"project": project, "raw_data":args},f)
        gr.Info(f"保存成功：{name}")
    except Exception as e:
        gr.Warning(str(e))
    return getspklist()

if __name__ == "__main__":
    Man=Man()
    os.environ['GRADIO_TEMP_DIR'] = os.path.join(current_path,"SAVAdata","temp","gradio")
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-p", "--server_port",type=int,help="server_port")
    parser.add_argument('-share', dest='share', action="store_true", default=False, help="set share True")
    parser.add_argument('-local', dest='local', action="store_true", default=False, help="access on local network")
    args, unknown = parser.parse_known_args()
    GSV.refresh_presets_list()
    CUSTOM.refresh_custom_api_list()
    if Sava_Utils.config.clear_tmp:
        cls_cache()
    if args.server_port is None:
        server_port = Sava_Utils.config.server_port
    else:
        server_port=args.server_port
    MSTTS.update_cfg(config=Sava_Utils.config)
    MSTTS.ms_refresh()
    with gr.Blocks(title="Srt-AI-Voice-Assistant-WebUI",theme=Sava_Utils.config.theme) as app:
        STATE=gr.State(value=Subtitles())
        gr.Markdown(value=Man.getInfo("title"))
        with gr.Tabs():            
            with gr.TabItem("API合成"):
                with gr.Row():
                    with gr.Column():
                        textbox_intput_text = gr.TextArea(label="文件内容展示", value="",interactive=False)
                        gen_multispeaker_btn = gr.Button(value="生成多角色项目")
                    with gr.Column():
                        with gr.TabItem("Bert-VITS2-HiyoriUI"):
                            BV2_ARGS=BV2.getUI()
                            BV2.spkchoser.change(switch_spk,inputs=[BV2.spkchoser],outputs=[BV2.spkid,BV2.speaker_name])
                        with gr.TabItem("GPT-SoVITS"):
                            GSV_ARGS=GSV.getUI()      
                        with gr.TabItem("微软TTS"):
                            MSTTS_ARGS=MSTTS.getUI()  
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

                with gr.Accordion(label="重新抽卡区域 *Note:完成字幕生成后，即可在本页面对每个字幕重新抽卡。合成参数取决于以上面板参数。请勿在使用本功能时清除临时文件。",open=False):
                    with gr.Column():
                        edit_rows=[]
                        edit_real_index_list=[]
                        edit_check_list=[]
                        with gr.Row():
                            worklist=gr.Dropdown(choices=os.listdir(os.path.join(current_path,"SAVAdata","temp","work")) if os.path.exists(os.path.join(current_path,"SAVAdata","temp","work")) else [""],label="合成历史", scale=1)
                            workrefbtn = gr.Button(value="🔄️", scale=1, min_width=60)
                            workloadbtn = gr.Button(value="加载", scale=1, min_width=60)
                            page_slider=gr.Slider(minimum=1,maximum=1,value=1,label="",step=Sava_Utils.config.num_edit_rows,scale=3)
                            audio_player=gr.Audio(label="",value=None,interactive=False,autoplay=True,scale=3)
                            recompose_btn = gr.Button(value="重新拼接内容", scale=3)
                            export_btn = gr.Button(value="导出字幕", scale=3)
                        for x in range(Sava_Utils.config.num_edit_rows):
                            edit_real_index=gr.Number(show_label=False,visible=False,value=-1,interactive=False)#real index                         
                            with gr.Row():
                                edit_check=gr.Checkbox(value=False,interactive=True,min_width=40,label="",scale=0)
                                edit_check_list.append(edit_check)
                                edit_rows.append(edit_real_index)  # real index
                                edit_real_index_list.append(edit_real_index)
                                edit_rows.append(gr.Number(scale=1,show_label=False,interactive=False,value=-1,min_width=40))#index(raw)
                                edit_rows.append(gr.Textbox(scale=4,show_label=False,interactive=False,value="NO INFO",max_lines=1))#start time and end time
                                s_txt=gr.Textbox(scale=6,show_label=False,interactive=False,value="NO INFO",max_lines=1)#content
                                edit_rows.append(s_txt)
                                edit_rows.append(gr.Textbox(scale=1,show_label=False,interactive=False,min_width=60,value="None",max_lines=1))#speaker
                                edit_rows.append(gr.Textbox(value="NO INFO",show_label=False,interactive=False,min_width=70,scale=1,max_lines=1))#is success or delayed?
                                with gr.Row():
                                    __=gr.Button(value="▶️",scale=1,min_width=60)  
                                    __.click(play_audio,inputs=[edit_real_index,STATE],outputs=[audio_player])
                                    bv2regenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)  
                                    edit_rows.append(bv2regenbtn)
                                    bv2regenbtn.click(remake,inputs=[page_slider,edit_real_index,s_txt,*BV2_ARGS,STATE],outputs=[audio_player,*edit_rows,STATE])
                                    gsvregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=True)
                                    edit_rows.append(gsvregenbtn)  
                                    gsvregenbtn.click(remake,inputs=[page_slider,edit_real_index,s_txt,*GSV_ARGS,STATE],outputs=[audio_player,*edit_rows,STATE])
                                    msttsregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)
                                    edit_rows.append(msttsregenbtn)
                                    msttsregenbtn.click(remake,inputs=[page_slider,edit_real_index,s_txt,*MSTTS_ARGS,STATE],outputs=[audio_player,*edit_rows,STATE])  
                                    customregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)
                                    edit_rows.append(customregenbtn)      
                                    customregenbtn.click(remake,inputs=[page_slider,edit_real_index,s_txt,CUSTOM.choose_custom_api,STATE],outputs=[audio_player,*edit_rows,STATE])                         
                        page_slider.change(show_page,inputs=[page_slider,STATE],outputs=edit_rows)       
                        workloadbtn.click(load_work,inputs=[worklist],outputs=[STATE,page_slider,*edit_rows])
                        workrefbtn.click(getworklist,inputs=[],outputs=[worklist])
                        recompose_btn.click(recompose,inputs=[page_slider,STATE],outputs=[audio_output,gen_textbox_output_text,*edit_rows,STATE])
                        export_btn.click(lambda x:x.export(),inputs=[STATE])
                        with gr.Row():
                            all_selection_btn = gr.Button(value="全选",interactive=True)
                            all_selection_btn.click(lambda :[True for i in range(Sava_Utils.config.num_edit_rows)],inputs=[],outputs=edit_check_list)
                            reverse_selection_btn = gr.Button(value="反选",interactive=True)
                            reverse_selection_btn.click(lambda *args:[not i for i in args],inputs=edit_check_list,outputs=edit_check_list)
                            clear_selection_btn=gr.Button(value="清除选择",interactive=True)
                            clear_selection_btn.click(lambda :[False for i in range(Sava_Utils.config.num_edit_rows)],inputs=[],outputs=edit_check_list)
                        with gr.Accordion(label="多角色配音"):
                            with gr.Row():
                                speaker_list=gr.Dropdown(label="",value="test",choices=["test"],allow_custom_value=True)
                                refresh_spk_list_btn=gr.Button(value="🔄️",scale=1,min_width=60)
                                refresh_spk_list_btn.click(getspklist,inputs=[],outputs=[speaker_list])
                                apply_btn = gr.Button(value="✅", scale=1, min_width=60)
                                apply_btn.click(apply_spk,inputs=[speaker_list,page_slider,STATE,*edit_check_list,*edit_real_index_list],outputs=[*edit_check_list,*edit_rows,STATE])
                                select_spk_projet_btn=gr.Dropdown(choices=['bv2','gsv','mstts','custom'],value='gsv',interactive=False,label="选择说话人所属项目（暂不可用）")
                                save_spk_btn=gr.Button(value="💾", scale=1, min_width=60)
                                save_spk_btn.click(save_spk,inputs=[speaker_list,*GSV_ARGS],outputs=[speaker_list])
                                del_spk_list_btn=gr.Button(value="🗑️", scale=1, min_width=60)
                                del_spk_list_btn.click(del_spk,inputs=[speaker_list],outputs=[speaker_list])
                                start_gen_multispeaker_btn=gr.Button(value="开始生成多角色配音!",variant="primary")
                                start_gen_multispeaker_btn.click(gen_multispeaker,inputs=[STATE,workers],outputs=[audio_output,page_slider,*edit_rows,STATE])

            with gr.TabItem("额外内容"):
                available=False
                from Sava_Utils.extern_extensions.wav2srt import WAV2SRT
                WAV2SRT = WAV2SRT(config=Sava_Utils.config)
                componments.append(WAV2SRT)
                available=WAV2SRT.UI()
                if not available:
                    gr.Markdown("没有任何扩展，安装后重启生效<br>[获取额外内容](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/tree/main/tools)")
            with gr.TabItem("设置"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("⚠️点击应用后，这些设置才会生效。⚠️")
                        with gr.Group():
                            gr.Markdown(value="通用设置")
                            server_port_set=gr.Number(label="本程序所使用的默认端口，重启生效。5001=自动。当冲突无法启动时，使用参数-p来指定启动端口",value=Sava_Utils.config.server_port,minimum=5001)
                            overwrite_workspace=gr.Checkbox(label="覆盖历史记录而不是新建工程",value=Sava_Utils.config.overwrite_workspace,interactive=True)
                            clear_cache=gr.Checkbox(label="每次启动时清除临时文件（会一并清除合成历史）",value=Sava_Utils.config.clear_tmp,interactive=True)
                            min_interval=gr.Slider(label="语音最小间隔(秒)",minimum=0,maximum=3,value=Sava_Utils.config.min_interval,step=0.1)
                            num_edit_rows=gr.Number(label="重新抽卡页面同时展示的字幕数",minimum=1,maximum=20,value=Sava_Utils.config.num_edit_rows)                        
                            theme = gr.Dropdown(choices=gradio_hf_hub_themes, value=Sava_Utils.config.theme, label="选择主题，重启后生效，部分主题可能需要科学上网",interactive=True)
                            cls_cache_btn=gr.Button(value="立即清除临时文件",variant="primary")
                        with gr.Group():
                            gr.Markdown(value="BV2")
                            bv2_pydir_input=gr.Textbox(label="设置BV2环境路径",interactive=True,value=Sava_Utils.config.bv2_pydir)
                            bv2_dir_input=gr.Textbox(label="设置BV2项目路径,使用整合包可不填",interactive=True,value=Sava_Utils.config.bv2_dir)
                            bv2_args=gr.Textbox(label="设置BV2启动参数",interactive=True,value=Sava_Utils.config.bv2_args)
                        with gr.Group():
                            gr.Markdown(value="GSV")
                            gsv_pydir_input=gr.Textbox(label="设置GSV环境路径",interactive=True,value=Sava_Utils.config.gsv_pydir)
                            gsv_dir_input=gr.Textbox(label="设置GSV项目路径,使用整合包可不填",interactive=True,value=Sava_Utils.config.gsv_dir)
                            gsv_args=gr.Textbox(label="设置GSV-API启动参数",interactive=True,value=Sava_Utils.config.gsv_args)
                        with gr.Group(): 
                            gr.Markdown(value="微软TTS")
                            ms_region=gr.Textbox(label="服务区域",interactive=True,value=Sava_Utils.config.ms_region)
                            ms_key=gr.Textbox(label="密钥 警告:密钥明文保存，请勿将密钥发送给他人或者分享设置文件！",interactive=True,value=Sava_Utils.config.ms_key)    
                        save_settings_btn=gr.Button(value="应用并保存当前设置",variant="primary")
                        restart_btn=gr.Button(value="重启UI",variant="stop")
                    with gr.Column():
                        with gr.TabItem("简介和常见错误"):
                            gr.Markdown(value=Man.getInfo("readme"))
                            gr.Markdown(value=Man.getInfo("issues"))
                        with gr.TabItem("帮助"):
                            gr.Markdown(value=Man.getInfo("help"))       
        gen_multispeaker_btn.click(create_multi_speaker,inputs=[input_file,fps,offset],outputs=[worklist,page_slider,*edit_rows,STATE])
        BV2.gen_btn1.click(generate_bv2,inputs=[input_file,fps,offset,workers,*BV2_ARGS],outputs=[audio_output,gen_textbox_output_text,worklist,page_slider,*edit_rows,STATE])
        GSV.gen_btn2.click(generate_gsv,inputs=[input_file,fps,offset,workers,*GSV_ARGS],outputs=[audio_output,gen_textbox_output_text,worklist,page_slider,*edit_rows,STATE])
        GSV.save_presets_btn.click(save_preset,inputs=[GSV.choose_presets,GSV.desc_presets,GSV.refer_audio,GSV.aux_ref_audio,GSV.refer_text,GSV.refer_lang,GSV.sovits_path,GSV.gpt_path],outputs=[gen_textbox_output_text])
        GSV.switch_gsvmodel_btn.click(GSV.switch_gsvmodel,inputs=[GSV.sovits_path,GSV.gpt_path,GSV.api_port2],outputs=[gen_textbox_output_text]) 
        GSV.choose_presets.change(GSV.load_preset,inputs=[GSV.choose_presets,GSV.api_port2],outputs=[GSV.sovits_path,GSV.gpt_path,GSV.desc_presets,GSV.refer_audio,GSV.aux_ref_audio,GSV.refer_text,GSV.refer_lang,gen_textbox_output_text])
        MSTTS.gen_btn3.click(generate_mstts,inputs=[input_file,fps,offset,workers,*MSTTS_ARGS],outputs=[audio_output,gen_textbox_output_text,worklist,page_slider,*edit_rows,STATE])
        CUSTOM.gen_btn4.click(generate_custom,inputs=[input_file,fps,offset,workers,CUSTOM.choose_custom_api],outputs=[audio_output,gen_textbox_output_text,worklist,page_slider,*edit_rows,STATE])
        cls_cache_btn.click(cls_cache,inputs=[],outputs=[])
        start_hiyoriui_btn.click(start_hiyoriui,outputs=[gen_textbox_output_text])
        start_gsv_btn.click(start_gsv,outputs=[gen_textbox_output_text])

        save_settings_btn.click(save_settngs,inputs=[server_port_set,overwrite_workspace,clear_cache,min_interval,num_edit_rows,theme,bv2_pydir_input,bv2_dir_input,gsv_pydir_input,gsv_dir_input,bv2_args,gsv_args,ms_region,ms_key],outputs=[server_port_set,overwrite_workspace,clear_cache,theme,bv2_pydir_input,bv2_dir_input,gsv_pydir_input,gsv_dir_input,bv2_args,gsv_args,ms_region,ms_key])
        restart_btn.click(restart,[],[])

    app.queue().launch(
            share=args.share,
            server_port=server_port if server_port>5001 else None,
            inbrowser=True,
            server_name='0.0.0.0' if args.local else '127.0.0.1'
            )
