import os
import subprocess
import json
import time
import yaml

MAX_P = 3
sava_config = json.load(open("SAVAdata/config.json", encoding="utf-8"))
apath = "api.py" if sava_config['gsv_fallback'] else "api_v2.py"
process_tab = dict()
if __name__ == "__main__":
    os.makedirs('SAVAdata/temp', exist_ok=True)
    count = 0
    for i in [os.path.join('SAVAdata/presets', x) for x in os.listdir('SAVAdata/presets') if os.path.isdir(os.path.join('SAVAdata/presets', x))]:
        preset = json.load(open(os.path.join(i, 'info.json'), encoding="utf-8"))
        gsv_yml = {
            "custom": {
                "device": "cuda",
                "is_half": False,
                "version": "v2",
                "t2s_weights_path": preset["gpt_path"],
                "vits_weights_path": preset["sovits_path"],
                "cnhuhbert_base_path": "GPT_SoVITS/pretrained_models/chinese-hubert-base",
                "bert_base_path": "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large",
            }
        }
        yml_temp_dir = os.path.join('SAVAdata/temp', f'{preset["name"]}.yml')
        with open(yml_temp_dir, 'w') as f:
            yaml.dump(gsv_yml, f)
        # launch api
        if preset["port"] not in process_tab:
            command = f"""
            "{sava_config['gsv_pydir']}" "{os.path.join(sava_config['gsv_dir'],apath)}" -c {os.path.abspath(yml_temp_dir)} -p {preset["port"]}
            """.strip()
            process_tab[preset["port"]] = subprocess.Popen(command, cwd=sava_config['gsv_dir'], shell=True)
            print(f'Run {preset["port"]}')
        count += 1
        if count >= MAX_P:
            break
    print('Launched.')
    while True:
        time.sleep(200)
