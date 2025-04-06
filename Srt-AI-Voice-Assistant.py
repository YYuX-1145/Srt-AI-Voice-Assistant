import os
import sys
import io


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

# import datetime
import time
import soundfile as sf
import concurrent.futures
from tqdm import tqdm

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

BV2 = Sava_Utils.tts_projects.bv2.BV2(Sava_Utils.config)
GSV = Sava_Utils.tts_projects.gsv.GSV(Sava_Utils.config)
MSTTS = Sava_Utils.tts_projects.mstts.MSTTS(Sava_Utils.config)
CUSTOM = Sava_Utils.tts_projects.custom.Custom(Sava_Utils.config)
TRANSLATION_MODULE = Translation_module(Sava_Utils.config)
Projet_dict = {"bv2": BV2, "gsv": GSV, "mstts": MSTTS, "custom": CUSTOM}
componments = [BV2, GSV, MSTTS, CUSTOM]


def custom_api(text):
    raise i18n('You need to load custom API functions!')


def generate(*args, proj="", in_files=[], fps=30, offset=0, max_workers=1):
    t1 = time.time()
    fps = positive_int(fps)[0]
    if in_files in [None, []]:
        gr.Info(i18n('Please upload the subtitle file!'))
        return (
            None,
            i18n('Please upload the subtitle file!'),
            getworklist(),
            *load_page(Subtitles()),
            Subtitles(),
        )
    if Sava_Utils.config.server_mode and len(in_files) > 1:
        gr.Warning(i18n('The current mode does not allow batch processing!'))
        return (
            None,
            i18n('The current mode does not allow batch processing!'),
            getworklist(),
            *load_page(Subtitles()),
            Subtitles(),
        )
    os.makedirs(os.path.join(current_path, "SAVAdata", "output"), exist_ok=True)
    for in_file in in_files:
        try:
            subtitle_list = read_file(in_file.name, fps, offset)
        except Exception as e:
            what = str(e)
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
        Projet_dict[proj].before_gen_action(*args, config=Sava_Utils.config, notify=False, force=False)
        abs_dir = subtitle_list.get_abs_dir()
        if Sava_Utils.config.server_mode:
            max_workers = 1
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
                                    "dir": abs_dir,
                                    "subtitle": i,
                                },
                            )
                            for i in subtitle_list
                        ],
                    ),
                    total=len(subtitle_list),
                    desc=i18n('Synthesizing single-speaker task'),
                )
            )
        file_list = [i for i in file_list if i is not None]
        if len(file_list) == 0:
            shutil.rmtree(abs_dir)
            if len(in_files) == 1:
                raise gr.Error(i18n('All subtitle syntheses have failed, please check the API service!'))
            else:
                continue
        sr, audio = subtitle_list.audio_join(sr=Sava_Utils.config.output_sr)
        sf.write(os.path.join(current_path, "SAVAdata", "output", f"{os.path.basename(in_file.name)}.wav"), audio, sr)
    t2 = time.time()
    m, s = divmod(t2 - t1, 60)
    use_time = "%02d:%02d" % (m, s)
    return (
        (sr, audio),
        f"{i18n('Done! Time used')}:{use_time}",
        getworklist(),
        *load_page(subtitle_list),
        subtitle_list,
    )


def generate_preprocess(*args, project=None):
    try:
        args, kwargs = Projet_dict[project].arg_filter(*args)
    except Exception as e:
        return None, f"{i18n('An error occurred')}: {str(e)}", getworklist(), *load_page(Subtitles()), Subtitles()
    return generate(*args, **kwargs)


