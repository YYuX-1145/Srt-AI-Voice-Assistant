import os
import sys
import io
# import inspect
import warnings

if getattr(sys, "frozen", False):
    current_path = os.path.dirname(sys.executable)
    os.environ["exe"] = 'True'
elif __file__:
    current_path = os.path.dirname(__file__)
    os.environ["exe"] = 'False'
os.environ["current_path"] = current_path

import shutil

import gradio as gr
warnings.filterwarnings("ignore", category=UserWarning)

import json

# import datetime
import time
import soundfile as sf
import concurrent.futures
from tqdm import tqdm
from collections import defaultdict

import Sava_Utils
from Sava_Utils import logger, i18n, args, MANUAL
from Sava_Utils.utils import *
from Sava_Utils.edit_panel import *
from Sava_Utils.subtitle import Base_subtitle, Subtitle, Subtitles

import Sava_Utils.tts_projects
import Sava_Utils.tts_projects.bv2
import Sava_Utils.tts_projects.gsv
import Sava_Utils.tts_projects.mstts
import Sava_Utils.tts_projects.custom
from Sava_Utils.subtitle_translation import Translation_module
from Sava_Utils.polyphone import Polyphone

BV2 = Sava_Utils.tts_projects.bv2.BV2(Sava_Utils.config)
GSV = Sava_Utils.tts_projects.gsv.GSV(Sava_Utils.config)
MSTTS = Sava_Utils.tts_projects.mstts.MSTTS(Sava_Utils.config)
CUSTOM = Sava_Utils.tts_projects.custom.Custom(Sava_Utils.config)
TRANSLATION_MODULE = Translation_module(Sava_Utils.config)
POLYPHONE = Polyphone(Sava_Utils.config)
Projet_dict = {"bv2": BV2, "gsv": GSV, "mstts": MSTTS, "custom": CUSTOM}
componments = {
    1: [GSV, BV2, MSTTS, CUSTOM],
    2: [TRANSLATION_MODULE, POLYPHONE],
    3: [],
}


def custom_api(text):
    raise i18n('You need to load custom API functions!')


#single speaker
def generate(*args, interrupt_event: Sava_Utils.utils.Flag, proj="", in_files=[], fps=30, offset=0, max_workers=1):
    t1 = time.time()
    fps = positive_int(fps)
    if in_files in [None, []]:
        gr.Info(i18n('Please upload the subtitle file!'))
        return (None, i18n('Please upload the subtitle file!'), getworklist(), *load_page(Subtitles()), Subtitles())
    if Sava_Utils.config.server_mode and len(in_files) > 1:
        gr.Warning(i18n('The current mode does not allow batch processing!'))
        return (None, i18n('The current mode does not allow batch processing!'), getworklist(), *load_page(Subtitles()), Subtitles())
    os.makedirs(os.path.join(current_path, "SAVAdata", "output"), exist_ok=True)
    for in_file in in_files:
        try:
            subtitle_list = read_file(in_file.name, fps, offset)
        except Exception as e:
            what = str(e)
            gr.Warning(what)
            return (None, what, getworklist(), *load_page(Subtitles()), Subtitles())
        # subtitle_list.sort()
        subtitle_list.set_dir_name(os.path.basename(in_file.name).replace(".", "-"))
        subtitle_list.set_proj(proj)
        Projet_dict[proj].before_gen_action(*args, config=Sava_Utils.config, notify=False, force=False)
        abs_dir = subtitle_list.get_abs_dir()
        if Sava_Utils.config.server_mode:
            max_workers = 1        
        file_list = []
        with interrupt_event:            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(save, args, proj=proj, dir=abs_dir, subtitle=i) for i in subtitle_list]
                for future in tqdm(
                    concurrent.futures.as_completed(futures),
                    total=len(subtitle_list),
                    desc=i18n('Synthesizing single-speaker task'),
                ):
                    if interrupt_event.is_set():
                        executor.shutdown(wait=True, cancel_futures=True)
                        subtitle_list.dump()
                        gr.Info("Interrupted.")
                        break
                    item = future.result()
                    if item:
                        file_list.append(item)
            if interrupt_event.is_set():
                sr_audio = None
                break
            if len(file_list) == 0:
                shutil.rmtree(abs_dir)
                if len(in_files) == 1:
                    raise gr.Error(i18n('All subtitle syntheses have failed, please check the API service!'))
                else:
                    continue
        sr_audio = subtitle_list.audio_join(sr=Sava_Utils.config.output_sr)
    t2 = time.time()
    m, s = divmod(t2 - t1, 60)
    use_time = "%02d:%02d" % (m, s)
    return (
        sr_audio,
        f"{i18n('Done! Time used')}:{use_time}",
        getworklist(value=subtitle_list.dir),
        *load_page(subtitle_list),
        subtitle_list,
    )


