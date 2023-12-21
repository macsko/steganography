from nicegui import app, ui, run
import cv2
import pathlib
import shutil
import random
from multiprocessing import Manager
import time

from alg_wrappers import lsb_basic_hide_wrapper, lsb_basic_reveal_wrapper, lsb_vr_hide_wrapper, lsb_vr_reveal_wrapper, coverless_hide_data_wrapper
from algorithms.coverless import build_block_cache, get_message


IMAGE_FILE_TYPES = ('Image Files (*.png;*.tiff;*.bmp)',)

secret_text_validation = {'Secret text too long': lambda value: len(value) <= 100}
im_filename_validation = {"Invalid file type, allowed: .png, .tiff, .bmp": lambda value: any(value.endswith(t) for t in (".png", ".tiff", ".bmp")) or not value}

def im_filename_validation_func(filename):
    return all(validate(filename) for _, validate in im_filename_validation.items())

def read_im(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

def write_im(path, im):
    cv2.imwrite(path, cv2.cvtColor(im, cv2.COLOR_BGR2RGB))

def set_im_ui(im_ui, im):
    tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
    write_im(tmp_png_im_path, im)
    im_ui.set_source(tmp_png_im_path)
    im_ui.update()

async def get_file(callback, file_types=None):
    if file_types == None:
        file_types = ()
    files = await app.native.main_window.create_file_dialog(allow_multiple=False, file_types=file_types)
    if files is not None and len(files) > 0:
        callback(files[0])

# TODOS:
# Add descriptions and help
# Set appropriate window sizing
# Add borders around images?
# concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly while the future was running or pending.

ui.image.default_classes("w-64 h-64")
ui.button.default_classes("w-64")
ui.input.default_classes("w-64")
ui.textarea.default_classes("w-64")

class LSBHideAlg:
    def __init__(self, hide_alg, opts_class):
        self.cover_im = None
        self.secret_im = None
        self.generated_im = None
        self.hide_alg = hide_alg
        self.computing = False
        
        with ui.row().classes('w-full justify-center'):
            with ui.column():
                ui.button('choose cover image', on_click=self.choose_cover_im)
                self.cover_im_ui = ui.image("")
                self.opts = opts_class()
            with ui.column():
                ui.button('choose secret image', on_click=self.choose_secret_im)
                self.secret_im_ui = ui.image("")
            with ui.column():
                self.generate_btn_ui = ui.button('generate stego image', on_click=self.generate_stego_image)
                    # bind_enabled_from(self, "generate_btn_state")
                self.generated_im_ui = ui.image("")
                self.progressbar_ui = ui.linear_progress(show_value=False).props('instant-feedback query'). \
                    bind_visibility_from(self, "computing")
                self.filename_ui = ui.input(label='Result filename', validation=im_filename_validation, on_change=self.update_save_btn). \
                    props('outlined')
                self.save_btn_ui = ui.button('save stego image', on_click=self.save_image)
                    # bind_enabled_from(self, "save_btn_state")

    # @property
    # def save_btn_state(self):
    #     return self.generated_im is not None and not self.computing and \
    #         len(self.filename_ui.value) > 0 and im_filename_validation_func(self.filename_ui.value)

    # @property
    # def generate_btn_state(self):
    #     return self.cover_im is not None and self.secret_im is not None and not self.computing
    
    def update_save_btn(self):
        enabled = self.generated_im is not None and not self.computing and \
            len(self.filename_ui.value) > 0 and im_filename_validation_func(self.filename_ui.value)
        self.save_btn_ui.set_enabled(enabled)
        self.save_btn_ui.update()
    
    def udpate_generate_btn(self):
        enabled = self.cover_im is not None and self.secret_im is not None and not self.computing
        self.generate_btn_ui.set_enabled(enabled)
        self.generate_btn_ui.update()
    
    def set_cover_im(self, im_path):
        self.cover_im = read_im(im_path)
        set_im_ui(self.cover_im_ui, self.cover_im)
        self.udpate_generate_btn()
    
    def set_secret_im(self, im_path):
        self.secret_im = read_im(im_path)
        set_im_ui(self.secret_im_ui, self.secret_im)
        self.udpate_generate_btn()

    async def choose_cover_im(self):
        await get_file(self.set_cover_im, file_types=IMAGE_FILE_TYPES)

    async def choose_secret_im(self):
        await get_file(self.set_secret_im, file_types=IMAGE_FILE_TYPES)

    async def save_image(self):
        write_im(self.filename_ui.value, self.generated_im)
        pathlib.Path(self.tmp_im_path).unlink(missing_ok=True)
        ui.notify(f"Saved image to {self.filename_ui.value}")
    
    def set_generated_im(self, im):
        self.tmp_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.tiff"
        write_im(self.tmp_im_path, im)
        self.generated_im = im
        set_im_ui(self.generated_im_ui, self.generated_im)
        self.update_save_btn()
    
    def clear_generated_im(self):
        self.generated_im_ui.set_source("")
        self.generated_im_ui.update()
    
    async def generate_stego_image(self):
        self.computing = True
        self.update_save_btn()
        self.udpate_generate_btn()
        self.clear_generated_im()
        result_im = await run.cpu_bound(self.hide_alg, self.cover_im, self.secret_im, **self.opts.get_args())
        self.set_generated_im(result_im)
        self.computing = False
        self.update_save_btn()
        self.udpate_generate_btn()


class LSBRevealAlg:
    def __init__(self, reveal_alg, opts_class):
        self.stego_im = None
        self.revealed_im = None
        self.reveal_alg = reveal_alg
        self.computing = False
        
        with ui.row().classes('w-full justify-center'):
            with ui.column():
                ui.button('choose stego image', on_click=self.choose_stego_im)
                self.stego_im_ui = ui.image("")
                self.opts = opts_class()
            with ui.column():
                self.reveal_btn_ui = ui.button('reveal secret image', on_click=self.reveal_secret_image). \
                    bind_enabled_from(self, "reveal_btn_state")
                self.revealed_im_ui = ui.image("")
                self.progressbar_ui = ui.linear_progress(show_value=False).props('instant-feedback query'). \
                    bind_visibility_from(self, "computing")
                self.filename_ui = ui.input(label='Result filename', validation=im_filename_validation). \
                    props('outlined')
                self.save_btn_ui = ui.button('save revealed image', on_click=self.save_image). \
                    bind_enabled_from(self, "save_btn_state")
    
    @property
    def save_btn_state(self):
        return self.revealed_im is not None and not self.computing and \
            len(self.filename_ui.value) > 0 and im_filename_validation_func(self.filename_ui.value)

    @property
    def reveal_btn_state(self):
        return self.stego_im is not None and not self.computing
    
    def set_stego_im(self, im_path):
        self.stego_im = read_im(im_path)
        set_im_ui(self.stego_im_ui, self.stego_im)
    
    async def choose_stego_im(self):
        await get_file(self.set_stego_im, file_types=IMAGE_FILE_TYPES)

    async def save_image(self):
        write_im(self.filename_ui.value, self.revealed_im)
        pathlib.Path(self.tmp_im_path).unlink(missing_ok=True)
        ui.notify(f"Saved image to {self.filename_ui.value}")
    
    def set_revealed_im(self, im):
        self.tmp_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.tiff"
        write_im(self.tmp_im_path, im)
        self.revealed_im = im
        set_im_ui(self.revealed_im_ui, self.revealed_im)
    
    def clear_revealed_im(self):
        self.revealed_im_ui.set_source("")
        self.revealed_im_ui.update()

    async def reveal_secret_image(self):
        self.computing = True
        self.clear_revealed_im()
        result_im = await run.cpu_bound(self.reveal_alg, self.stego_im, **self.opts.get_args())
        self.set_revealed_im(result_im)
        self.computing = False


class CoverlessHideAlg:
    def __init__(self):
        self.cover_im = None
        self.blocks_dir = None
        self.generated_im = None
        self.blocks_computing = False
        self.cache_progress_queue = Manager().Queue()
        self.blocks_cache = None
        self.computing = False
        self.progress_queue = Manager().Queue()
        
        with ui.row().classes('w-full justify-center'):
            with ui.column():
                ui.button('choose cover image', on_click=self.choose_cover_im)
                self.cover_im_ui = ui.image("")
                ui.button('choose blocks directory', on_click=self.choose_blocks_dir). \
                    bind_enabled_from(self, "choose_blocks_btn_state")
                self.cache_progressbar_ui = ui.linear_progress(value=0, show_value=False).props('instant-feedback'). \
                    bind_value_from(self, "cache_progress_bar_state")
                self.chosen_blocks_dir_label_ui = ui.textarea(label='Selected blocks directory'). \
                    props('outlined readonly autogrow').bind_value_from(self, "blocks_dir")
            with ui.column():
                ui.button('load secret text', on_click=self.choose_secret_text_file)
                self.secret_text_ui = ui.textarea(label='Secret text', validation=secret_text_validation). \
                    props('outlined autogrow')
            with ui.column():
                self.generate_btn_ui = ui.button('generate stego image', on_click=self.generate_stego_image). \
                    bind_enabled_from(self, "generate_btn_state")
                self.generated_im_ui = ui.image("")
                self.progressbar_ui = ui.linear_progress(value=0, show_value=False).props('instant-feedback'). \
                    bind_value_from(self, "progress_bar_state")
                self.filename_ui = ui.input(label='Result filename', validation=im_filename_validation). \
                    props('outlined')
                self.save_btn_ui = ui.button('save stego image', on_click=self.save_image). \
                    bind_enabled_from(self, "save_btn_state")
    
    @property
    def cache_progress_bar_state(self):
        if self.blocks_computing:
            return self.cache_progress_queue.get() if not self.cache_progress_queue.empty() else self.cache_progressbar_ui.value
        return 1 if self.blocks_cache else 0
    
    @property
    def progress_bar_state(self):
        if self.computing:
            return self.progress_queue.get() if not self.progress_queue.empty() else self.progressbar_ui.value
        return 1 if self.generated_im is not None else 0

    @property
    def choose_blocks_btn_state(self):
        return not self.blocks_computing
    
    @property
    def save_btn_state(self):
        return self.generated_im is not None and not self.computing and \
            len(self.filename_ui.value) > 0 and im_filename_validation_func(self.filename_ui.value)

    @property
    def generate_btn_state(self):
        return self.cover_im is not None and self.blocks_cache is not None and not self.computing and \
            len(self.secret_text_ui.value) > 0 and not self.blocks_computing
    
    def set_cover_im(self, im_path):
        self.cover_im = read_im(im_path)
        set_im_ui(self.cover_im_ui, self.cover_im)
    
    def set_secret_text_file(self, text_path):
        with open(text_path, "r") as f:
            self.secret_text_ui.set_value(f.read()[:100])
            self.secret_text_ui.update()
    
    def set_blocks_dir(self, dir_path):
        self.blocks_dir = dir_path

    async def choose_cover_im(self):
        await get_file(self.set_cover_im, file_types=IMAGE_FILE_TYPES)

    async def choose_blocks_dir(self):
        await get_file(lambda f: self.set_blocks_dir(str(pathlib.Path(f).parent)))
        self.blocks_computing = True
        blocks_dir_filenames = [str(f) for f in pathlib.Path(self.blocks_dir).iterdir() if f.is_file()]
        self.blocks_cache = await run.cpu_bound(build_block_cache, blocks_dir_filenames, self.cache_progress_queue)
        self.blocks_computing = False
    
    async def choose_secret_text_file(self):
        await get_file(self.set_secret_text_file)

    async def save_image(self):
        write_im(self.filename_ui.value, self.generated_im)
        pathlib.Path(self.tmp_im_path).unlink(missing_ok=True)
        ui.notify(f"Saved image to {self.filename_ui.value}")

    def set_generated_im(self, im):
        self.tmp_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.tiff"
        write_im(self.tmp_im_path, im)
        self.generated_im = im
        set_im_ui(self.generated_im_ui, self.generated_im)
    
    def clear_generated_im(self):
        self.generated_im_ui.set_source("")
        self.generated_im_ui.update()
    
    async def generate_stego_image(self):
        self.computing = True
        self.clear_generated_im()
        self.generate_btn_ui.disable()
        self.generate_btn_ui.update()
        result_im = await run.cpu_bound(coverless_hide_data_wrapper, self.cover_im, self.secret_text_ui.value + "\0", self.blocks_cache, self.progress_queue)
        self.set_generated_im(result_im)
        self.computing = False


class CoverlessRevealAlg:
    def __init__(self):
        self.stego_im = None
        self.revealed_text = ""
        self.computing = False
        
        with ui.row().classes('w-full justify-center'):
            with ui.column():
                ui.button('choose stego image', on_click=self.choose_stego_im)
                self.stego_im_ui = ui.image("")
            with ui.column():
                self.reveal_btn_ui = ui.button('reveal secret text', on_click=self.reveal_secret_text). \
                    bind_enabled_from(self, "reveal_btn_state")
                self.revealed_text_ui = ui.textarea(label='Result').props('outlined readonly autogrow'). \
                    classes("h-64").bind_value_from(self, "revealed_text")
                self.progressbar_ui = ui.linear_progress(show_value=False).props('instant-feedback query'). \
                    bind_visibility_from(self, "computing")
                self.filename_ui = ui.input(label='Result filename').props('outlined')
                self.save_btn_ui = ui.button('save revealed text', on_click=self.save_revealed_text). \
                    bind_enabled_from(self, "save_btn_state")
    
    @property
    def save_btn_state(self):
        return len(self.revealed_text) > 0 and not self.computing and len(self.filename_ui.value) > 0
    
    @property
    def reveal_btn_state(self):
        return self.stego_im is not None and not self.computing
    
    def set_stego_im(self, im_path):
        self.stego_im = read_im(im_path)
        set_im_ui(self.stego_im_ui, self.stego_im)
    
    async def choose_stego_im(self):
        await get_file(self.set_stego_im, file_types=IMAGE_FILE_TYPES)
    
    async def save_revealed_text(self):
        with open(self.filename_ui.value, "w") as f:
            f.write(self.revealed_text)
            ui.notify(f"Saved text to {self.filename_ui.value}")
    
    async def reveal_secret_text(self):
        self.computing = True
        self.revealed_text = ""
        result_text = await run.cpu_bound(get_message, self.stego_im)
        self.revealed_text = result_text[:result_text.index("\\x00")]
        self.computing = False

        
class BasicLSBOptions:
    def __init__(self):
        with ui.element('div').classes('border rounded-md border-gray-300'):
            ui.label('Color proportions:').classes("mt-2 ml-2 mr-2")
            with ui.row().classes("w-64 justify-center"):
                self.r_ui = ui.number(label='R', value=4, min=0, max=8, precision=0).classes("w-8")
                self.g_ui = ui.number(label='G', value=4, min=0, max=8, precision=0).classes("w-8")
                self.b_ui = ui.number(label='B', value=4, min=0, max=8, precision=0).classes("w-8")
    
    def get_args(self):
        return {"color_proportion": (int(self.r_ui.value), int(self.g_ui.value), int(self.b_ui.value))}


class VRLSBOptions:
    def __init__(self):
        with ui.element('div').classes('border rounded-md border-gray-300'):
            ui.label('Parameters:').classes("mt-2 ml-2 mr-2")
            with ui.row().classes("w-64 justify-center"):
                self.alpha_ui = ui.number(label='Alpha', value=9, min=-1, max=255, precision=0).classes("w-12")
                self.max_p_ui = ui.number(label='Max bits', value=4, min=1, max=8, precision=0).classes("w-12")
    
    def get_args(self):
        return {"alpha": int(self.alpha_ui.value), "max_p": int(self.max_p_ui.value)}


@ui.page('/')
def main_page():
    with ui.tabs().classes('w-full') as tabs:
        one = ui.tab('Basic LSB')
        two = ui.tab('Variable rate LSB')
        three = ui.tab('Coverless')

    with ui.tabs().classes('w-full') as tabs_mode:
        hide = ui.tab('Hide')
        reveal = ui.tab('Reveal')

    with ui.tab_panels(tabs, value=one).classes('w-full'):
        with ui.tab_panel(one):
            with ui.tab_panels(tabs_mode, value=hide).classes('w-full'):
                with ui.tab_panel(hide):
                    LSBHideAlg(lsb_basic_hide_wrapper, BasicLSBOptions)
                with ui.tab_panel(reveal):
                    LSBRevealAlg(lsb_basic_reveal_wrapper, BasicLSBOptions)
        with ui.tab_panel(two):
            with ui.tab_panels(tabs_mode, value=hide).classes('w-full'):
                with ui.tab_panel(hide):
                    LSBHideAlg(lsb_vr_hide_wrapper, VRLSBOptions)
                with ui.tab_panel(reveal):
                    LSBRevealAlg(lsb_vr_reveal_wrapper, VRLSBOptions)
        with ui.tab_panel(three):
            with ui.tab_panels(tabs_mode, value=hide).classes('w-full'):
                with ui.tab_panel(hide):
                    CoverlessHideAlg()
                with ui.tab_panel(reveal):
                    CoverlessRevealAlg()
    
    ui.button('Help', on_click=lambda: ui.open('/help')).classes(remove="w-64")


@ui.page('/help')
def help_page():
    ui.button('Go back', on_click=lambda: ui.open('/')).classes(remove="w-64")
    ui.label('Help tab')

    with ui.tabs().classes('w-full'):
        ui.tab('Basic LSB')
        ui.tab('Variable rate LSB')
        ui.tab('Coverless')

    with ui.tabs().classes('w-full'):
        ui.tab('Hide')
        ui.tab('Reveal')

    
def on_startup():
    pathlib.Path("tmp/").mkdir(parents=True, exist_ok=True)

def on_shutdown():
    shutil.rmtree('tmp/', ignore_errors=True)

app.on_startup(on_startup)
app.on_shutdown(on_shutdown)

ui.run(native=True, window_size=(1000, 750))