def gen_multispeaker(*args, remake=False):  # page,maxworkers,*args,subtitles
    page = args[0]
    max_workers = int(args[1])
    subtitles: Subtitles = args[-1]
    if len(subtitles) == 0 or subtitles is None:
        gr.Info(i18n('There is no subtitle in the current workspace'))
        return *show_page(page, Subtitles()), None
    for key in list(subtitles.speakers.keys()):
        if subtitles.speakers[key] <= 0:
            subtitles.speakers.pop(key)
    if len(list(subtitles.speakers.keys())) == 0 and subtitles.default_speaker is None and subtitles.proj is None:
        gr.Warning(i18n('Warning: No speaker has been assigned'))
    proj_args = (None, None, *args[:-1])
    if remake:
        todo = [i for i in subtitles if not i.is_success]
    else:
        todo = subtitles
    if len(todo) == 0:
        gr.Info(i18n('No subtitles are going to be resynthesized.'))
        return *show_page(page, subtitles), None
    abs_dir = subtitles.get_abs_dir()
    tasks = {key: [] for key in [*subtitles.speakers.keys(), None]}
    for i in todo:
        tasks[i.speaker].append(i)
    for key in list(tasks.keys()):
        if len(tasks[key]) == 0:
            tasks.pop((key))
    ok = True
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
                logger.error(f"{i18n('Speaker archive not found')}: {spk}")
                gr.Warning(f"{i18n('Speaker archive not found')}: {spk}")
                continue
            args = info["raw_data"]
            project = info["project"]
        try:
            args, kwargs = Projet_dict[project].arg_filter(*args)
            Projet_dict[project].before_gen_action(*args, config=Sava_Utils.config)
        except Exception as e:
            gr.Warning(str(e))
            continue
        if Sava_Utils.config.server_mode:
            max_workers = 1
        progress = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            file_list = list(
                tqdm(
                    executor.map(
                        lambda x: save(x[0], **x[1]),
                        [
                            (
                                args,
                                {
                                    "proj": project,
                                    "dir": abs_dir,
                                    "subtitle": i,
                                },
                            )
                            for i in tasks[key]
                        ],
                    ),
                    total=len(todo),
                    initial=progress,
                    desc=f"{i18n('Synthesizing multi-speaker task, the current speaker is')} :{spk}",
                )
            )
        file_list = [i for i in file_list if i is not None]
        progress += len(file_list)
        if len(file_list) == 0:
            ok = False
            gr.Warning(f"{i18n('Synthesis for the single speaker has failed !')} {spk}")

    gr.Info(i18n('Done!'))
    if remake:
        if ok:
            gr.Info(i18n('Audio re-generation was successful! Click the <Reassemble Audio> button.'))
        return show_page(page, subtitles)
    audio = subtitles.audio_join(sr=Sava_Utils.config.output_sr)
    return *show_page(page, subtitles), audio


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
    page = args[0]
    if int(args[1]) == -1:
        gr.Info("Not available!")
        return fp, *show_page(page, subtitle_list)
    page, idx, s_txt = args[:3]
    if Sava_Utils.config.server_mode and len(s_txt) > 512:
        gr.Warning("too long!")
        return fp, *show_page(page, subtitle_list)
    if subtitle_list[int(idx)].speaker is not None or (subtitle_list.proj is None and subtitle_list.default_speaker is not None):
        spk = subtitle_list[int(idx)].speaker
        if spk is None:
            spk = subtitle_list.default_speaker
        try:
            with open(os.path.join(current_path, "SAVAdata", "speakers", spk), 'rb') as f:
                info = pickle.load(f)
        except FileNotFoundError:
            logger.error(f"{i18n('Speaker archive not found')}: {spk}")
            gr.Warning(f"{i18n('Speaker archive not found')}: {spk}")
            return fp, *show_page(page, subtitle_list)
        args = info["raw_data"]
        proj = info["project"]
        args, kwargs = Projet_dict[proj].arg_filter(*args)
        # Projet_dict[proj].before_gen_action(*args,notify=False,force=True)
    else:
        if subtitle_list.proj is None:
            gr.Info(i18n('You must specify the speakers while using multi-speaker dubbing!'))
            return fp, *show_page(page, subtitle_list)
        args = [None, *args]  # fill data
        try:
            proj = subtitle_list.proj
            args, kwargs = Projet_dict[proj].arg_filter(*args)
        except Exception as e:
            # print(e)
            return fp, *show_page(page, subtitle_list)
    Projet_dict[proj].before_gen_action(*args, config=Sava_Utils.config, notify=False, force=False)
    subtitle_list[int(idx)].text = s_txt
    fp = save(args, proj=proj, dir=subtitle_list.get_abs_dir(), subtitle=subtitle_list[int(idx)])
    if fp is not None:
        gr.Info(i18n('Audio re-generation was successful! Click the <Reassemble Audio> button.'))
    else:
        gr.Warning("Audio re-generation failed!")
    subtitle_list.dump()
    return fp, *show_page(page, subtitle_list)


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
    if args.server_port is None:
        server_port = Sava_Utils.config.server_port
    else:
        server_port = args.server_port
    try:
        speaker_list_choices = ["None", *os.listdir(os.path.join(current_path, "SAVAdata", "speakers"))]
    except:
        speaker_list_choices = ["None"]
    with gr.Blocks(title="Srt-AI-Voice-Assistant-WebUI", theme=Sava_Utils.config.theme) as app:
        STATE = gr.State(value=Subtitles())
        gr.Markdown(value=MANUAL.getInfo("title"))
        with gr.Tabs():
            with gr.TabItem(i18n('Subtitle Dubbing')):
                with gr.Row():
                    with gr.Column():
                        textbox_intput_text = gr.TextArea(label=i18n('File content'), value="", interactive=False)
                        with gr.Accordion(i18n('Speaker Map'), open=False):
                            speaker_map = gr.Dataframe(show_label=False, headers=[i18n('Original Speaker'), i18n('Target Speaker')], datatype=["str", "str"], col_count=(2, 'fixed'), type="numpy", interactive=True)
                            with gr.Row():
                                origin_speaker_list = gr.Dropdown(label=i18n('Select Original Speaker'), value=None, choices=[], allow_custom_value=False)
                                speaker_list0 = gr.Dropdown(label=i18n('Select Target Speaker'), value="None", choices=speaker_list_choices, allow_custom_value=False)
                                speaker_list0.change(modify_spkmap, inputs=[origin_speaker_list, speaker_list0, speaker_map], outputs=[speaker_map])
                            update_spkmap_btn = gr.Button(value=i18n('Identify Original Speakers'))
                        create_multispeaker_btn = gr.Button(value=i18n('Create Multi-Speaker Dubbing Project'))
                    with gr.Column():
                        with gr.TabItem("AR-TTS"):
                            GSV_ARGS = GSV.getUI()
                        with gr.TabItem("Bert-VITS2-HiyoriUI"):
                            BV2_ARGS = BV2.getUI()
                        with gr.TabItem("Azure-TTS(Microsoft)"):
                            MSTTS_ARGS = MSTTS.getUI()
                        with gr.TabItem(i18n('Custom API')):
                            CUSTOM.getUI()
                    with gr.Column():
                        fps = gr.Number(label=i18n('Frame rate of Adobe Premiere project, only applicable to csv files exported from Pr'), value=30, visible=True, interactive=True, minimum=1)
                        workers = gr.Number(label=i18n('Number of threads for sending requests'), value=2, visible=True, interactive=True, minimum=1)
                        offset = gr.Slider(minimum=-6, maximum=6, value=0, step=0.1, label=i18n('Voice time offset (seconds)'))
                        input_file = gr.File(label=i18n('Upload file (Batch mode only supports one speaker at a time)'), file_types=['.csv', '.srt', '.txt'], type="file", file_count='multiple')
                        gen_textbox_output_text = gr.Textbox(label=i18n('Output Info'), interactive=False)
                        audio_output = gr.Audio(label="Output Audio")
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
                        with gr.Row():
                            worklist = gr.Dropdown(
                                choices=os.listdir(os.path.join(current_path, "SAVAdata", "temp", "workspaces")) if os.path.exists(os.path.join(current_path, "SAVAdata", "temp", "workspaces")) else [""],
                                label=i18n('History'),
                                scale=2,
                                visible=not Sava_Utils.config.server_mode,
                            )
                            workrefbtn = gr.Button(value="🔄️", scale=1, min_width=60, visible=not Sava_Utils.config.server_mode)
                            workloadbtn = gr.Button(value=i18n('Load'), scale=1, min_width=60, visible=not Sava_Utils.config.server_mode)
                            page_slider = gr.Slider(minimum=1, maximum=1, value=1, label="", step=Sava_Utils.config.num_edit_rows, scale=4)
                            audio_player = gr.Audio(label="", value=None, interactive=False, autoplay=True, scale=4)
                            recompose_btn = gr.Button(value=i18n('Reassemble Audio'), scale=1, min_width=60)
                            export_btn = gr.Button(value=i18n('Export Subtitles'), scale=1, min_width=60)
                        for x in range(Sava_Utils.config.num_edit_rows):
                            edit_real_index = gr.Number(show_label=False, visible=False, value=-1, interactive=False)  # real index
                            with gr.Row():
                                edit_check = gr.Checkbox(value=False, interactive=True, min_width=40, label="", scale=0)
                                edit_check_list.append(edit_check)
                                edit_rows.append(edit_real_index)  # real index
                                edit_real_index_list.append(edit_real_index)
                                edit_rows.append(gr.Text(scale=1, show_label=False, interactive=False, value='-1', max_lines=1, min_width=40))  # index(raw)
                                edit_start_end_time = gr.Textbox(scale=3, show_label=False, interactive=False, value="NO INFO", max_lines=1)
                                edit_start_end_time_list.append(edit_start_end_time)
                                edit_rows.append(edit_start_end_time)  # start time and end time
                                s_txt = gr.Textbox(scale=6, show_label=False, interactive=False, value="NO INFO", max_lines=1)  # content
                                edit_rows.append(s_txt)
                                edit_rows.append(gr.Textbox(show_label=False, interactive=False, min_width=100, value="None", scale=1, max_lines=1))  # speaker
                                edit_rows.append(gr.Textbox(value="NO INFO", show_label=False, interactive=False, min_width=100, scale=1, max_lines=1))  # is success or delayed?
                                with gr.Row():
                                    __ = gr.Button(value="▶️", scale=1, min_width=60)
                                    __.click(play_audio, inputs=[edit_real_index, STATE], outputs=[audio_player])
                                    bv2regenbtn = gr.Button(value="🔄️", scale=1, min_width=60, visible=False)
                                    edit_rows.append(bv2regenbtn)
                                    bv2regenbtn.click(remake, inputs=[page_slider, edit_real_index, s_txt, *BV2_ARGS, STATE], outputs=[audio_player, *edit_rows])
                                    gsvregenbtn = gr.Button(value="🔄️", scale=1, min_width=60, visible=True)
                                    edit_rows.append(gsvregenbtn)
                                    gsvregenbtn.click(remake, inputs=[page_slider, edit_real_index, s_txt, *GSV_ARGS, STATE], outputs=[audio_player, *edit_rows])
                                    msttsregenbtn = gr.Button(value="🔄️", scale=1, min_width=60, visible=False)
                                    edit_rows.append(msttsregenbtn)
                                    msttsregenbtn.click(remake, inputs=[page_slider, edit_real_index, s_txt, *MSTTS_ARGS, STATE], outputs=[audio_player, *edit_rows])
                                    customregenbtn = gr.Button(value="🔄️", scale=1, min_width=60, visible=False)
                                    edit_rows.append(customregenbtn)
                                    customregenbtn.click(remake, inputs=[page_slider, edit_real_index, s_txt, CUSTOM.choose_custom_api, STATE], outputs=[audio_player, *edit_rows])
                        page_slider.change(show_page, inputs=[page_slider, STATE], outputs=edit_rows)
                        workloadbtn.click(load_work, inputs=[worklist], outputs=[STATE, page_slider, *edit_rows])
                        workrefbtn.click(getworklist, inputs=[], outputs=[worklist])
                        recompose_btn.click(recompose, inputs=[page_slider, STATE], outputs=[audio_output, gen_textbox_output_text, *edit_rows])
                        export_btn.click(lambda x: x.export(), inputs=[STATE], outputs=[input_file])
                        with gr.Row(equal_height=True):
                            all_selection_btn = gr.Button(value=i18n('Select All'), interactive=True, min_width=50)
                            all_selection_btn.click(lambda: [True for i in range(Sava_Utils.config.num_edit_rows)], inputs=[], outputs=edit_check_list)
                            reverse_selection_btn = gr.Button(value=i18n('Reverse Selection'), interactive=True, min_width=50)
                            reverse_selection_btn.click(lambda *args: [not i for i in args], inputs=edit_check_list, outputs=edit_check_list)
                            clear_selection_btn = gr.Button(value=i18n('Clear Selection'), interactive=True, min_width=50)
                            clear_selection_btn.click(lambda: [False for i in range(Sava_Utils.config.num_edit_rows)], inputs=[], outputs=edit_check_list)
                            apply_se_btn = gr.Button(value=i18n('Apply Timestamp modifications'), interactive=True, min_width=50)
                            apply_se_btn.click(apply_start_end_time, inputs=[page_slider, STATE, *edit_real_index_list, *edit_start_end_time_list], outputs=[*edit_rows])
                            copy_btn = gr.Button(value=i18n('Copy'), interactive=True, min_width=50)
                            copy_btn.click(copy_subtitle, inputs=[page_slider, STATE, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, page_slider, *edit_rows])
                            merge_btn = gr.Button(value=i18n('Merge'), interactive=True, min_width=50)
                            merge_btn.click(merge_subtitle, inputs=[page_slider, STATE, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, page_slider, *edit_rows])
                            delete_btn = gr.Button(value=i18n('Delete'), interactive=True, min_width=50)
                            delete_btn.click(delete_subtitle, inputs=[page_slider, STATE, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, page_slider, *edit_rows])
                            all_regen_btn_bv2 = gr.Button(value=i18n('Regenerate All'), variant="primary", visible=False, interactive=True, min_width=50)
                            edit_rows.append(all_regen_btn_bv2)
                            all_regen_btn_gsv = gr.Button(value=i18n('Regenerate All'), variant="primary", visible=True, interactive=True, min_width=50)
                            edit_rows.append(all_regen_btn_gsv)
                            all_regen_btn_mstts = gr.Button(value=i18n('Regenerate All'), variant="primary", visible=False, interactive=True, min_width=50)
                            edit_rows.append(all_regen_btn_mstts)
                            all_regen_btn_custom = gr.Button(value=i18n('Regenerate All'), variant="primary", visible=False, interactive=True, min_width=50)
                            edit_rows.append(all_regen_btn_custom)
                            all_regen_btn_bv2.click(lambda *args: gen_multispeaker(*args, remake=True), inputs=[page_slider, workers, *BV2_ARGS, STATE], outputs=edit_rows)
                            all_regen_btn_gsv.click(lambda *args: gen_multispeaker(*args, remake=True), inputs=[page_slider, workers, *GSV_ARGS, STATE], outputs=edit_rows)
                            all_regen_btn_mstts.click(lambda *args: gen_multispeaker(*args, remake=True), inputs=[page_slider, workers, *MSTTS_ARGS, STATE], outputs=edit_rows)
                            all_regen_btn_custom.click(lambda *args: gen_multispeaker(*args, remake=True), inputs=[page_slider, workers, CUSTOM.choose_custom_api, STATE], outputs=edit_rows)
                        with gr.Accordion(i18n('Find and Replace'), open=False):
                            with gr.Row():
                                find_text_expression = gr.Text(show_label=False, placeholder=i18n('Find What'), scale=3)
                                target_text = gr.Text(show_label=False, placeholder=i18n('Replace With'), scale=3)
                                enable_re = gr.Checkbox(label=i18n('Enable Regular Expression'), min_width=60, scale=1)
                                find_and_replace_btn = gr.Button(value=i18n('Replace All'), variant="primary", min_width=60, scale=1)
                                find_and_replace_btn.click(find_and_replace, inputs=[STATE, find_text_expression, target_text, enable_re], outputs=[page_slider, *edit_rows])
                with gr.Accordion(label=i18n('Multi-speaker dubbing')):
                    with gr.Row(equal_height=True):
                        speaker_list = gr.Dropdown(label=i18n('Select/Create Speaker'), value="None", choices=speaker_list_choices, allow_custom_value=not Sava_Utils.config.server_mode, scale=4)
                        # speaker_list.change(set_default_speaker,inputs=[speaker_list,STATE])
                        select_spk_projet = gr.Dropdown(choices=['bv2', 'gsv', 'mstts', 'custom'], value='gsv', interactive=True, label=i18n('TTS Project'))
                        refresh_spk_list_btn = gr.Button(value="🔄️", min_width=60, scale=0)
                        refresh_spk_list_btn.click(getspklist, inputs=[], outputs=[speaker_list0, speaker_list])
                        apply_btn = gr.Button(value="✅", min_width=60, scale=0)
                        apply_btn.click(apply_spk, inputs=[speaker_list, page_slider, STATE, *edit_check_list, *edit_real_index_list], outputs=[*edit_check_list, *edit_rows])

                        save_spk_btn_bv2 = gr.Button(value="💾", min_width=60, scale=0, visible=False)
                        save_spk_btn_bv2.click(lambda *args: save_spk(*args, project="bv2"), inputs=[speaker_list, *BV2_ARGS], outputs=[speaker_list0, speaker_list])
                        save_spk_btn_gsv = gr.Button(value="💾", min_width=60, scale=0, visible=True)
                        save_spk_btn_gsv.click(lambda *args: save_spk(*args, project="gsv"), inputs=[speaker_list, *GSV_ARGS], outputs=[speaker_list0, speaker_list])
                        save_spk_btn_mstts = gr.Button(value="💾", min_width=60, scale=0, visible=False)
                        save_spk_btn_mstts.click(lambda *args: save_spk(*args, project="mstts"), inputs=[speaker_list, *MSTTS_ARGS], outputs=[speaker_list0, speaker_list])
                        save_spk_btn_custom = gr.Button(value="💾", min_width=60, scale=0, visible=False)
                        save_spk_btn_custom.click(lambda *args: save_spk(*args, project="custom"), inputs=[speaker_list, CUSTOM.choose_custom_api], outputs=[speaker_list0, speaker_list])

                        select_spk_projet.change(switch_spk_proj, inputs=[select_spk_projet], outputs=[save_spk_btn_bv2, save_spk_btn_gsv, save_spk_btn_mstts, save_spk_btn_custom])

                        del_spk_list_btn = gr.Button(value="🗑️", min_width=60, scale=0)
                        del_spk_list_btn.click(del_spk, inputs=[speaker_list], outputs=[speaker_list0, speaker_list])
                        start_gen_multispeaker_btn = gr.Button(value=i18n('Start Multi-speaker Synthesizing'), variant="primary")
                        start_gen_multispeaker_btn.click(gen_multispeaker, inputs=[page_slider, workers, STATE], outputs=edit_rows + [audio_output])
            with gr.TabItem(i18n('Auxiliary Functions')):
                TRANSLATION_MODULE.UI(input_file)
                componments.append(TRANSLATION_MODULE)
            with gr.TabItem(i18n('Extended Contents')):
                available = False
                from Sava_Utils.extern_extensions.wav2srt import WAV2SRT

                WAV2SRT = WAV2SRT(config=Sava_Utils.config)
                componments.append(WAV2SRT)
                available = WAV2SRT.UI(input_file, TRANSLATION_MODULE.translation_upload)
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

        update_spkmap_btn.click(get_speaker_map, inputs=[input_file], outputs=[speaker_map, origin_speaker_list])
        create_multispeaker_btn.click(create_multi_speaker, inputs=[input_file, speaker_map, fps, offset], outputs=[worklist, page_slider, *edit_rows, STATE])
        BV2.gen_btn1.click(lambda *args: generate_preprocess(*args, project="bv2"), inputs=[input_file, fps, offset, workers, *BV2_ARGS], outputs=[audio_output, gen_textbox_output_text, worklist, page_slider, *edit_rows, STATE])
        GSV.gen_btn2.click(lambda *args: generate_preprocess(*args, project="gsv"), inputs=[input_file, fps, offset, workers, *GSV_ARGS], outputs=[audio_output, gen_textbox_output_text, worklist, page_slider, *edit_rows, STATE])
        MSTTS.gen_btn3.click(lambda *args: generate_preprocess(*args, project="mstts"), inputs=[input_file, fps, offset, workers, *MSTTS_ARGS], outputs=[audio_output, gen_textbox_output_text, worklist, page_slider, *edit_rows, STATE])
        CUSTOM.gen_btn4.click(lambda *args: generate_preprocess(*args, project="custom"), inputs=[input_file, fps, offset, workers, CUSTOM.choose_custom_api], outputs=[audio_output, gen_textbox_output_text, worklist, page_slider, *edit_rows, STATE])

    app.queue(concurrency_count=Sava_Utils.config.concurrency_count, max_size=2 * Sava_Utils.config.concurrency_count).launch(
        share=args.share, server_port=server_port if server_port > 0 else None, inbrowser=True, server_name='0.0.0.0' if Sava_Utils.config.LAN_access else '127.0.0.1', show_api=not Sava_Utils.config.server_mode
    )
