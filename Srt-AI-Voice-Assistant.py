import os
import sys
# import inspect

if getattr(sys, "frozen", False):
    current_path = os.path.dirname(sys.executable)
    os.environ["exe"] = 'True'
elif __file__:
    current_path = os.path.dirname(__file__)
    os.environ["exe"] = 'False'
os.environ["current_path"] = current_path

import shutil

import gradio as gr

import json
#import datetime
import time
import soundfile as sf
import concurrent.futures
from tqdm import tqdm

import Sava_Utils
from Sava_Utils.man.manual import Man
from Sava_Utils.utils import *
from Sava_Utils.edit_panel import *
from Sava_Utils import logger
from Sava_Utils import args
from Sava_Utils.subtitle import Base_subtitle,Subtitle,Subtitles

import Sava_Utils.tts_projects
import Sava_Utils.tts_projects.bv2
import Sava_Utils.tts_projects.gsv
import Sava_Utils.tts_projects.mstts
import Sava_Utils.tts_projects.custom
from Sava_Utils.subtitle_translation import Translation_module

BV2 = Sava_Utils.tts_projects.bv2.BV2()
GSV = Sava_Utils.tts_projects.gsv.GSV()
MSTTS = Sava_Utils.tts_projects.mstts.MSTTS()
CUSTOM = Sava_Utils.tts_projects.custom.Custom()
TRANSLATION_MODULE = Translation_module()
Projet_dict={"bv2":BV2,"gsv":GSV,"mstts":MSTTS,"custom":CUSTOM}
componments=[BV2,GSV,MSTTS,CUSTOM]

def custom_api(text):
    raise "需要加载自定义API函数！"

def generate(*args,proj="",in_files=[],fps=30,offset=0,max_workers=1):
    t1 = time.time()
    fps = positive_int(fps)[0]
    if in_files in [None,[]]:
        gr.Info("请上传字幕文件！")
        return (
            None,
            "请上传字幕文件！",
            getworklist(),
            *load_page(Subtitles()),
            Subtitles(),
        )
    os.makedirs(os.path.join(current_path, "SAVAdata", "output"), exist_ok=True)
    for in_file in in_files:
        try:
            subtitle_list = read_file(in_file.name, fps, offset)
        except Exception as e:
            what=str(e)
            gr.Warning(what)
            return (
                None,
                what,
                getworklist(),
                *load_page(Subtitles()),
                Subtitles(),
            )
        # subtitle_list.sort()
        subtitle_list.set_dir_name(os.path.basename(in_file.name).replace(".", "-"))
        subtitle_list.set_proj(proj)
        Projet_dict[proj].before_gen_action(*args, config=Sava_Utils.config,notify=False,force=False)
        abs_dir = subtitle_list.get_abs_dir()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            file_list = list(
                tqdm(
                    executor.map(
                        lambda x: save(x[0], **x[1]),
                        [
                            (
                                args,
                                {
                                    "proj": proj,
                                    "text": i.text,
                                    "dir": abs_dir,
                                    "subid": i.index,
                                },
                            )
                            for i in subtitle_list
                        ],
                    ),
                    total=len(subtitle_list),
                    desc="正在合成单说话人任务"
                )
            )
        file_list = [i for i in file_list if i is not None]
        if len(file_list) == 0:
            shutil.rmtree(abs_dir)
            if len(in_files)==1:
                raise gr.Error("所有的字幕合成都出错了，请检查API服务！")
            else:
                continue
        sr, audio = subtitle_list.audio_join(sr=Sava_Utils.config.output_sr)        
        sf.write(os.path.join(current_path, "SAVAdata", "output", f"{os.path.basename(in_file.name)}.wav"), audio, sr)
    t2 = time.time()
    m, s = divmod(t2 - t1, 60)
    use_time = "%02d:%02d" % (m, s)
    return (
        (sr, audio),
        f"完成！所用时间:{use_time}",
        getworklist(),
        *load_page(subtitle_list),
        subtitle_list,
    )

def generate_preprocess(*args,project=None): 
    try:
        args, kwargs = Projet_dict[project].arg_filter(*args)
    except Exception as e:
        return None, str(e), getworklist(), *load_page(Subtitles()), Subtitles()
    return generate(*args, **kwargs)

