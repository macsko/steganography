from nicegui import ui

@ui.page('/help')
def help_page():
    ui.button('Go back', on_click=lambda: ui.open('/')).classes(remove="w-64")

    with ui.expansion('Algorithm selection', value=True).props("header-class=text-2xl").classes("w-full"):
        ui.markdown('''
                    The purpose of the application is to provide the image steganography techniques.
                    It implements two image in image methods: **Basic LSB** and **Variable rate LSB**,
                    and one text in image method: **Coverless**.''')
        ui.separator()

        ui.markdown('Algorithm can be chosen using top selection bar:')
        with ui.tabs().classes('w-full'):
            ui.tab('Basic LSB')
            ui.tab('Variable rate LSB')
            ui.tab('Coverless')
        ui.separator()

        ui.markdown('All three algorithms have two modes: hide and reveal which has to be selected:')
        with ui.tabs().classes('w-full'):
            ui.tab('Hide')
            ui.tab('Reveal')
    ui.separator()
    
    with ui.expansion('Basic LSB').props("header-class=text-2xl").classes("w-full"):
        ui.label('Hiding').classes("text-xl")
        ui.markdown('''
                    1) Select the cover image using **CHOOSE COVER IMAGE** button.\n
                    2) Select the secret image using **CHOOSE SECRET IMAGE** button.\n
                    3) (Optional) Specify the parameters of the algorithm in the section **Color proportions**:
                    number of bits used to hide a secret image per each of the colors R, G and B.\n
                    _The higher the parameters are, the lower quality of stego image and the higher resolution of secret image are._\n
                    _Remember the parameters as they are required to properly reveal the image._\n
                    4) To generate the stego image click **GENERATE STEGO IMAGE** button.
                    Secret image is resized to match whole cover image for given parameters.\n
                    5) After a short time, the result is displayed
                    and it is possible to save the image by specifying a filename in an appropriate input field.
                    _Note that the filename has to end with one of extensions: .png, .tiff or .bmp._
                    By clicking **SAVE STEGO IMAGE** the result is saved with the given name in the working directory of an application.''')
        
        ui.label('Revealing').classes("text-xl")
        ui.markdown('''
                    1) Select the stego image using **CHOOSE STEGO IMAGE** button.\n
                    2) Specify the parameters of the algorithm in the section **Color proportions**.\n
                    _Use the same parameters as used for hiding._
                    3) To reveal the secret image click **REVEAL SECRET IMAGE** button.\n
                    4) After a short time, the result is displayed
                    and it is possible to save the image by specifying a filename in an appropriate input field.
                    _Note that the filename has to end with one of extensions: .png, .tiff or .bmp._
                    By clicking **SAVE REVEALED IMAGE** the result is saved with the given name in the working directory of an application.''')
    
    ui.separator()

    with ui.expansion('Variable rate LSB').props("header-class=text-2xl").classes("w-full"):
        ui.label('Hiding').classes("text-xl")
        ui.markdown('''
                    1) Select the cover image using **CHOOSE COVER IMAGE** button.\n
                    2) Select the secret image using **CHOOSE SECRET IMAGE** button.\n
                    3) (Optional) Specify two parameters of the algorithm in the section **Parameters**:\n
                    - _Alpha_ which is a cut-off parameter of smoothness parameter below that the number of bits used is reduced to 1.
                    - _Max bits_ which defines maximum bits number used for hiding per pixel color.\n
                    _The lower the Alpha is and the higher the Max bits are, the lower quality of stego image
                    and the higher resolution of secret image are._\n
                    _Remember the parameters as they are required to properly reveal the image._\n
                    4) To generate the stego image click **GENERATE STEGO IMAGE** button.
                    Secret image is resized to match whole cover image for given parameters.\n
                    5) After a short time, the result is displayed
                    and it is possible to save the image by specifying a filename in an appropriate input field.
                    _Note that the filename has to end with one of extensions: .png, .tiff or .bmp._
                    By clicking **SAVE STEGO IMAGE** the result is saved with the given name in the working directory of an application.''')

        ui.label('Revealing').classes("text-xl")
        ui.markdown('''
                    1) Select the stego image using **CHOOSE STEGO IMAGE** button.\n
                    2) Specify the parameters of the algorithm in the section **Parameters**.
                    _Use the same parameters as used for hiding._\n
                    3) To reveal the secret image click **REVEAL SECRET IMAGE** button.\n
                    4) After a short time, the result is displayed
                    and it is possible to save the image by specifying a filename in an appropriate input field.
                    _Note that the filename has to end with one of extensions: .png, .tiff or .bmp._
                    By clicking **SAVE REVEALED IMAGE** the result is saved with the given name in the working directory of an application.''')
    
    ui.separator()

    with ui.expansion('Coverless').props("header-class=text-2xl").classes("w-full"):
        ui.label('Hiding').classes("text-xl")
        ui.markdown('''
                    1) Select the _grayscale_ cover image using **CHOOSE COVER IMAGE** button.\n
                    2) Select the directory used to generate a blocks cache using **CHOOSE BLOCKS DIRECTORY** button.
                    It should be done by selecting one of the children in the desired directory.
                    _The algorithm will take all the files from the directory. It should contain only images intended to be used._\n
                    3) Specify the secret text in an appropriate input field
                    or select the file from which the text will be taken using **LOAD SECRET TEXT** button.
                    _Secret text length is limited to 100 characters._\n
                    4) To generate the stego image click **GENERATE STEGO IMAGE** button.\n
                    5) After a short time, the result is displayed
                    and it is possible to save the image by specifying a filename in an appropriate input field.
                    _Note that the filename has to end with one of extensions: .png, .tiff or .bmp._
                    By clicking **SAVE STEGO IMAGE** the result is saved with the given name in the working directory of an application.''')
        
        ui.label('Revealing').classes("text-xl")
        ui.markdown('''
                    1) Select the stego image using **CHOOSE STEGO IMAGE** button.\n
                    2) To reveal the secret text click **REVEAL SECRET TEXT** button.\n
                    3) After a short time, the result is displayed
                    and it is possible to save the text by specifying a filename in an appropriate input field.
                    By clicking **SAVE REVEALED IMAGE** the result is saved with the given name in the working directory of an application.''')
    
    ui.markdown()