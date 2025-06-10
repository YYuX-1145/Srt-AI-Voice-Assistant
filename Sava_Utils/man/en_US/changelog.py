changelog = r"""
## ChangeLog

### V4-2503 Update:
#### To make versions more clear, version are assigned in addition to release dates.
#### After this update, the synthesis history and saved speakers from the previous version need to be recreated; otherwise, errors may occur!
1. Subtitle editing  
2. Subtitle translation  
3. Various details improved and bugs fixed  
4. Supports CosyVoice2 (reusing GSV panel)  
5. (4.0.1) Batch mode  
6. (4.1) Server mode  
7. (4.2) I18n  
8. (4.3) Automatic audio acceleration & silence removing; Creating multi-speaker dubbing project from labeled texts.  
9. (4.3.1) Add Find and Replace; add a one-click regeneration button.  
10. (4.4) Polyphone editing for GPT-SoVITS and automatic model detection; Allow custom prompt for Ollama; Export subtitles with speaker names using customizable templates  
11.(4.5) The translation module now supports merging bilingual subtitles; The audio-video transcription module adds support for the UVR vocal separation model and Video merging.  

### 250214 Update:
1. Supports reading historical projects  
2. Supports multi-speaker dubbing 

### 250123 Update:
1. Supports re-export SRT subtitle files that match the actual start and end timestamps after synthesis; also supports reading TXT text files for synthesis, in which case paragraphs are split by sentences.
2. To enhance expandability in the future and simplicity, the design of a single script file, which makes downloads more convenient, had to be abandoned. The code will be refactored step by step starting from this version.
3. Added some documentations.

### 240811 Update:
1. Notifies users of the error message
2. Automatic detection of TTS-Project envs
3. Compatibility with api-v1 restored
4. A major feature update: Support regenerating specific lines if you're not satisfied with them.
"""