def gen_multispeaker(subtitles:Subtitles,max_workers):
    if len(subtitles)==0 or subtitles is None:
        gr.Info("当前没有字幕")
        return None, *load_page(Subtitles())
    for key in list(subtitles.speakers.keys()):
        if subtitles.speakers[key]<=0:
            subtitles.speakers.pop(key)
    if len(list(subtitles.speakers.keys()))==0 and subtitles.default_speaker is None:
        gr.Warning("警告：没有指派任何说话人")
    abs_dir=subtitles.get_abs_dir()
    progress=0
    tasks = {key: [] for key in [*subtitles.speakers.keys(),None]}
    for i in subtitles:
        tasks[i.speaker].append(i)
    for key in tasks.keys():
        if key is None:
            if subtitles.proj is None and subtitles.default_speaker is not None and len(tasks[None])>0:
                print(f"当前使用选定的默认说话人：{subtitles.default_speaker}")
            else:
                continue
        spk = key if key is not None else subtitles.default_speaker
        try:
            with open(os.path.join(current_path, "SAVAdata", "speakers",spk), 'rb') as f:
                info = pickle.load(f) 
        except FileNotFoundError:
            logger.error(f"找不到说话人存档{spk}")
            gr.Warning(f"找不到说话人存档{spk}")
            continue
        args=info["raw_data"]
        project=info["project"]
        args, kwargs = Projet_dict[project].arg_filter(*args)
        Projet_dict[project].before_gen_action(*args,config=Sava_Utils.config)   
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(max_workers)) as executor:
            file_list = list(
                tqdm(
                    executor.map(
                        lambda x: save(x[0], **x[1]),
                        [
                            (
                                args,
                                {
                                    "proj": project,
                                    "text": i.text,
                                    "dir": abs_dir,
                                    "subid": i.index,
                                },
                            )
                            for i in tasks[key]
                        ],
                    ),
                    total=len(subtitles),
                    initial=progress,
                    desc=f"正在合成多说话人任务，当前说话人为 {spk}",
                )
            )
        file_list=[i for i in file_list if i is not None]
        progress+=len(file_list)
        if len(file_list)==0:
            raise gr.Error("单一说话人的全部语音合成失败了！")
    audio=subtitles.audio_join(sr=Sava_Utils.config.output_sr)
    gr.Info("合成完毕！")
    return audio,*load_page(subtitles)


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

def start_hiyoriui():
    if Sava_Utils.config.bv2_pydir == "":
        gr.Warning("请前往设置页面指定环境路径并保存!")
        return "请前往设置页面指定环境路径并保存!"    
    command = f'"{Sava_Utils.config.bv2_pydir}" "{os.path.join(Sava_Utils.config.bv2_dir,"hiyoriUI.py")}" {Sava_Utils.config.bv2_args}'
    rc_open_window(command=command, dir=Sava_Utils.config.bv2_dir)
    time.sleep(0.1)
    return "HiyoriUI已启动，请确保其配置文件无误"

def start_gsv():
    if Sava_Utils.config.gsv_pydir == "":
        gr.Warning("请前往设置页面指定GSV环境路径并保存!")
        return "请前往设置页面指定GSV环境路径并保存!"
    if Sava_Utils.config.gsv_fallback:
        apath="api.py"    
        gr.Info("api降级至v1，功能受限。")
        logger.warning("api降级至v1，功能受限。")
    else:
        apath="api_v2.py"
    if not os.path.exists(os.path.join(Sava_Utils.config.gsv_dir, apath)):
        raise gr.Error("api文件不存在？？？")

    command = f'"{Sava_Utils.config.gsv_pydir}" "{os.path.join(Sava_Utils.config.gsv_dir,apath)}" {Sava_Utils.config.gsv_args}'
    rc_open_window(command=command, dir=Sava_Utils.config.gsv_dir)
    time.sleep(0.1)
    return "GSV-API服务已启动，请确保其配置文件无误"

