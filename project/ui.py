from nicegui import app, ui
import cv2
import pathlib
import shutil
import random
from algorithms.basic_lsb import lsb_basic_hide, lsb_basic_reveal
from algorithms.variable_rate_lsb import lsb_vr_count_available_bits, lsb_vr_hide, lsb_vr_reveal
from algorithms.coverless import build_block_cache, hide_data, get_message

def read_im(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

def write_im(path, im):
    cv2.imwrite(path, cv2.cvtColor(im, cv2.COLOR_BGR2RGB))

def lsb_basic_hide_wrapper(im1, im2, color_proportion):
    bit_fraction_used = sum(color_proportion)/24
    new_x, new_y = int(im1.shape[0] * bit_fraction_used), int(im1.shape[1] * bit_fraction_used)
    if new_x < im2.shape[0] or new_y < im2.shape[0]:
        im2 = cv2.resize(im2.copy(), (new_x, new_y))

    return lsb_basic_hide(im1, im2, color_proportion)

def lsb_basic_reveal_wrapper(im, color_proportion):
    bit_fraction_used = sum(color_proportion)/24
    hidden_shape = int(im.shape[0] * bit_fraction_used), int(im.shape[1] * bit_fraction_used), im.shape[2]

    return lsb_basic_reveal(im, hidden_shape, color_proportion)

def lsb_vr_hide_wrapper(im1, im2, alpha, max_p):
    bit_fraction_used = lsb_vr_count_available_bits(im1, alpha, max_p) / (im1.shape[0] * im1.shape[1] * im1.shape[2] * 8)
    new_x, new_y = int(im1.shape[0] * bit_fraction_used), int(im1.shape[1] * bit_fraction_used)
    if new_x < im2.shape[0] or new_y < im2.shape[0]:
        im2 = cv2.resize(im2.copy(), (new_x, new_y))

    return lsb_vr_hide(im1, im2, alpha, max_p)

def lsb_vr_reveal_wrapper(im, alpha, max_p):
    bit_fraction_used = lsb_vr_count_available_bits(im, alpha, max_p) / (im.shape[0] * im.shape[1] * im.shape[2] * 8)
    hidden_shape = int(im.shape[0] * bit_fraction_used), int(im.shape[1] * bit_fraction_used), im.shape[2]

    return lsb_vr_reveal(im, hidden_shape, alpha, max_p)

# TODOS:
# Allow only for certain file types in file dialog - find what file type names to use
# Add descriptions and help
# Set appropriate window sizing
# Update coverless generate button based on textfield input


class LSBHideAlg:
    def __init__(self, hide_alg, opts_class):
        self.cover_im = None
        self.secret_im = None
        self.generated_im = None
        self.hide_alg = hide_alg
        
        with ui.row().classes('w-full justify-center'):
            with ui.column():
                ui.button('choose cover image', on_click=self.choose_cover_im).classes("w-64")
                self.cover_im_ui = ui.image("").classes("w-64 h-64")
                self.opts = opts_class()
            with ui.column():
                ui.button('choose secret image', on_click=self.choose_secret_im).classes("w-64")
                self.secret_im_ui = ui.image("").classes("w-64 h-64")
            with ui.column():
                self.generate_btn_ui = ui.button('generate stego image', on_click=self.generate_stego_image).classes("w-64")
                self.generate_btn_ui.disable()
                self.generated_im_ui = ui.image("").classes("w-64 h-64")
                self.filename_ui = ui.input(label='Result filename').props('outlined').classes("w-64")
                self.save_btn_ui = ui.button('save stego image', on_click=self.save_image).classes("w-64")
                self.save_btn_ui.disable()
    
    def set_cover_im(self, im_path):
        self.cover_im = read_im(im_path)
        tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
        write_im(tmp_png_im_path, self.cover_im)
        self.cover_im_ui.set_source(tmp_png_im_path)
        self.cover_im_ui.update()
        if self.secret_im is not None:
            self.enable_generate_btn()
    
    def set_secret_im(self, im_path):
        self.secret_im = read_im(im_path)
        tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
        write_im(tmp_png_im_path, self.secret_im)
        self.secret_im_ui.set_source(tmp_png_im_path)
        self.secret_im_ui.update()
        if self.cover_im is not None:
            self.enable_generate_btn()
    
    def set_generated_im(self, im):
        self.tmp_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.tiff"
        write_im(self.tmp_im_path, im)
        self.generated_im = im
        tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
        write_im(tmp_png_im_path, self.generated_im)
        self.generated_im_ui.set_source(tmp_png_im_path)
        self.generated_im_ui.update()
    
    def enable_save_btn(self):
        self.save_btn_ui.enable()
        self.save_btn_ui.update()
    
    def enable_generate_btn(self):
        self.generate_btn_ui.enable()
        self.generate_btn_ui.update()
    
    async def choose_cover_im(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False)
        if files is not None and len(files) > 0:
            self.set_cover_im(files[0])

    async def choose_secret_im(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False)
        if files is not None and len(files) > 0:
            self.set_secret_im(files[0])

    async def save_image(self):
        write_im(self.filename_ui.value, self.generated_im)
        pathlib.Path(self.tmp_im_path).unlink(missing_ok=True)
        ui.notify(f"Saved image to {self.filename_ui.value}")

    async def generate_stego_image(self):
        result_im = self.hide_alg(self.cover_im, self.secret_im, **self.opts.get_args())
        self.set_generated_im(result_im)
        self.enable_save_btn()


class LSBRevealAlg:
    def __init__(self, reveal_alg, opts_class):
        self.stego_im = None
        self.revealed_im = None
        self.reveal_alg = reveal_alg
        
        with ui.row().classes('w-full justify-center'):
            with ui.column():
                ui.button('choose stego image', on_click=self.choose_stego_im).classes("w-64")
                self.stego_im_ui = ui.image("").classes("w-64 h-64")
                self.opts = opts_class()
            with ui.column():
                self.reveal_btn_ui = ui.button('reveal secret image', on_click=self.reveal_secret_image).classes("w-64")
                self.reveal_btn_ui.disable()
                self.revealed_im_ui = ui.image("").classes("w-64 h-64")
                self.filename_ui = ui.input(label='Result filename').props('outlined').classes("w-64")
                self.save_btn_ui = ui.button('save revealed image', on_click=self.save_image).classes("w-64")
                self.save_btn_ui.disable()
    
    def set_stego_im(self, im_path):
        self.stego_im = read_im(im_path)
        tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
        write_im(tmp_png_im_path, self.stego_im)
        self.stego_im_ui.set_source(tmp_png_im_path)
        self.stego_im_ui.update()
        self.enable_reveal_btn()
    
    def set_revealed_im(self, im):
        self.tmp_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.tiff"
        write_im(self.tmp_im_path, im)
        self.revealed_im = im
        tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
        write_im(tmp_png_im_path, self.revealed_im)
        self.revealed_im_ui.set_source(tmp_png_im_path)
        self.revealed_im_ui.update()
    
    def enable_save_btn(self):
        self.save_btn_ui.enable()
        self.save_btn_ui.update()
    
    def enable_reveal_btn(self):
        self.reveal_btn_ui.enable()
        self.reveal_btn_ui.update()
    
    async def choose_stego_im(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False)
        if files is not None and len(files) > 0:
            self.set_stego_im(files[0])

    async def save_image(self):
        write_im(self.filename_ui.value, self.revealed_im)
        pathlib.Path(self.tmp_im_path).unlink(missing_ok=True)
        ui.notify(f"Saved image to {self.filename_ui.value}")

    async def reveal_secret_image(self):
        result_im = self.reveal_alg(self.stego_im, **self.opts.get_args())
        self.set_revealed_im(result_im)
        self.enable_save_btn()


class CoverlessHideAlg:
    def __init__(self):
        self.cover_im = None
        self.blocks_dir = None
        self.generated_im = None
        self.max_secret_text_chars = 100
        
        with ui.row().classes('w-full justify-center'):
            with ui.column():
                ui.button('choose cover image', on_click=self.choose_cover_im).classes("w-64")
                self.cover_im_ui = ui.image("").classes("w-64 h-64")
                ui.button('choose blocks directory', on_click=self.choose_blocks_dir).classes("w-64")
                self.chosen_blocks_dir_label_ui = ui.textarea(label='Selected blocks directory').props('outlined readonly autogrow').classes("w-64")
            with ui.column():
                ui.button('load secret text', on_click=self.choose_secret_text_file).classes("w-64")
                self.secret_text_ui = ui.textarea(label='Secret text', validation={'Secret text too long': lambda value: len(value) <= self.max_secret_text_chars}).props('outlined autogrow').classes("w-64")
            with ui.column():
                self.generate_btn_ui = ui.button('generate stego image', on_click=self.generate_stego_image).classes("w-64")
                self.generate_btn_ui.disable()
                self.generated_im_ui = ui.image("").classes("w-64 h-64")
                self.filename_ui = ui.input(label='Result filename').props('outlined').classes("w-64")
                self.save_btn_ui = ui.button('save stego image', on_click=self.save_image).classes("w-64")
                self.save_btn_ui.disable()

    def set_cover_im(self, im_path):
        self.cover_im = read_im(im_path)
        tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
        write_im(tmp_png_im_path, self.cover_im)
        self.cover_im_ui.set_source(tmp_png_im_path)
        self.cover_im_ui.update()
        if self.blocks_dir is not None:
            self.enable_generate_btn()
    
    def set_blocks_dir(self, dir_path):
        self.blocks_dir = dir_path
        self.set_blocks_dir_text()
        if self.cover_im is not None:
            self.enable_generate_btn()
    
    def set_secret_text_file(self, text_path):
        with open(text_path, "r") as f:
            self.secret_text_ui.set_value(f.read()[:self.max_secret_text_chars])
            self.secret_text_ui.update()
    
    def set_generated_im(self, im):
        self.tmp_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.tiff"
        write_im(self.tmp_im_path, im)
        self.generated_im = im
        tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
        write_im(tmp_png_im_path, self.generated_im)
        self.generated_im_ui.set_source(tmp_png_im_path)
        self.generated_im_ui.update()
    
    def enable_save_btn(self):
        self.save_btn_ui.enable()
        self.save_btn_ui.update()
    
    def enable_generate_btn(self):
        self.generate_btn_ui.enable()
        self.generate_btn_ui.update()
        
    def set_blocks_dir_text(self):
        self.chosen_blocks_dir_label_ui.set_value(self.blocks_dir)
        self.chosen_blocks_dir_label_ui.update()
    
    async def choose_cover_im(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False)
        if files is not None and len(files) > 0:
            self.set_cover_im(files[0])

    async def choose_blocks_dir(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False)
        if files is not None and len(files) > 0:
            self.set_blocks_dir(str(pathlib.Path(files[0]).parent))
    
    async def choose_secret_text_file(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False)
        if files is not None and len(files) > 0:
            self.set_secret_text_file(files[0])

    async def save_image(self):
        write_im(self.filename_ui.value, self.generated_im)
        pathlib.Path(self.tmp_im_path).unlink(missing_ok=True)
        ui.notify(f"Saved image to {self.filename_ui.value}")

    async def generate_stego_image(self):
        blocks_dir_filenames = [str(f) for f in pathlib.Path(self.blocks_dir).iterdir() if f.is_file()]
        cache = build_block_cache(blocks_dir_filenames)
        result_im = self.cover_im.copy()
        hide_data(result_im, self.secret_text_ui.value + "\0", cache)
        self.set_generated_im(result_im)
        self.enable_save_btn()


class CoverlessRevealAlg:
    def __init__(self):
        self.stego_im = None
        self.revealed_text = None
        
        with ui.row().classes('w-full justify-center'):
            with ui.column():
                ui.button('choose stego image', on_click=self.choose_stego_im).classes("w-64")
                self.stego_im_ui = ui.image("").classes("w-64 h-64")
            with ui.column():
                self.reveal_btn_ui = ui.button('reveal secret text', on_click=self.reveal_secret_text).classes("w-64")
                self.reveal_btn_ui.disable()
                self.revealed_text_ui = ui.textarea(label='Result').props('outlined readonly autogrow').classes("w-64 h-64")
                self.filename_ui = ui.input(label='Result filename').props('outlined').classes("w-64")
                self.save_btn_ui = ui.button('save revealed text', on_click=self.save_revealed_text).classes("w-64")
                self.save_btn_ui.disable()
    
    def set_stego_im(self, im_path):
        self.stego_im = read_im(im_path)
        tmp_png_im_path = f"tmp/tmp_im_{random.randint(0, 100000)}.png"
        write_im(tmp_png_im_path, self.stego_im)
        self.stego_im_ui.set_source(tmp_png_im_path)
        self.stego_im_ui.update()
        self.enable_reveal_btn()
    
    def set_revealed_text(self, text):
        self.revealed_text = text
        self.revealed_text_ui.set_value(text)
        self.revealed_text_ui.update()
    
    def enable_save_btn(self):
        self.save_btn_ui.enable()
        self.save_btn_ui.update()
    
    def enable_reveal_btn(self):
        self.reveal_btn_ui.enable()
        self.reveal_btn_ui.update()
    
    async def choose_stego_im(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False)
        if files is not None and len(files) > 0:
            self.set_stego_im(files[0])
    
    async def save_revealed_text(self):
        with open(self.filename_ui.value, "w") as f:
            f.write(self.revealed_text)
            ui.notify(f"Saved text to {self.filename_ui.value}")

    async def reveal_secret_text(self):
        result_text = get_message(self.stego_im)
        self.set_revealed_text(result_text[:result_text.index("\\x00")])
        self.enable_save_btn()

        
class BasicLSBOptions:
    def __init__(self):
        ui.label('Color proportions:')
        with ui.row().classes("w-64 justify-center"):
            self.r_ui = ui.number(label='R', value=4, min=0, max=8, precision=0).classes("w-8")
            self.g_ui = ui.number(label='G', value=4, min=0, max=8, precision=0).classes("w-8")
            self.b_ui = ui.number(label='B', value=4, min=0, max=8, precision=0).classes("w-8")
    
    def get_args(self):
        return {"color_proportion": (int(self.r_ui.value), int(self.g_ui.value), int(self.b_ui.value))}


class VRLSBOptions:
    def __init__(self):
        ui.label('Parameters:')
        with ui.row().classes("w-64 justify-center"):
            self.alpha_ui = ui.number(label='Alpha', value=9, min=-1, max=255, precision=0).classes("w-12")
            self.max_p_ui = ui.number(label='Max bits', value=4, min=1, max=8, precision=0).classes("w-12")
    
    def get_args(self):
        return {"alpha": self.alpha_ui.value, "max_p": self.max_p_ui.value}


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

                
ui.button('Help', on_click=lambda: ui.open('/help'))

@ui.page('/help')
def other_page():
    ui.button('Go back', on_click=lambda: ui.open('/'))
    ui.label('Help tab')

    
def on_startup():
    pathlib.Path("tmp/").mkdir(parents=True, exist_ok=True)

app.on_startup(on_startup)

def on_shutdown():
    shutil.rmtree('tmp/', ignore_errors=True)

app.on_shutdown(on_shutdown)

ui.run(native=True, window_size=(1000, 750))