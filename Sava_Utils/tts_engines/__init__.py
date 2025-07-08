from ..base_component import Base_Component
from abc import ABC, abstractmethod
import traceback
from .. import i18n, logger, ext_tab
import gradio as gr


class TTSProjet(Base_Component):

    def __init__(self, name, title=None, config=None):
        self.gen_btn = None
        self.args = []
        super().__init__(name, title, config)

    @abstractmethod
    def api(self, *args, **kwargs):
        raise NotImplementedError

    def arg_filter(self, *args):
        return args

    def before_gen_action(self, *args, **kwargs):
        pass

    def save_action(self, *args, **kwargs):
        return self.api(*args, **kwargs)

    def api_launcher(self) -> None:
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
        # BV2 = bv2.BV2(Sava_Utils.config)
        GSV = gsv.GSV()
        MSTTS = mstts.MSTTS()
        # CUSTOM = custom.Custom(Sava_Utils.config)
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
                logger.error(f"Failed to load TTS-Engine UI: {i.dirname}")
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
