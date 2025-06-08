import os
import shutil
import subprocess
from tqdm import tqdm
import librosa
import argparse
import numpy as np
import torch
from tools.slicer2 import Slicer

try:
    from tools.uvr5.mdxnet import MDXNetDereverb
    from tools.uvr5.vr import AudioPre, AudioPreDeEcho
    from tools.uvr5.bsroformer import Roformer_Loader
    UVR5_AVAILABLE = True
except ImportError:
    UVR5_AVAILABLE = False

current_directory = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-input", nargs='+', default=None, type=str)
parser.add_argument("-output_dir", default=None, type=str)
parser.add_argument("-engine", default="whisper", type=str)
parser.add_argument("--uvr_model", default=None, type=str)
parser.add_argument("--whisper_size", default="large-v3-turbo", type=str)
parser.add_argument("--threshold", default=-40, type=float)
parser.add_argument("--min_length", default=2000, type=int)
parser.add_argument("--min_interval", default=300, type=int)
parser.add_argument("--hop_size", default=20, type=int)
parser.add_argument("--max_sil_kept", default=1000, type=int)
args = parser.parse_args()


def basename_no_ext(path: str):
    return os.path.basename(os.path.splitext(path)[0])


def init_ASRmodels():
    global args, model
    if args.engine == "whisper":
        import faster_whisper
        from faster_whisper import WhisperModel
        model_path = f'tools/asr/models/faster-whisper-{args.whisper_size}'
        os.makedirs(model_path, exist_ok=True)
        if os.listdir(model_path) == []:
            print("Downloading faster whisper model...")
            os.makedirs(model_path, exist_ok=True)
            faster_whisper.download_model(size_or_id=args.whisper_size, output_dir=model_path)
        try:
            print("Loading faster whisper model:", model_path)
            model = WhisperModel(model_path, device='cuda')
        except Exception as e:
            print(e)
            print("下载或加载出错。如果不能下载，请前往HF镜像站手动下载faster whisper模型")
        if args.whisper_size == "large-v3":
            model.feature_extractor.mel_filters = model.feature_extractor.get_mel_filters(model.feature_extractor.sampling_rate, model.feature_extractor.n_fft, n_mels=128)
    else:
        from funasr import AutoModel
        print("Loading FunASR models...")
        path_asr = 'tools/asr/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch'
        path_asr = path_asr if os.path.exists(path_asr) else "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
        model_revision = "v2.0.4"
        path_vad = 'tools/asr/models/speech_fsmn_vad_zh-cn-16k-common-pytorch'
        path_punc = 'tools/asr/models/punc_ct-transformer_zh-cn-common-vocab272727-pytorch'
        path_vad = path_vad if os.path.exists(path_vad) else "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
        path_punc = path_punc if os.path.exists(path_punc) else "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
        vad_model_revision = punc_model_revision = "v2.0.4"
        # sync with gsv
        model = AutoModel(
            model=path_asr,
            model_revision=model_revision,
            vad_model=path_vad,
            vad_model_revision=vad_model_revision,
            punc_model=path_punc,
            punc_model_revision=punc_model_revision,
        )


def whisper_transcribe(audio, sr):
    global model
    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    # lang = ['zh', 'ja', 'en']
    try:
        segments, info = model.transcribe(audio=audio.astype(np.float32), beam_size=5, vad_filter=False, language=None)
        text = ""
        # assert info.language in lang
        for seg in segments:
            text += seg.text
        return text
    except Exception as e:
        print(e)


def funasr_transcribe(audio, sr):
    global model
    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    text = model.generate(input=audio)[0]["text"]
    return text


