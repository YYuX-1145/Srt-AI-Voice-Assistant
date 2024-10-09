import faster_whisper
import os 
import librosa
import soundfile as sf
import argparse
from tools.slicer2 import Slicer
from faster_whisper import WhisperModel
from funasr import AutoModel

current_directory = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-input_dir", default=None,type=str)
parser.add_argument("-output_dir",default=current_directory,type=str)
parser.add_argument("-engine",default="whisper",type=str)
parser.add_argument("--whisper_size", default="large-v3",type=str)
parser.add_argument("--threshold",default=-40,type=float)
parser.add_argument("--min_length",default=5000,type=int)
parser.add_argument("--min_interval",default=300,type=int)
parser.add_argument("--hop_size",default=20,type=int)
parser.add_argument("--max_sil_kept", default=1000,type=int)
args = parser.parse_args()


if args.engine=="whisper":
    model_path = f'tools/asr/models/faster-whisper-{args.whisper_size}'
    if os.listdir(model_path)==[]:         
        print("downloading...")
        os.makedirs(model_path,exist_ok=True)
        faster_whisper.download_model(size_or_id=args.whisper_size,output_dir=model_path)    
    try:
        print("loading faster whisper model:",model_path)
        model = WhisperModel(model_path, device='cuda')
    except Exception as e:
        print(e) 
        print("加载或者加载出错。如果不能下载，请前往HF镜像站手动下载faster whisper模型")
    if args.whisper_size=="large-v3":
        model.feature_extractor.mel_filters = model.feature_extractor.get_mel_filters(model.feature_extractor.sampling_rate, model.feature_extractor.n_fft, n_mels=128)
else :
    path_asr = 'tools/asr/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch'
    path_asr = path_asr if os.path.exists(path_asr) else "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
    model_revision="v2.0.4" 
    path_vad = 'tools/asr/models/speech_fsmn_vad_zh-cn-16k-common-pytorch'
    path_punc = 'tools/asr/models/punc_ct-transformer_zh-cn-common-vocab272727-pytorch'
    path_vad = path_vad if os.path.exists(path_vad) else "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
    path_punc = path_punc if os.path.exists(path_punc) else "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
    vad_model_revision=punc_model_revision="v2.0.4"
    #sync with gsv
    model = AutoModel(
        model=path_asr,
        model_revision=model_revision,
        vad_model=path_vad,
        vad_model_revision=vad_model_revision,
        punc_model=path_punc,
        punc_model_revision=punc_model_revision,
    )


def whisper_transcribe(audio,sr):
    audio=librosa.resample(audio,orig_sr=sr,target_sr=16000)
    lang=['zh','ja','en']
    try:
        segments, info = model.transcribe(
            audio          = audio,
            beam_size      = 5,
            vad_filter     = False,
            language       = None)
        text=""
        assert(info.language in lang)
        for seg in segments:
            text+=seg.text
        return text
    except Exception as e:
        print(e)

def funasr_transcribe(audio,sr):
    sf.write("temp.wav",audio,sr)
    text = model.generate(input="temp.wav")[0]["text"]
    os.remove("temp.wav")
    return text

def transcribe(audio_path):
    global model
    audio,sr=librosa.load(audio_path,sr=None)
    slicer=Slicer(
        sr=sr,
        threshold=int(args.threshold),  # 音量小于这个值视作静音的备选切割点
        min_length=int(args.min_length),  # 每段最小多长，如果第一段太短一直和后面段连起来直到超过这个值
        min_interval=  int(args.min_interval),  # 最短切割间隔
        hop_size= int(args.hop_size),  # 怎么算音量曲线，越小精度越大计算量越高（不是精度越大效果越好）
        max_sil_kept=   int(args.max_sil_kept),  # 切完后静音最多留多长
    )
    srt=[]
    for chunk, start, end in slicer.slice(audio):  # start和end是帧数
        start=start/sr
        end=end/sr
        try:
            if args.engine=="whisper":
                text=whisper_transcribe(chunk,sr)
            else:
                text=funasr_transcribe(chunk,sr)
        except Exception as e:
            print(e)
            continue
        srt.append((start,end,text))
    srt_content=[]
    idx=0
    for i in srt:
        idx+=1
        start,end,text=i
        srt_content.append(str(idx)+"\n")
        srt_content.append(f"{to_time(start)} --> {to_time(end)}"+"\n")
        srt_content.append(text+"\n")
        srt_content.append("\n")

    savepath=os.path.join(args.output_dir,"output.srt")
    with open(savepath,"w",encoding="utf-8") as f:
        f.writelines(srt_content)
    os.system(f'explorer /select, {savepath}')
        
def to_time(time_raw:float):
    hours, r = divmod(time_raw,3600)
    minutes, r = divmod(r,60)
    seconds, milliseconds = divmod(r, 1)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(milliseconds*1000):03d}"

if __name__=="__main__":
    if args.input_dir is not None:
        wav_path=args.input_dir.strip('"')
    else:
        wav_path=input("enter input audio path: ").strip('"')
    print(wav_path)
    transcribe(wav_path)
    
