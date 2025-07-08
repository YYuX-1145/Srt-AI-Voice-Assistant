from ..base_component import Base_Component
from abc import ABC, abstractmethod
import traceback
from .. import i18n, logger, ext_tab
import gradio as gr


class TTSProjet(Base_Component):

    def __init__(self, name, title=None, config=None):
        """
        The name parameter must not be empty for extensions.
        self.gen_btn is a class member representing the generation button, which is not necessary to be defined.
        """
        self.gen_btn = None
        super().__init__(name, title, config)

    @abstractmethod
    def api(self, *args, **kwargs) -> bytes|None:
        """
        Mandatory. Define the API call code here.
        Return value must be binary data of a wav file. If there is an error, return None.
        Please pay attention to the return type. 
        If api returns a path, you can use the following example:
            with open(path, "rb") as f: return f.read()
        """
        raise NotImplementedError

    def arg_filter(self, *args):
        """
        Filters and modifies input arguments. You can raise an exception here when encountering illegal arguments.
        Typical usage: Verify if a file path exists; read audio file binary data from the path
        Must return the modified arguments (even if no changes were made)
        """
        return args

    def before_gen_action(self, *args, **kwargs) -> None:
        """
        Perform preprocessing operations before calling the API
        Typical usage: Switch GSV models, obtain API key for Microsoft TTS 
        """
        pass

    def save_action(self, *args, **kwargs):
        """
        Pass the filtered arguments to the API call method
        """
        return self.api(*args, **kwargs)

    def api_launcher(self) -> None:
        """
        Define button for launching API here.
        Example:
            def start_gsv():
                pass
            start_gsv_btn = gr.Button(value="GPT-SoVITS")
            start_gsv_btn.click(start_gsv)
        """
        pass

    def getUI(self, *args, **kwargs):
        x = super().getUI(*args, **kwargs)
        if self.gen_btn is None:
            self.gen_btn = gr.Button(value=i18n('Generate Audio'), variant="primary", visible=True)
        return x


from . import gsv, mstts
from .. import extension_loader


class TTS_UI_Loader(Base_Component):
    def __init__(self):
        GSV = gsv.GSV()
        MSTTS = mstts.MSTTS()
        self.components: list[TTSProjet] = [GSV, MSTTS]
        self.components += extension_loader.load_ext_from_dir(["Sava_Extensions/tts_engine"], ext_enabled_dict=ext_tab["tts_engine"])
        self.project_dict = {i.name: i for i in self.components}
        super().__init__()

    def _UI(self, *args, **kwargs):
        self.TTS_ARGS = []
        for i in self.components:
            try:
                with gr.TabItem(i.title):
                    self.TTS_ARGS.append(i.getUI())
                    if not hasattr(i, "gen_btn"):
                        setattr(i, "gen_btn", gr.Button(value=i18n('Generate Audio'), variant="primary", visible=True))
            except:
                logger.error(f"{i18n('Failed to load TTS-Engine UI')}: {i.dirname}")
                traceback.print_exc()

    def get_launch_api_btn(self):
        for item in self.components:
            item.api_launcher()

    def get_btn_visible_dict(self):
        BTN_VISIBLE_DICT = {}
        for idx, item in enumerate(self.components):
            BTN_VISIBLE_DICT[item.name] = [gr.update(visible=(idx == j)) for j in range(len(self.components))]
        BTN_VISIBLE_DICT[None] = BTN_VISIBLE_DICT[item.name]
        return BTN_VISIBLE_DICT

    def get_regenbtn(self, inputs, outputs, remake):
        visible = True
        ret = []
        for item, ARGS in zip(self.components, self.TTS_ARGS):
            regenbtn = gr.Button(value="🔄️", scale=1, min_width=50, visible=visible)
            ret.append(regenbtn)
            regenbtn.click(remake, inputs=inputs + ARGS, outputs=outputs)
            visible = False
        return ret

    def get_all_regen_btn(self, inputs, outputs, gen_multispeaker):  # outputs=edit_rows
        visible = True
        for item in self.components:
            all_regen_btn = gr.Button(value=i18n('Continue Generation'), variant="primary", visible=visible, interactive=True, min_width=50)
            outputs.append(all_regen_btn)
            visible = False
        for item, ARGS in zip(outputs[-len(self.components) :], self.TTS_ARGS):
            item.click(lambda process=gr.Progress(track_tqdm=True), *args: gen_multispeaker(*args, remake=True), inputs=inputs + ARGS, outputs=outputs)

    def get_save_spk_btn(self, speaker_dropdown, save_spk):
        def make_handler(project_name):
            return lambda *args, process=gr.Progress(track_tqdm=True): save_spk(*args, project=project_name)

        visible = True
        ret = []
        for item, ARGS in zip(self.components, self.TTS_ARGS):
            save_spk_btn = gr.Button(value="💾", min_width=60, scale=0, visible=visible)
            ret.append(save_spk_btn)
            save_spk_btn.click(make_handler(item.name), [speaker_dropdown] + ARGS, speaker_dropdown)
            visible = False
        return ret

    def activate(self, inputs, outputs, generate_preprocess):
        def make_handler(project_name):
            return lambda *args, process=gr.Progress(track_tqdm=True): generate_preprocess(*args, project=project_name)
            # avoid late binding

        for item, ARGS in zip(self.components, self.TTS_ARGS):
            item.gen_btn.click(make_handler(item.name), inputs=[*inputs, *ARGS], outputs=outputs)
            # Stability is not ensured due to the mechanism of gradio.


TTS_UI_LOADER = TTS_UI_Loader()