def transcribe(wav_paths, save_root):
    for audio_path in tqdm(wav_paths, desc='Transcribing...'):
        audio, sr = librosa.load(audio_path, sr=None)
        slicer = Slicer(
            sr=sr,
            threshold=int(args.threshold),  # 音量小于这个值视作静音的备选切割点
            min_length=int(args.min_length),  # 每段最小多长，如果第一段太短一直和后面段连起来直到超过这个值
            min_interval=int(args.min_interval),  # 最短切割间隔
            hop_size=int(args.hop_size),  # 怎么算音量曲线，越小精度越大计算量越高（不是精度越大效果越好）
            max_sil_kept=int(args.max_sil_kept),  # 切完后静音最多留多长
        )
        srt = []
        for chunk, start, end in slicer.slice(audio):  # start和end是帧数
            start = start / sr
            end = end / sr
            try:
                if args.engine == "whisper":
                    text = whisper_transcribe(chunk, sr)
                else:
                    text = funasr_transcribe(chunk, sr)
            except Exception as e:
                print(e)
                continue
            srt.append((start, end, text))
        srt_content = []
        idx = 0
        for i in srt:
            idx += 1
            start, end, text = i
            srt_content.append(str(idx) + "\n")
            srt_content.append(f"{to_time(start)} --> {to_time(end)}" + "\n")
            srt_content.append(text + "\n")
            srt_content.append("\n")

        save_path = save_root if save_root is not None else os.path.dirname(audio_path)
        if os.path.basename(audio_path).startswith('vocal_'):
            savename = os.path.join(save_path, f"{basename_no_ext(audio_path)[6:]}.srt")
        else:
            savename = os.path.join(save_path, f"{basename_no_ext(audio_path)}.srt")
        with open(savename, "w", encoding="utf-8") as f:
            f.writelines(srt_content)


def uvr(model_name, input_paths, save_root, agg=10, format0='wav'):
    if not UVR5_AVAILABLE:
        print("UVR5 is not available.")
        return input_paths
    weight_uvr5_root = "tools/uvr5/uvr5_weights"
    try:
        is_hp3 = "HP3" in model_name
        if model_name == "onnx_dereverb_By_FoxJoy":
            pre_fun = MDXNetDereverb(15)
        elif "roformer" in model_name.lower():
            func = Roformer_Loader
            pre_fun = func(
                model_path=os.path.join(weight_uvr5_root, model_name + ".ckpt"),
                config_path=os.path.join(weight_uvr5_root, model_name + ".yaml"),
                device='cuda' if torch.cuda.is_available() else 'cpu',
                is_half=True,
            )
        else:
            func = AudioPre if "DeEcho" not in model_name else AudioPreDeEcho
            pre_fun = func(
                agg=int(agg),
                model_path=os.path.join(weight_uvr5_root, model_name + ".pth"),
                device='cuda' if torch.cuda.is_available() else 'cpu',
                is_half=True,
            )
        ret = []
        for input_path in tqdm(input_paths, desc='Denoising...'):
            save_path = save_root if save_root is not None else os.path.dirname(input_path)
            tmp_path = f"{basename_no_ext(input_path)}_reformatted.wav"
            try:
                assert subprocess.run(f'ffmpeg -i "{input_path}" -vn -acodec pcm_s16le -ac 2 -ar 44100 "{tmp_path}" -y', stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
            except:
                print(f"FFmpeg Error: {input_path}")
                continue
            try:
                pre_fun._path_audio_(tmp_path, save_path, save_path, format0, is_hp3)
                out_p = os.path.join(save_path, f"vocal_{os.path.basename(tmp_path)}_{agg}.wav")
                # (ins/vocal)_audio|_10_reformatted.wav.wav"     17 + 4 + len(agg)
                x = -22 if agg < 10 else -23
                shutil.move(out_p, out_p[:x] + '.wav')
                out_p = os.path.join(save_path, f"instrument_{os.path.basename(tmp_path)}_{agg}.wav")
                shutil.move(out_p, out_p[:x] + '.wav')
                ret.append(os.path.join(save_path, f"vocal_{basename_no_ext(input_path)}.wav"))
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    finally:
        try:
            if model_name == "onnx_dereverb_By_FoxJoy":
                del pre_fun.pred.model
                del pre_fun.pred.model_
            else:
                del pre_fun.model
                del pre_fun
        except Exception as e:
            print(e)
        print("clean_empty_cache")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return ret


def to_time(time_raw: float):
    hours, r = divmod(time_raw, 3600)
    minutes, r = divmod(r, 60)
    seconds, milliseconds = divmod(r, 1)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(milliseconds*1000):03d}"


if __name__ == "__main__":
    if args.input is not None:
        wav_paths = [os.path.abspath(i.strip('"')) for i in args.input]
    else:
        wav_paths = [input("enter input audio path: ").strip('"')]
    print(wav_paths)
    if args.uvr_model not in [None, '', 'None']:
        wav_paths = uvr(args.uvr_model, wav_paths, args.output_dir)
        wav_paths = [i for i in wav_paths if os.path.exists(i)]
    init_ASRmodels()
    transcribe(wav_paths, args.output_dir)
