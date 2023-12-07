from nicegui import app, ui
import cv2
import pathlib
from algorithms.basic_lsb import lsb_basic_hide, lsb_basic_reveal

def read_im(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

def write_im(path, im):
    cv2.imwrite(path, cv2.cvtColor(im, cv2.COLOR_BGR2RGB))


# TODOS:
# Differentiate algorithms called for each tab
# Make special tab for coverless - no secret image, but text
# Generate random tmp names each time
# Save tmp images in tmp dict and remove it on close (create on app startup)
# Add monits when clicked save buttons
# Test app on Windows (tiffs not loading)
# Allow only for certain file types in file dialog
# Compute image shapes based on algorithms options and add them (for LSB algs)
# Add descriptions and help
# Set appropriate window sizing
# Misc images differ in sizes!
# Make better positioning of elements in reveal tabs


class HideAlg:
    def __init__(self):
        self.cover_im = None
        self.secret_im = None
        self.generated_im = None
        self.tmp_im_path = "tmp_im_1.tiff" # Generate random name each time
        
        with ui.row():
            with ui.column():
                ui.button('choose cover image', on_click=self.choose_cover_im).classes("w-64")
                self.cover_im_ui = ui.image("").classes("w-64 h-64")
            with ui.column():
                ui.button('choose secret image', on_click=self.choose_secret_im).classes("w-64")
                self.secret_im_ui = ui.image("").classes("w-64 h-64")
            with ui.column():
                self.generate_btn_ui = ui.button('generate stego image', on_click=self.generate_stego_image).classes("w-64")
                self.generate_btn_ui.disable()
                self.generated_im_ui = ui.image("").classes("w-64 h-64")
                self.filename_ui = ui.input(label='Result filename').classes("w-64")
                self.save_btn_ui = ui.button('save stego image', on_click=self.save_image).classes("w-64")
                self.save_btn_ui.disable()
    
    def set_cover_im(self, im_path):
        self.cover_im = read_im(im_path)
        self.cover_im_ui.set_source(im_path)
        self.cover_im_ui.update()
        if self.secret_im is not None:
            self.enable_generate_btn()
    
    def set_secret_im(self, im_path):
        self.secret_im = read_im(im_path)
        self.secret_im = cv2.resize(self.secret_im, (self.secret_im.shape[0]//2, self.secret_im.shape[1]//2))
        self.secret_im_ui.set_source(im_path)
        self.secret_im_ui.update()
        if self.cover_im is not None:
            self.enable_generate_btn()
    
    def set_generated_im(self, im):
        write_im(self.tmp_im_path, im)
        self.generated_im = im
        self.generated_im_ui.set_source(self.tmp_im_path)
        self.generated_im_ui.update()
    
    def enable_save_btn(self):
        self.save_btn_ui.enable()
        self.save_btn_ui.update()
    
    def enable_generate_btn(self):
        self.generate_btn_ui.enable()
        self.generate_btn_ui.update()
    
    async def choose_cover_im(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False) # Add file_types filter
        if files is not None and len(files) > 0:
            self.set_cover_im(files[0])

    async def choose_secret_im(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False)
        if files is not None and len(files) > 0:
            self.set_secret_im(files[0])

    async def save_image(self):
        write_im(self.filename_ui.value, self.generated_im)
        pathlib.Path(self.tmp_im_path).unlink(missing_ok=True) # Monit when save

    async def generate_stego_image(self):
        # Run selected alg with cover_im, secret_im and other configuration params
        result_im = lsb_basic_hide(self.cover_im, self.secret_im) # Choose right alg
        self.set_generated_im(result_im)
        self.enable_save_btn()


class RevealAlg:
    def __init__(self):
        self.stego_im = None
        self.revealed_im = None
        self.tmp_im_path = "tmp_im_2.tiff" # Generate random name each time
        
        with ui.row():
            with ui.column():
                ui.button('choose stego image', on_click=self.choose_stego_im).classes("w-64")
                self.stego_im_ui = ui.image("").classes("w-64 h-64")
            with ui.column():
                self.reveal_btn_ui = ui.button('reveal secret image', on_click=self.reveal_secret_image).classes("w-64")
                self.reveal_btn_ui.disable()
                self.revealed_im_ui = ui.image("").classes("w-64 h-64")
                self.filename_ui = ui.input(label='Result filename').classes("w-64")
                self.save_btn_ui = ui.button('save revealed image', on_click=self.save_image).classes("w-64")
                self.save_btn_ui.disable()
    
    def set_stego_im(self, im_path):
        self.stego_im = read_im(im_path)
        self.stego_im_ui.set_source(im_path)
        self.stego_im_ui.update()
        self.enable_reveal_btn()
    
    def set_revealed_im(self, im):
        write_im(self.tmp_im_path, im)
        self.revealed_im = im
        self.revealed_im_ui.set_source(self.tmp_im_path)
        self.revealed_im_ui.update()
    
    def enable_save_btn(self):
        self.save_btn_ui.enable()
        self.save_btn_ui.update()
    
    def enable_reveal_btn(self):
        self.reveal_btn_ui.enable()
        self.reveal_btn_ui.update()
    
    async def choose_stego_im(self):
        files = await app.native.main_window.create_file_dialog(allow_multiple=False) # Add file_types filter
        if files is not None and len(files) > 0:
            self.set_stego_im(files[0])

    async def save_image(self):
        write_im(self.filename_ui.value, self.revealed_im)
        pathlib.Path(self.tmp_im_path).unlink(missing_ok=True)

    async def reveal_secret_image(self):
        # Run selected alg with stego_im and other configuration params
        res_shape = (self.stego_im.shape[0]//2, self.stego_im.shape[1]//2, self.stego_im.shape[2]) # TODO Right shape
        result_im = lsb_basic_reveal(self.stego_im, res_shape)
        self.set_revealed_im(result_im)
        self.enable_save_btn()


def alg_hide(n):
    ui.label(f'Alg {n} desc and options')
    HideAlg()

def alg_reveal(n):
    ui.label(f'Alg {n} desc and options')
    RevealAlg()

with ui.tabs().classes('w-full') as tabs:
    one = ui.tab('Alg 1')
    two = ui.tab('Alg 2')
    three = ui.tab('Alg 3')

with ui.tabs().classes('w-full') as tabs_mode:
    hide = ui.tab('Hide')
    reveal = ui.tab('Reveal')

with ui.tab_panels(tabs, value=one).classes('w-full'):
    with ui.tab_panel(one):
        with ui.tab_panels(tabs_mode, value=hide).classes('w-full'):
            with ui.tab_panel(hide):
                alg_hide(0)
            with ui.tab_panel(reveal):
                alg_reveal(0)
    with ui.tab_panel(two):
        with ui.tab_panels(tabs_mode, value=hide).classes('w-full'):
            with ui.tab_panel(hide):
                alg_hide(1)
            with ui.tab_panel(reveal):
                alg_reveal(1)
    with ui.tab_panel(three):
        with ui.tab_panels(tabs_mode, value=hide).classes('w-full'):
            with ui.tab_panel(hide):
                alg_hide(2)
            with ui.tab_panel(reveal):
                alg_reveal(2)

                
ui.button('Help', on_click=lambda: ui.open('/help'))

@ui.page('/help')
def other_page():
    ui.button('Go back', on_click=lambda: ui.open('/'))
    ui.label('Help tab')


def on_shutdown():
    pathlib.Path("tmp_im_1.tiff").unlink(missing_ok=True) # Clear all tmp files, tmp directory?
    pathlib.Path("tmp_im_2.tiff").unlink(missing_ok=True)

app.on_shutdown(on_shutdown)

ui.run(native=True, window_size=(950, 800))