def generate_preprocess(interrupt_event, *args, project=None):
    try:
        args, kwargs = Projet_dict[project].arg_filter(*args)
    except Exception as e:
        info = f"{i18n('An error occurred')}: {str(e)}"
        gr.Warning(info)
        return None, info, getworklist(), *load_page(Subtitles()), Subtitles()
    return generate(*args, interrupt_event=interrupt_event, **kwargs)


def gen_multispeaker(interrupt_event: Sava_Utils.utils.Flag, *args, remake=False):  # args: page,maxworkers,*args,subtitles
    page = args[0]
    max_workers = int(args[1])
    subtitles: Subtitles = args[-1]
    if subtitles is None or len(subtitles) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return *show_page(page, Subtitles()), None
    proj_args = (None, None, *args[:-1])
    if remake:
        todo = [i for i in subtitles if not i.is_success]
    else:
        todo = subtitles
    if len(todo) == 0:
        gr.Info(i18n('No subtitles are going to be resynthesized.'))
        return *show_page(page, subtitles), None
    abs_dir = subtitles.get_abs_dir()
    tasks = defaultdict(list)
    for i in todo:
        tasks[i.speaker].append(i)
    if list(tasks.keys()) == [None] and subtitles.default_speaker is None and subtitles.proj is None:
        gr.Warning(i18n('Warning: No speaker has been assigned'))
        return *show_page(page, subtitles), None
    ok = True
    progress = 0
    for key in tasks.keys():
        if key is None:
            if subtitles.proj is None and subtitles.default_speaker is not None and len(tasks[None]) > 0:
                print(f"{i18n('Using default speaker')}:{subtitles.default_speaker}")
                spk = subtitles.default_speaker
            elif subtitles.proj is not None and remake:
                args = proj_args
                project = subtitles.proj
                spk = None
            else:
                continue
        else:
            spk = key
        if spk is not None:
            try:
                with open(os.path.join(current_path, "SAVAdata", "speakers", spk), 'rb') as f:
                    info = pickle.load(f)
            except FileNotFoundError:
                ok = False
                logger.error(f"{i18n('Speaker archive not found')}: {spk}")
                gr.Warning(f"{i18n('Speaker archive not found')}: {spk}")
                continue
            args = info["raw_data"]
            project = info["project"]
        try:
            args, kwargs = Projet_dict[project].arg_filter(*args)
            Projet_dict[project].before_gen_action(*args, config=Sava_Utils.config)
        except Exception as e:
            ok = False
            gr.Warning(str(e))
            continue
        if Sava_Utils.config.server_mode:
            max_workers = 1
        file_list = []
        with interrupt_event:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(save, args, proj=project, dir=abs_dir, subtitle=i) for i in tasks[key]]
                for future in tqdm(
                    concurrent.futures.as_completed(futures),
                    total=len(todo),
                    initial=progress,
                    desc=f"{i18n('Synthesizing multi-speaker task, the current speaker is')} :{spk}",
                ):
                    if interrupt_event.is_set():
                        executor.shutdown(wait=True, cancel_futures=True)
                        gr.Info("Interrupted.")
                        ok = False
                        break
                    item = future.result()
                    if item:
                        file_list.append(item)
                if interrupt_event.is_set():
                    break     
        progress += len(file_list)
        if len(file_list) == 0:
            ok = False
            gr.Warning(f"{i18n('Synthesis for the single speaker has failed !')} {spk}")

    gr.Info(i18n('Done!'))
    if remake:
        if ok:
            gr.Info(i18n('Audio re-generation was successful! Click the <Reassemble Audio> button.'))
        subtitles.dump()
        return show_page(page, subtitles)
    else:
        sr_audio = subtitles.audio_join(sr=Sava_Utils.config.output_sr)
    return *show_page(page, subtitles), sr_audio


