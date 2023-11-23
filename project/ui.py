from nicegui import app, ui

im1 = None
im2 = None
generated_stego_im = None
revealed_secret_im = None

async def choose_im1():
    global im1
    files = await app.native.main_window.create_file_dialog(allow_multiple=False) # Add file_types filter
    if files is not None and len(files) > 0:
        im1 = files[0]
        ui.image(im1).classes("w-64")

async def choose_im2():
    global im2
    files = await app.native.main_window.create_file_dialog(allow_multiple=False)
    if files is not None and len(files) > 0:
        im2 = files[0]
        ui.image(im2).classes("w-64")

async def save_image():
    # Save image, perhaps use text field to specify the name
    pass

async def generate_stego_image():
    global generated_stego_im
    if im1 is None or im2 is None:
        return
    # Run selected alg with im1, im2 and other configuration params
    generated_stego_im = im1 # Change to function result
    ui.image(generated_stego_im).classes("w-64")
    ui.button('save stego image', on_click=save_image).classes("w-64")

def alg_hide(n):
    ui.label(f'Alg {n} desc and options')
    with ui.row():
        with ui.column():
            ui.button('choose cover image', on_click=choose_im1).classes("w-64")
        with ui.column():
            ui.button('choose secret image', on_click=choose_im2).classes("w-64")
        with ui.column():
            ui.button('generate stego image', on_click=generate_stego_image).classes("w-64")

async def reveal_secret_image():
    global revealed_secret_im
    if im1 is None:
        return
    # Run selected alg with im1 and other configuration params
    revealed_secret_im = im1 # Change to function result
    ui.image(revealed_secret_im).classes("w-64")
    ui.button('save revealed image', on_click=save_image).classes("w-64")

def alg_reveal(n):
    ui.label(f'Alg {n} desc and options')
    with ui.row():
        with ui.column():
            ui.button('choose stego image', on_click=choose_im1).classes("w-64")
        with ui.column():
            ui.button('reveal secret image', on_click=reveal_secret_image).classes("w-64")

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
                alg_hide(1)
            with ui.tab_panel(reveal):
                alg_reveal(1)
    with ui.tab_panel(two):
        with ui.tab_panels(tabs_mode, value=hide).classes('w-full'):
            with ui.tab_panel(hide):
                alg_hide(2)
            with ui.tab_panel(reveal):
                alg_reveal(2)
    with ui.tab_panel(three):
        with ui.tab_panels(tabs_mode, value=hide).classes('w-full'):
            with ui.tab_panel(hide):
                alg_hide(3)
            with ui.tab_panel(reveal):
                alg_reveal(3)

ui.run(native=True, window_size=(900, 600))