def register(context):
    globals().update(context)
    from .wav2srt_webui import WAV2SRT
    return WAV2SRT()