def remake(*args):
    fp=None
    subtitle_list=args[-1]
    args=args[:-1]
    page=args[0]    
    if int(args[1])==-1:
        gr.Info("Not available !")
        return fp,*show_page(page,subtitle_list)
    page,idx,s_txt=args[:3]
    if subtitle_list[int(idx)].speaker is not None or (subtitle_list.proj is None and subtitle_list.default_speaker is not None):
        spk = subtitle_list[int(idx)].speaker
        if spk is None:
            spk=subtitle_list.default_speaker
        try:
            with open(os.path.join(current_path, "SAVAdata", "speakers",spk), 'rb') as f:
                info = pickle.load(f)
        except FileNotFoundError:
            logger.error(f"找不到说话人存档{spk}")
            gr.Warning(f"找不到说话人存档{spk}")
            return fp, *show_page(page, subtitle_list)
        args=info["raw_data"]
        proj=info["project"]
        args, kwargs = Projet_dict[proj].arg_filter(*args)
        #Projet_dict[proj].before_gen_action(*args,notify=False,force=True)
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
    Projet_dict[proj].before_gen_action(*args,config=Sava_Utils.config,notify=False,force=False)
    subtitle_list[int(idx)].text=s_txt
    fp=save(args,proj=proj,text=s_txt,dir=subtitle_list.get_abs_dir(),subid=subtitle_list[int(idx)].index)
    if fp is not None:
        subtitle_list[int(idx)].is_success=True
        gr.Info("重新合成成功！点击重新拼接内容。")
    else:
        subtitle_list[int(idx)].is_success=False
        gr.Warning("重新合成失败！")
    subtitle_list.dump()
    return fp,*show_page(page,subtitle_list)

def recompose(page,subtitle_list:Subtitles):
    if subtitle_list is None or len(subtitle_list)==0:
        gr.Info("上次生成未成功，请先完成生成流程！")
        return None,"上次生成未成功，请先完成生成流程！",*show_page(page,subtitle_list)
    audio=subtitle_list.audio_join(sr=Sava_Utils.config.output_sr)
    gr.Info("重新合成完毕！")
    return audio,"OK",*show_page(page,subtitle_list)

def save_spk(name,*args,project):
    if Sava_Utils.config.server_mode:
        gr.Warning("当前功能被禁止")
        return gr.update(choices=["None", *os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))])
    if name in ["",[],None,'None']:
        gr.Info("请输入有效的名称！")
        return gr.update(choices=["None", *os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))])
    args=[None, None, None, None,*args]
    # catch all arguments
    # process raw data before generating
    try:
        Projet_dict[project].arg_filter(*args)
        os.makedirs(os.path.join(current_path, "SAVAdata", "speakers"), exist_ok=True)
        with open(os.path.join(current_path, "SAVAdata", "speakers", name), "wb") as f:
            pickle.dump({"project": project, "raw_data":args},f)
        gr.Info(f"保存成功：{name}")
    except Exception as e:
        gr.Warning(str(e))
        return gr.update(choices=["None", *os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))])
    return gr.update(choices=["None", *os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))],value=name)

