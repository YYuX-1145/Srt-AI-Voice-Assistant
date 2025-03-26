i18n_dict={
    #GSV
    "DICT_LANGUAGE":{
        "Chinese": "all_zh",
        "Cantonese": "all_yue",
        "English": "en",
        "Japanese": "all_ja",
        "Korean": "all_ko",
        "Chinese-English Mix": "zh",
        "Cantonese-English Mix": "yue",
        "Japanese-English Mix": "ja",
        "Korean-English Mix": "ko",
        "Multi-Language Mix": "auto",
        "Multi-Language Mix (Cantonese)": "auto_yue"
    },
    "CUT_METHOD":{
        "No cutting": "cut0",
        "Slice once every 4 sentences": "cut1",
        "Slice per 50 characters": "cut2", 
        "Slice by Chinese punct": "cut3",
        "Slice by English punct": "cut4",
        "Slice by every punct": "cut5"
    },

    #MSTTS
    "MSTTS_NOTICE":"""Microsoft TTS needs Internet Connection. You should fill in your key and specify the server region before gengerating audios. Please pay attention to the monthly free quota.<br>[【To Get Your Key】](https://learn.microsoft.com/en-US/azure/ai-services/speech-service/get-started-text-to-speech)""",

    #Subtitle Translation
    "OLLAMA_NOTICE":"⚠️LLMs use much VRAM while they're running and do not forget to select and unload the corresponding model after usage in order to free up VRAM.",

    #EXTENSIONS

        #WAV2SRT
        "WAV2SRT_INFO":"""
            This function can be directly used in the GPT-SoVITS integrated package; otherwise, you need to install the corresponding dependencies yourself.  

            # Other Parameters:
            `--whisper_size` Default:large-v3 | Specifies the model when using faster whisper.  
            `--threshold` Default:-40 | Volume less than this value is considered as a mute alternative cutting point.  
            `--hop_size` Default:20 | How to calculate the volume curve; the smaller the value, the higher the precision and computation (Note: Higher precision does not always mean better quality).  
            """
}