def save(args, proj: str = None, dir: str = None, subtitle: Subtitle = None):
    audio = Projet_dict[proj].save_action(*args, text=subtitle.text)
    if audio is not None:
        if audio[:4] == b'RIFF' and audio[8:12] == b'WAVE':
            # sr=int.from_bytes(audio[24:28],'little')
            filepath = os.path.join(dir, f"{subtitle.index}.wav")
            if Sava_Utils.config.remove_silence:
                audio, sr = Sava_Utils.librosa_load.load_audio(io.BytesIO(audio))
                audio = remove_silence(audio, sr)
                sf.write(filepath, audio, sr)
            else:
                with open(filepath, 'wb') as file:
                    file.write(audio)
            if Sava_Utils.config.max_accelerate_ratio > 1.0:
                audio, sr = Sava_Utils.librosa_load.load_audio(filepath)
                target_dur = int(subtitle.end_time - subtitle.start_time) * sr
                if target_dur > 0 and (audio.shape[-1] - target_dur) > (0.01 * sr):
                    ratio = min(audio.shape[-1] / target_dur, Sava_Utils.config.max_accelerate_ratio)
                    cmd = f'ffmpeg -i "{filepath}" -filter:a atempo={ratio:.2f} -y "{filepath}.wav"'
                    p = subprocess.Popen(cmd, cwd=current_path, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger.info(f"{i18n('Execute command')}:{cmd}")
                    exit_code = p.wait()
                    if exit_code == 0:
                        shutil.move(f"{filepath}.wav", filepath)
                    else:
                        logger.error("Failed to execute ffmpeg.")
            subtitle.is_success = True
            return filepath
        else:
            data = json.loads(audio)
            logger.error(f"{i18n('Failed subtitle id')}:{subtitle.index},{i18n('error message received')}:{str(data)}")
            subtitle.is_success = False
            return None
    else:
        logger.error(f"{i18n('Failed subtitle id')}:{subtitle.index}")
        subtitle.is_success = False
        return None


def start_hiyoriui():
    if Sava_Utils.config.bv2_pydir == "":
        gr.Warning(i18n('Please go to the settings page to specify the corresponding environment path and do not forget to save it!'))
        return i18n('Please go to the settings page to specify the corresponding environment path and do not forget to save it!')
    command = f'"{Sava_Utils.config.bv2_pydir}" "{os.path.join(Sava_Utils.config.bv2_dir,"hiyoriUI.py")}" {Sava_Utils.config.bv2_args}'
    rc_open_window(command=command, dir=Sava_Utils.config.bv2_dir)
    time.sleep(0.1)
    return f"HiyoriUI{i18n(' has been launched, please ensure the configuration is correct.')}"


def start_gsv():
    if Sava_Utils.config.gsv_pydir == "":
        gr.Warning(i18n('Please go to the settings page to specify the corresponding environment path and do not forget to save it!'))
        return i18n('Please go to the settings page to specify the corresponding environment path and do not forget to save it!')
    if Sava_Utils.config.gsv_fallback:
        apath = "api.py"
        gr.Info(i18n('API downgraded to v1, functionality is limited.'))
        logger.warning(i18n('API downgraded to v1, functionality is limited.'))
    else:
        apath = "api_v2.py"
    if not os.path.exists(os.path.join(Sava_Utils.config.gsv_dir, apath)):
        raise FileNotFoundError(os.path.join(Sava_Utils.config.gsv_dir, apath))
    command = f'"{Sava_Utils.config.gsv_pydir}" "{os.path.join(Sava_Utils.config.gsv_dir,apath)}" {Sava_Utils.config.gsv_args}'
    rc_open_window(command=command, dir=Sava_Utils.config.gsv_dir)
    time.sleep(0.1)
    return f"GSV-API{i18n(' has been launched, please ensure the configuration is correct.')}"


def remake(*args):
    fp = None
    subtitle_list = args[-1]
    args = args[:-1]
    page, idx, timestamp, s_txt = args[:4]
    idx = int(idx)
    if int(args[1]) == -1:
        gr.Info("Not available!")
        return fp, *load_single_line(subtitle_list, idx)
    if Sava_Utils.config.server_mode and len(s_txt) > 512:
        gr.Warning("too long!")
        return fp, *load_single_line(subtitle_list, idx)
    subtitle_list[idx].text = s_txt
    subtitle_list[idx].is_success = None
    try:
        subtitle_list[idx].reset_srt_time(timestamp)
    except ValueError as e:
        gr.Info(str(e))
    if subtitle_list[idx].speaker is not None or (subtitle_list.proj is None and subtitle_list.default_speaker is not None):
        spk = subtitle_list[idx].speaker
        if spk is None:
            spk = subtitle_list.default_speaker
        try:
            with open(os.path.join(current_path, "SAVAdata", "speakers", spk), 'rb') as f:
                info = pickle.load(f)
        except FileNotFoundError:
            logger.error(f"{i18n('Speaker archive not found')}: {spk}")
            gr.Warning(f"{i18n('Speaker archive not found')}: {spk}")
            return fp, *load_single_line(subtitle_list, idx)
        args = info["raw_data"]
        proj = info["project"]
        args, kwargs = Projet_dict[proj].arg_filter(*args)
        # Projet_dict[proj].before_gen_action(*args,notify=False,force=True)
    else:
        if subtitle_list.proj is None:
            gr.Info(i18n('You must specify the speakers while using multi-speaker dubbing!'))
            return fp, *load_single_line(subtitle_list, idx)
        # args = [None, *args]  # ~~fill data~~
        try:
            proj = subtitle_list.proj
            args, kwargs = Projet_dict[proj].arg_filter(*args)
        except Exception as e:
            # print(e)
            return fp, *load_single_line(subtitle_list, idx)
    Projet_dict[proj].before_gen_action(*args, config=Sava_Utils.config, notify=False, force=False)
    # subtitle_list[idx].text = s_txt
    fp = save(args, proj=proj, dir=subtitle_list.get_abs_dir(), subtitle=subtitle_list[idx])
    if fp is not None:
        gr.Info(i18n('Audio re-generation was successful! Click the <Reassemble Audio> button.'))
    else:
        gr.Warning("Audio re-generation failed!")
    subtitle_list.dump()
    return fp, *load_single_line(subtitle_list, idx)


def recompose(page: int, subtitle_list: Subtitles):
    if subtitle_list is None or len(subtitle_list) == 0:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return None, i18n('There is no subtitle in the current workspace'), *show_page(page, subtitle_list)
    audio = subtitle_list.audio_join(sr=Sava_Utils.config.output_sr)
    gr.Info(i18n("Reassemble successfully!"))
    return audio, "OK", *show_page(page, subtitle_list)


def save_spk(name: str, *args, project: str):
    name = name.strip()
    if Sava_Utils.config.server_mode:
        gr.Warning(i18n('This function has been disabled!'))
        return getspklist()
    if name in ["", [], None, 'None']:
        gr.Info(i18n('Please enter a valid name!'))
        return getspklist()
    args = [None, None, None, None, *args]
    # catch all arguments
    # process raw data before generating
    try:
        Projet_dict[project].arg_filter(*args)
        os.makedirs(os.path.join(current_path, "SAVAdata", "speakers"), exist_ok=True)
        with open(os.path.join(current_path, "SAVAdata", "speakers", name), "wb") as f:
            pickle.dump({"project": project, "raw_data": args}, f)
        gr.Info(f"{i18n('Saved successfully')}: [{project}]{name}")
    except Exception as e:
        gr.Warning(str(e))
        return getspklist(value=name)
    return getspklist(value=name)


if __name__ == "__main__":
    os.environ['GRADIO_TEMP_DIR'] = os.path.join(current_path, "SAVAdata", "temp", "gradio")
    workspaces_list = refworklist()
    if args.server_port is None:
        server_port = Sava_Utils.config.server_port
    else:
        server_port = args.server_port
    with gr.Blocks(title="Srt-AI-Voice-Assistant-WebUI", theme=Sava_Utils.config.theme, analytics_enabled=False) as app:
        STATE = gr.State(value=Subtitles())
        INTERRUPT_EVENT = gr.State(value=Sava_Utils.utils.Flag())
        gr.Markdown(value=MANUAL.getInfo("title"))
        with gr.Tabs():
            with gr.TabItem(i18n('Subtitle Dubbing')):
                with gr.Row():
                    with gr.Column():
                        textbox_intput_text = gr.TextArea(label=i18n('File content'), value="", interactive=False)
                        with gr.Accordion(i18n('Speaker Map'), open=False):
                            use_labled_text_mode = gr.Checkbox(label=i18n('Enable Marking Mode'))
                            speaker_map_set = gr.State(value=set())
                            speaker_map_dict = gr.State(value=dict())
                            edit_map_ui_md1 = f"### <center>{i18n('Speaker map is empty.')}</center>"
                            edit_map_ui_md2 = f"### <center>{i18n('Original Speaker')}</center>"
                            edit_map_ui_md3 = f"### <center>{i18n('Target Speaker')}</center>"
                            @gr.render(inputs=speaker_map_set)
                            def edit_map_ui(x):
                                if len(x)==0:
                                    gr.Markdown(value=edit_map_ui_md1)
                                    return
                                c = refspklist()
                                with gr.Row():
                                    gr.Markdown(value=edit_map_ui_md2)
                                    gr.Markdown(value=edit_map_ui_md3)
                                with gr.Group():
                                    for i in x:
                                        with gr.Row():
                                            k = gr.Textbox(value=i,show_label=False,interactive=False)
                                            v = gr.Dropdown(value=i, choices=c, show_label=False, allow_custom_value=True)
                                            v.change(modify_spkmap, inputs=[speaker_map_dict,k,v])
                                gr.Button(value="🗑️",variant="stop").click(lambda:(set(),dict()),outputs=[speaker_map_set,speaker_map_dict])
                            with gr.Accordion(i18n('Identify Original Speakers'),open=True):
                                update_spkmap_btn_upload = gr.Button(value=i18n('From Upload File'))
                                update_spkmap_btn_current = gr.Button(value=i18n('From Workspace'))
                            apply_spkmap2workspace_btn = gr.Button(value=i18n('Apply to current Workspace'))
                        create_multispeaker_btn = gr.Button(value=i18n('Create Multi-Speaker Dubbing Project'))
                    with gr.Column():
                        TTS_ARGS=[]
                        for i in componments[1]:
                            TTS_ARGS.append(i.getUI())
                    GSV_ARGS,BV2_ARGS,MSTTS_ARGS,CUSTOM_ARGS=TTS_ARGS
                    with gr.Column():
                        with gr.Accordion(i18n('Other Parameters'), open=True):
                            fps = gr.Number(label=i18n('Frame rate of Adobe Premiere project, only applicable to csv files exported from Pr'), value=30, visible=True, interactive=True, minimum=1)
                            workers = gr.Number(label=i18n('Number of threads for sending requests'), value=2, visible=True, interactive=True, minimum=1)
                            offset = gr.Slider(minimum=-6, maximum=6, value=0, step=0.1, label=i18n('Voice time offset (seconds)'))
                        input_file = gr.File(label=i18n('Upload file (Batch mode only supports one speaker at a time)'), file_types=['.csv', '.srt', '.txt'], file_count='multiple')
                        gen_textbox_output_text = gr.Textbox(label=i18n('Output Info'), interactive=False)
                        audio_output = gr.Audio(label="Output Audio")
                        stop_btn = gr.Button(value=i18n('Stop'),variant="stop")
                        stop_btn.click(lambda x:gr.Info(x.set()),inputs=[INTERRUPT_EVENT])
                        if not Sava_Utils.config.server_mode:
                            with gr.Accordion(i18n('API Launcher')):
                                start_hiyoriui_btn = gr.Button(value="HiyoriUI")
                                start_gsv_btn = gr.Button(value="GPT-SoVITS")
                                start_hiyoriui_btn.click(start_hiyoriui, outputs=[gen_textbox_output_text])
                                start_gsv_btn.click(start_gsv, outputs=[gen_textbox_output_text])
                        input_file.change(file_show, inputs=[input_file], outputs=[textbox_intput_text])

                with gr.Accordion(label=i18n('Editing area *Note: DO NOT clear temporary files while using this function.'), open=True):
                    with gr.Column():
                        edit_rows = []
                        edit_real_index_list = []
                        edit_check_list = []
                        edit_start_end_time_list = []
                        with gr.Row(equal_height=True):
                            worklist = gr.Dropdown(choices=workspaces_list if len(workspaces_list) > 0 else [""], label=i18n('History'), scale=2)
                            workrefbtn = gr.Button(value="🔄️", scale=1, min_width=40, visible=not Sava_Utils.config.server_mode, interactive=not Sava_Utils.config.server_mode)
                            workloadbtn = gr.Button(value=i18n('Load'), scale=1, min_width=40)
                            page_slider = gr.Slider(minimum=1, maximum=1, value=1, label="", step=Sava_Utils.config.num_edit_rows, scale=5)
                            audio_player = gr.Audio(show_label=False, value=None, interactive=False, autoplay=True, scale=4, waveform_options={"show_recording_waveform":False})
                            recompose_btn = gr.Button(value=i18n('Reassemble Audio'), scale=1, min_width=100)
                            export_btn = gr.Button(value=i18n('Export Subtitles'), scale=1, min_width=100)
                        for x in range(Sava_Utils.config.num_edit_rows):
                            edit_real_index = gr.Number(show_label=False, visible=False, value=-1, interactive=False)  # real index
                            with gr.Row(equal_height=True, height=55):
                                edit_check = gr.Checkbox(value=False, interactive=True, min_width=40, show_label=False, label="", scale=0)
                                edit_check_list.append(edit_check)
                                edit_rows.append(edit_real_index)  # real index
                                edit_real_index_list.append(edit_real_index)
                                edit_rows.append(gr.Textbox(scale=1, visible=False, show_label=False, interactive=False, value='-1', max_lines=1, min_width=40))  # index(raw)
                                edit_start_end_time = gr.Textbox(scale=3, visible=False, show_label=False, interactive=False, value="NO INFO", max_lines=1)
                                edit_start_end_time_list.append(edit_start_end_time)
                                edit_rows.append(edit_start_end_time)  # start time and end time
                                s_txt = gr.Textbox(scale=6, visible=False, show_label=False, interactive=False, value="NO INFO", max_lines=1)  # content
                                edit_rows.append(s_txt)
                                edit_rows.append(gr.Textbox(show_label=False, visible=False, interactive=False, min_width=100, value="None", scale=1, max_lines=1))  # speaker
                                edit_rows.append(gr.Textbox(value="NO INFO", show_label=False, visible=False, interactive=False, min_width=100, scale=1, max_lines=1))  # is success or delayed?
                                with gr.Row(equal_height=True):
                                    __ = gr.Button(value="▶️", scale=1, min_width=50)
                                    __.click(play_audio, inputs=[edit_real_index, STATE], outputs=[audio_player])
                                    bv2regenbtn = gr.Button(value="🔄️", scale=1, min_width=50, visible=False)                        
                                    bv2regenbtn.click(remake, inputs=[page_slider, edit_real_index, edit_start_end_time, s_txt, *BV2_ARGS, STATE], outputs=[audio_player, page_slider] + edit_rows[-6:])
                                    gsvregenbtn = gr.Button(value="🔄️", scale=1, min_width=50, visible=True)
                                    gsvregenbtn.click(remake, inputs=[page_slider, edit_real_index, edit_start_end_time, s_txt, *GSV_ARGS, STATE], outputs=[audio_player, page_slider] + edit_rows[-6:])
                                    msttsregenbtn = gr.Button(value="🔄️", scale=1, min_width=50, visible=False)
                                    msttsregenbtn.click(remake, inputs=[page_slider, edit_real_index, edit_start_end_time, s_txt, *MSTTS_ARGS, STATE], outputs=[audio_player, page_slider] + edit_rows[-6:])
                                    customregenbtn = gr.Button(value="🔄️", scale=1, min_width=50, visible=False)
                                    customregenbtn.click(remake, inputs=[page_slider, edit_real_index, edit_start_end_time, s_txt, CUSTOM.choose_custom_api, STATE], outputs=[audio_player, page_slider] + edit_rows[-6:])
                                    edit_rows.append(bv2regenbtn)
                                    edit_rows.append(gsvregenbtn)
                                    edit_rows.append(msttsregenbtn)
                                    edit_rows.append(customregenbtn)                                    
                        workrefbtn.click(getworklist, inputs=[], outputs=[worklist])
                        export_btn.click(lambda file_list, x: ([i.name for i in file_list] if file_list else []) + ([o] if (o:=x.export()) else []), inputs=[input_file, STATE], outputs=[input_file])
                        with gr.Row(equal_height=True):
                            all_selection_btn = gr.Button(value=i18n('Select All'), interactive=True, min_width=50)
                            all_selection_btn.click(None, inputs=[], outputs=edit_check_list, js=f"() => Array({Sava_Utils.config.num_edit_rows}).fill(true)")
                            reverse_selection_btn = gr.Button(value=i18n('Reverse Selection'), interactive=True, min_width=50)
                            reverse_selection_btn.click(None, inputs=edit_check_list, outputs=edit_check_list, js="(...vals) => vals.map(v => !v)")
                            clear_selection_btn = gr.Button(value=i18n('Clear Selection'), interactive=True, min_width=50)
                            clear_selection_btn.click(None, inputs=[], outputs=edit_check_list, js=f"() => Array({Sava_Utils.config.num_edit_rows}).fill(false)")
                            apply_se_btn = gr.Button(value=i18n('Apply Timestamp modifications'), interactive=True, min_width=50)
                            apply_se_btn.click(apply_start_end_time, inputs=[page_slider, STATE, *edit_real_index_list, *edit_start_end_time_list], outputs=edit_rows)
                            copy_btn = gr.Button(value=i18n('Copy'), interactive=True, min_width=50)
                            copy_btn.click(copy_subtitle, inputs=[page_slider, STATE, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, page_slider, *edit_rows])
                            merge_btn = gr.Button(value=i18n('Merge'), interactive=True, min_width=50)
                            merge_btn.click(merge_subtitle, inputs=[page_slider, STATE, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, page_slider, *edit_rows])
                            delete_btn = gr.Button(value=i18n('Delete'), interactive=True, min_width=50)
                            delete_btn.click(delete_subtitle, inputs=[page_slider, STATE, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, page_slider, *edit_rows])
                            all_regen_btn_bv2 = gr.Button(value=i18n('Continue Generation'), variant="primary", visible=False, interactive=True, min_width=50)
                            edit_rows.append(all_regen_btn_bv2)
                            all_regen_btn_gsv = gr.Button(value=i18n('Continue Generation'), variant="primary", visible=True, interactive=True, min_width=50)
                            edit_rows.append(all_regen_btn_gsv)
                            all_regen_btn_mstts = gr.Button(value=i18n('Continue Generation'), variant="primary", visible=False, interactive=True, min_width=50)
                            edit_rows.append(all_regen_btn_mstts)
                            all_regen_btn_custom = gr.Button(value=i18n('Continue Generation'), variant="primary", visible=False, interactive=True, min_width=50)
                            edit_rows.append(all_regen_btn_custom)
                            all_regen_btn_bv2.click(lambda process=gr.Progress(track_tqdm=True), *args: gen_multispeaker(*args, remake=True), inputs=[INTERRUPT_EVENT, page_slider, workers, *BV2_ARGS, STATE], outputs=edit_rows)
                            all_regen_btn_gsv.click(lambda process=gr.Progress(track_tqdm=True), *args: gen_multispeaker(*args, remake=True), inputs=[INTERRUPT_EVENT, page_slider, workers, *GSV_ARGS, STATE], outputs=edit_rows)
                            all_regen_btn_mstts.click(lambda process=gr.Progress(track_tqdm=True), *args: gen_multispeaker(*args, remake=True), inputs=[INTERRUPT_EVENT, page_slider, workers, *MSTTS_ARGS, STATE], outputs=edit_rows)
                            all_regen_btn_custom.click(lambda process=gr.Progress(track_tqdm=True), *args: gen_multispeaker(*args, remake=True), inputs=[INTERRUPT_EVENT, page_slider, workers, CUSTOM.choose_custom_api, STATE], outputs=edit_rows)

                        page_slider.change(show_page, inputs=[page_slider, STATE], outputs=edit_rows)
                        workloadbtn.click(load_work, inputs=[worklist], outputs=[STATE, page_slider, *edit_rows])
                        recompose_btn.click(recompose, inputs=[page_slider, STATE], outputs=[audio_output, gen_textbox_output_text, *edit_rows])

                        apply_spkmap2workspace_btn.click(apply_spkmap2workspace,inputs=[speaker_map_dict,page_slider,STATE],outputs=edit_rows)

                        with gr.Accordion(i18n('Find and Replace'), open=False):
                            with gr.Row(equal_height=True):
                                find_text_expression = gr.Textbox(show_label=False, placeholder=i18n('Find What'), scale=3)
                                target_text = gr.Textbox(show_label=False, placeholder=i18n('Replace With'), scale=3)
                                find_and_rep_exec = gr.Textbox(show_label=False, placeholder=r'Exec... e.g. item.speaker="Name"', scale=3, visible=not Sava_Utils.config.server_mode)
                                enable_re = gr.Checkbox(label=i18n('Enable Regular Expression'), min_width=60, scale=1)
                                find_next_btn = gr.Button(value=i18n('Find Next'), variant="secondary", min_width=50, scale=1)
                                replace_all_btn = gr.Button(value=i18n('Replace All'), variant="primary", min_width=50, scale=1)
                                find_next_btn.click(find_next, inputs=[STATE, find_text_expression, enable_re, page_slider, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, page_slider, *edit_rows])
                                replace_all_btn.click(find_and_replace, inputs=[STATE, find_text_expression, target_text, find_and_rep_exec, enable_re, page_slider], outputs=[page_slider, *edit_rows])
                with gr.Accordion(label=i18n('Multi-speaker dubbing')):
                    with gr.Row(equal_height=True):
                        speaker_list = gr.Dropdown(label=i18n('Select/Create Speaker'), value="None", choices=refspklist(), allow_custom_value=not Sava_Utils.config.server_mode, scale=4)
                        # speaker_list.change(set_default_speaker,inputs=[speaker_list,STATE])
                        select_spk_projet = gr.Dropdown(choices=['bv2', 'gsv', 'mstts', 'custom'], value='gsv', interactive=True, label=i18n('TTS Project'))
                        refresh_spk_list_btn = gr.Button(value="🔄️", min_width=60, scale=0)
                        refresh_spk_list_btn.click(getspklist, inputs=[], outputs=[speaker_list])
                        apply_btn = gr.Button(value="✅", min_width=60, scale=0)
                        apply_btn.click(apply_spk, inputs=[speaker_list, page_slider, STATE, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, *edit_rows])

                        save_spk_btn_bv2 = gr.Button(value="💾", min_width=60, scale=0, visible=False)
                        save_spk_btn_bv2.click(lambda *args: save_spk(*args, project="bv2"), inputs=[speaker_list, *BV2_ARGS], outputs=[speaker_list])
                        save_spk_btn_gsv = gr.Button(value="💾", min_width=60, scale=0, visible=True)
                        save_spk_btn_gsv.click(lambda *args: save_spk(*args, project="gsv"), inputs=[speaker_list, *GSV_ARGS], outputs=[speaker_list])
                        save_spk_btn_mstts = gr.Button(value="💾", min_width=60, scale=0, visible=False)
                        save_spk_btn_mstts.click(lambda *args: save_spk(*args, project="mstts"), inputs=[speaker_list, *MSTTS_ARGS], outputs=[speaker_list])
                        save_spk_btn_custom = gr.Button(value="💾", min_width=60, scale=0, visible=False)
                        save_spk_btn_custom.click(lambda *args: save_spk(*args, project="custom"), inputs=[speaker_list, CUSTOM.choose_custom_api], outputs=[speaker_list])

                        select_spk_projet.change(switch_spk_proj, inputs=[select_spk_projet], outputs=[save_spk_btn_bv2, save_spk_btn_gsv, save_spk_btn_mstts, save_spk_btn_custom])

                        del_spk_list_btn = gr.Button(value="🗑️", min_width=60, scale=0)
                        del_spk_list_btn.click(del_spk, inputs=[speaker_list], outputs=[speaker_list])
                        start_gen_multispeaker_btn = gr.Button(value=i18n('Start Multi-speaker Synthesizing'), variant="primary")
                        start_gen_multispeaker_btn.click(lambda process=gr.Progress(track_tqdm=True),*args:gen_multispeaker(*args), inputs=[INTERRUPT_EVENT, page_slider, workers, STATE], outputs=edit_rows + [audio_output])
            with gr.TabItem(i18n('Auxiliary Functions')):
                for i in componments[2]:
                    i.getUI(input_file)
            with gr.TabItem(i18n('Extended Contents')):
                available = False
                from Sava_Utils.extern_extensions.wav2srt_webui import WAV2SRT
                WAV2SRT = WAV2SRT(config=Sava_Utils.config)
                componments[3].append(WAV2SRT)
                available = WAV2SRT.getUI(input_file, worklist, TRANSLATION_MODULE)
                if not available:
                    gr.Markdown("No additional extensions have been installed and a restart is required for the changes to take effect.<br>[Get Extentions](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/tree/main/tools)")
            with gr.TabItem(i18n('Settings')):
                with gr.Row():
                    with gr.Column():
                        SETTINGS = Sava_Utils.settings.Settings_UI(componments=componments)
                        SETTINGS.getUI()
                    with gr.Column():
                        with gr.TabItem(i18n('Readme')):
                            gr.Markdown(value=MANUAL.getInfo("readme"))
                            gr.Markdown(value=MANUAL.getInfo("changelog"))
                        with gr.TabItem(i18n('Issues')):
                            gr.Markdown(value=MANUAL.getInfo("issues"))
                        with gr.TabItem(i18n('Help & User guide')):
                            gr.Markdown(value=MANUAL.getInfo("help"))

        update_spkmap_btn_upload.click(get_speaker_map_from_file, inputs=[input_file], outputs=[speaker_map_set,speaker_map_dict])
        update_spkmap_btn_current.click(get_speaker_map_from_sub, inputs=[STATE], outputs=[speaker_map_set, speaker_map_dict])
        create_multispeaker_btn.click(create_multi_speaker, inputs=[input_file, use_labled_text_mode,speaker_map_dict, fps, offset], outputs=[worklist, page_slider, *edit_rows, STATE])
        BV2.gen_btn1.click(lambda process=gr.Progress(track_tqdm=True),*args: generate_preprocess(*args, project="bv2"), inputs=[INTERRUPT_EVENT, input_file, fps, offset, workers, *BV2_ARGS], outputs=[audio_output, gen_textbox_output_text, worklist, page_slider, *edit_rows, STATE])
        GSV.gen_btn2.click(lambda process=gr.Progress(track_tqdm=True),*args: generate_preprocess(*args, project="gsv"), inputs=[INTERRUPT_EVENT, input_file, fps, offset, workers, *GSV_ARGS], outputs=[audio_output, gen_textbox_output_text, worklist, page_slider, *edit_rows, STATE])
        MSTTS.gen_btn3.click(lambda process=gr.Progress(track_tqdm=True),*args: generate_preprocess(*args, project="mstts"), inputs=[INTERRUPT_EVENT, input_file, fps, offset, workers, *MSTTS_ARGS], outputs=[audio_output, gen_textbox_output_text, worklist, page_slider, *edit_rows, STATE])
        CUSTOM.gen_btn4.click(lambda process=gr.Progress(track_tqdm=True),*args: generate_preprocess(*args, project="custom"), inputs=[INTERRUPT_EVENT, input_file, fps, offset, workers, CUSTOM.choose_custom_api], outputs=[audio_output, gen_textbox_output_text, worklist, page_slider, *edit_rows, STATE])
        # Stability is not ensured due to the mechanism of gradio.

    app.queue(default_concurrency_limit=Sava_Utils.config.concurrency_count, max_size=2 * Sava_Utils.config.concurrency_count).launch(
        share=args.share,
        server_port=server_port if server_port > 0 else None,
        inbrowser=True,
        server_name='0.0.0.0' if Sava_Utils.config.LAN_access or args.LAN_access else '127.0.0.1',
        show_api=not Sava_Utils.config.server_mode,
    )
