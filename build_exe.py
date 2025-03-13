import PyInstaller.__main__
import os

def build_exe():
    script_path = os.path.abspath('text_to_image_gui.py')
    icon_path = os.path.abspath('assets/cute_icon.ico')
    assets_path = os.path.abspath('assets')
    
    PyInstaller.__main__.run([
        script_path,
        '--name=텍스트이미지변환기',
        '--onefile',
        '--windowed',
        f'--icon={icon_path}',
        f'--add-data={assets_path};assets',
        '--clean'
    ])

if __name__ == '__main__':
    build_exe() 