if __name__ == "__main__":
    Man=Man()
    os.environ['GRADIO_TEMP_DIR'] = os.path.join(current_path,"SAVAdata","temp","gradio")
    GSV.refresh_presets_list()
    CUSTOM.refresh_custom_api_list()
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
            with gr.TabItem("字幕音频合成"):
                with gr.Row():
                    with gr.Column():
                        textbox_intput_text = gr.TextArea(label="文件内容展示", value="",interactive=False)
                        create_multispeaker_btn = gr.Button(value="创建多角色项目")
                    with gr.Column():
                        with gr.TabItem("AR-TTS"):
                            GSV_ARGS=GSV.getUI()                             
                        with gr.TabItem("Bert-VITS2-HiyoriUI"):
                            BV2_ARGS=BV2.getUI() 
                        with gr.TabItem("微软TTS"):
                            MSTTS_ARGS=MSTTS.getUI()  
                        with gr.TabItem("自定义API"):
                            CUSTOM.getUI()
                    with gr.Column():                  
                        fps=gr.Number(label="Pr项目帧速率,仅适用于Pr导出的csv文件",value=30,visible=True,interactive=True,minimum=1)
                        workers=gr.Number(label="调取合成线程数(高于1时请增加api的workers数量,否则不会提速)",value=2,visible=True,interactive=True,minimum=1)
                        offset=gr.Slider(minimum=-6, maximum=6, value=0, step=0.1, label="语音时间偏移(秒) 延后或提前所有语音的时间")
                        input_file = gr.File(label="上传文件(批量只支持单个同一说话人)",file_types=['.csv','.srt','.txt'],type="file",file_count='multiple')
                        gen_textbox_output_text=gr.Textbox(label="输出信息", placeholder="点击处理按钮",interactive=False)
                        audio_output = gr.Audio(label="Output Audio")
                        if not Sava_Utils.config.server_mode:
                            with gr.Accordion("启动服务"):
                                gr.Markdown(value="请先在设置中应用项目路径")
                                start_hiyoriui_btn=gr.Button(value="启动HiyoriUI")
                                start_gsv_btn=gr.Button(value="启动GPT-SoVITS")
                                start_hiyoriui_btn.click(start_hiyoriui,outputs=[gen_textbox_output_text])
                                start_gsv_btn.click(start_gsv,outputs=[gen_textbox_output_text])
                        input_file.change(file_show,inputs=[input_file],outputs=[textbox_intput_text])

                with gr.Accordion(label="编辑区域 *Note:请勿在使用本功能时清除临时文件。",open=True):
                    with gr.Column():
                        edit_rows=[]
                        edit_real_index_list=[]
                        edit_check_list=[]
                        edit_start_end_time_list=[]
                        with gr.Row():
                            worklist=gr.Dropdown(choices=os.listdir(os.path.join(current_path,"SAVAdata","temp","work")) if os.path.exists(os.path.join(current_path,"SAVAdata","temp","work")) else [""],label="合成历史", scale=2)
                            workrefbtn = gr.Button(value="🔄️", scale=1, min_width=60)
                            workloadbtn = gr.Button(value="加载", scale=1, min_width=60)
                            page_slider=gr.Slider(minimum=1,maximum=1,value=1,label="",step=Sava_Utils.config.num_edit_rows,scale=4)
                            audio_player=gr.Audio(label="",value=None,interactive=False,autoplay=True,scale=4)
                            recompose_btn = gr.Button(value="重新拼接", scale=1, min_width=60)
                            export_btn = gr.Button(value="导出字幕", scale=1, min_width=60)
                        for x in range(Sava_Utils.config.num_edit_rows):
                            edit_real_index=gr.Number(show_label=False,visible=False,value=-1,interactive=False)#real index                         
                            with gr.Row():
                                edit_check=gr.Checkbox(value=False,interactive=True,min_width=40,label="",scale=0)
                                edit_check_list.append(edit_check)
                                edit_rows.append(edit_real_index)  # real index
                                edit_real_index_list.append(edit_real_index)
                                edit_rows.append(gr.Text(scale=1,show_label=False,interactive=False,value='-1',max_lines=1,min_width=40))#index(raw)
                                edit_start_end_time=gr.Textbox(scale=3,show_label=False,interactive=False,value="NO INFO",max_lines=1)
                                edit_start_end_time_list.append(edit_start_end_time)
                                edit_rows.append(edit_start_end_time)#start time and end time
                                s_txt=gr.Textbox(scale=6,show_label=False,interactive=False,value="NO INFO",max_lines=1)#content
                                edit_rows.append(s_txt)
                                edit_rows.append(gr.Textbox(show_label=False,interactive=False,min_width=100,value="None",scale=1,max_lines=1))#speaker
                                edit_rows.append(gr.Textbox(value="NO INFO",show_label=False,interactive=False,min_width=100,scale=1,max_lines=1))#is success or delayed?
                                with gr.Row():
                                    __=gr.Button(value="▶️",scale=1,min_width=60)  
                                    __.click(play_audio,inputs=[edit_real_index,STATE],outputs=[audio_player])
                                    bv2regenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)  
                                    edit_rows.append(bv2regenbtn)
                                    bv2regenbtn.click(remake,inputs=[page_slider,edit_real_index,s_txt,*BV2_ARGS,STATE],outputs=[audio_player,*edit_rows])
                                    gsvregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=True)
                                    edit_rows.append(gsvregenbtn)  
                                    gsvregenbtn.click(remake,inputs=[page_slider,edit_real_index,s_txt,*GSV_ARGS,STATE],outputs=[audio_player,*edit_rows])
                                    msttsregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)
                                    edit_rows.append(msttsregenbtn)
                                    msttsregenbtn.click(remake,inputs=[page_slider,edit_real_index,s_txt,*MSTTS_ARGS,STATE],outputs=[audio_player,*edit_rows])  
                                    customregenbtn=gr.Button(value="🔄️",scale=1,min_width=60,visible=False)
                                    edit_rows.append(customregenbtn)      
                                    customregenbtn.click(remake,inputs=[page_slider,edit_real_index,s_txt,CUSTOM.choose_custom_api,STATE],outputs=[audio_player,*edit_rows])                         
                        page_slider.change(show_page,inputs=[page_slider,STATE],outputs=edit_rows)       
                        workloadbtn.click(load_work,inputs=[worklist],outputs=[STATE,page_slider,*edit_rows])
                        workrefbtn.click(getworklist,inputs=[],outputs=[worklist])
                        recompose_btn.click(recompose,inputs=[page_slider,STATE],outputs=[audio_output,gen_textbox_output_text,*edit_rows])
                        export_btn.click(lambda x:x.export(),inputs=[STATE],outputs=[input_file])
                        with gr.Row(equal_height=True):
                            all_selection_btn = gr.Button(value="全选",interactive=True,min_width=60)
                            all_selection_btn.click(lambda :[True for i in range(Sava_Utils.config.num_edit_rows)],inputs=[],outputs=edit_check_list)
                            reverse_selection_btn = gr.Button(value="反选",interactive=True,min_width=60)
                            reverse_selection_btn.click(lambda *args:[not i for i in args],inputs=edit_check_list,outputs=edit_check_list)
                            clear_selection_btn=gr.Button(value="清除选择",interactive=True,min_width=60)
                            clear_selection_btn.click(lambda :[False for i in range(Sava_Utils.config.num_edit_rows)],inputs=[],outputs=edit_check_list)
                            apply_se_btn = gr.Button(value="应用时间", interactive=True,min_width=60)
                            apply_se_btn.click(apply_start_end_time,inputs=[page_slider,STATE,*edit_real_index_list,*edit_start_end_time_list],outputs=[*edit_rows])
                            copy_btn = gr.Button(value="复制", interactive=True,min_width=60)
                            copy_btn.click(copy_subtitle,inputs=[page_slider,STATE,*edit_check_list,*edit_real_index_list],outputs=[*edit_check_list,page_slider,*edit_rows])
                            merge_btn = gr.Button(value="合并", interactive=True,min_width=60)
                            merge_btn.click(merge_subtitle,inputs=[page_slider,STATE,*edit_check_list,*edit_real_index_list],outputs=[*edit_check_list,page_slider,*edit_rows])
                            delete_btn = gr.Button(value="删除", interactive=True,min_width=60)
                            delete_btn.click(delete_subtitle,inputs=[page_slider,STATE,*edit_check_list,*edit_real_index_list],outputs=[*edit_check_list,page_slider,*edit_rows])
                        with gr.Accordion(label="多角色配音"):
                            with gr.Row(equal_height=True):
                                try:
                                    speaker_list_choices=["None",*os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))]
                                except:
                                    speaker_list_choices=["None"]
                                speaker_list=gr.Dropdown(label="选定默认/选择/创建说话人",value="None",choices=speaker_list_choices,allow_custom_value=not Sava_Utils.config.server_mode,scale=4)
                                #speaker_list.change(set_default_speaker,inputs=[speaker_list,STATE])
                                select_spk_projet=gr.Dropdown(choices=['bv2','gsv','mstts','custom'],value='gsv',interactive=True,label="说话人项目")
                                refresh_spk_list_btn=gr.Button(value="🔄️",min_width=60, scale=0)
                                refresh_spk_list_btn.click(getspklist,inputs=[],outputs=[speaker_list])
                                apply_btn = gr.Button(value="✅", min_width=60, scale=0)
                                apply_btn.click(apply_spk,inputs=[speaker_list,page_slider,STATE,*edit_check_list,*edit_real_index_list],outputs=[*edit_check_list,*edit_rows])

                                save_spk_btn_bv2=gr.Button(value="💾", min_width=60, scale=0,visible=False)
                                save_spk_btn_bv2.click(lambda *args:save_spk(*args,project="bv2"),inputs=[speaker_list,*BV2_ARGS],outputs=[speaker_list])
                                save_spk_btn_gsv=gr.Button(value="💾", min_width=60, scale=0,visible=True)
                                save_spk_btn_gsv.click(lambda *args:save_spk(*args,project="gsv"),inputs=[speaker_list,*GSV_ARGS],outputs=[speaker_list])
                                save_spk_btn_mstts=gr.Button(value="💾", min_width=60, scale=0,visible=False)
                                save_spk_btn_mstts.click(lambda *args:save_spk(*args,project="mstts"),inputs=[speaker_list,*MSTTS_ARGS],outputs=[speaker_list])
                                save_spk_btn_custom=gr.Button(value="💾", min_width=60, scale=0,visible=False)
                                save_spk_btn_custom.click(lambda *args:save_spk(*args,project="custom"),inputs=[speaker_list,CUSTOM.choose_custom_api],outputs=[speaker_list])

                                select_spk_projet.change(switch_spk_proj,inputs=[select_spk_projet],outputs=[save_spk_btn_bv2,save_spk_btn_gsv,save_spk_btn_mstts,save_spk_btn_custom])

                                del_spk_list_btn=gr.Button(value="🗑️", min_width=60, scale=0)
                                del_spk_list_btn.click(del_spk,inputs=[speaker_list],outputs=[speaker_list])
                                start_gen_multispeaker_btn=gr.Button(value="生成多角色配音",variant="primary")
                                start_gen_multispeaker_btn.click(gen_multispeaker,inputs=[STATE,workers],outputs=[audio_output,page_slider,*edit_rows])
            with gr.TabItem("辅助功能"):
                TRANSLATION_MODULE.UI(input_file)
            with gr.TabItem("外部扩展内容"):
                available=False
                from Sava_Utils.extern_extensions.wav2srt import WAV2SRT
                WAV2SRT = WAV2SRT(config=Sava_Utils.config)
                componments.append(WAV2SRT)
                available=WAV2SRT.UI(input_file,TRANSLATION_MODULE.translation_upload)
                if not available:
                    gr.Markdown("没有任何扩展，安装后重启生效<br>[获取外部扩展内容](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/tree/main/tools)")
            with gr.TabItem("设置"):
                with gr.Row():
                    with gr.Column():
                        SETTINGS=Sava_Utils.settings.Settings_UI(componments=componments)
                        SETTINGS.getUI()
                    with gr.Column():
                        with gr.TabItem("简介"):
                            gr.Markdown(value=Man.getInfo("readme"))
                        with gr.TabItem("常见错误"):
                            gr.Markdown(value=Man.getInfo("issues"))
                        with gr.TabItem("使用指南"):
                            gr.Markdown(value=Man.getInfo("help"))       
        create_multispeaker_btn.click(create_multi_speaker,inputs=[input_file,fps,offset],outputs=[worklist,page_slider,*edit_rows,STATE])
        BV2.gen_btn1.click(lambda *args:generate_preprocess(*args,project="bv2"),inputs=[input_file,fps,offset,workers,*BV2_ARGS],outputs=[audio_output,gen_textbox_output_text,worklist,page_slider,*edit_rows,STATE])
        GSV.gen_btn2.click(lambda *args:generate_preprocess(*args,project="gsv"),inputs=[input_file,fps,offset,workers,*GSV_ARGS],outputs=[audio_output,gen_textbox_output_text,worklist,page_slider,*edit_rows,STATE])
        MSTTS.gen_btn3.click(lambda *args:generate_preprocess(*args,project="mstts"),inputs=[input_file,fps,offset,workers,*MSTTS_ARGS],outputs=[audio_output,gen_textbox_output_text,worklist,page_slider,*edit_rows,STATE])
        CUSTOM.gen_btn4.click(lambda *args:generate_preprocess(*args,project="custom"),inputs=[input_file,fps,offset,workers,CUSTOM.choose_custom_api],outputs=[audio_output,gen_textbox_output_text,worklist,page_slider,*edit_rows,STATE])

    app.queue(concurrency_count=Sava_Utils.config.concurrency_count).launch(
            share=args.share,
            server_port=server_port if server_port>0 else None,
            inbrowser=True,
            server_name='0.0.0.0' if Sava_Utils.config.LAN_access else '127.0.0.1'
            )
