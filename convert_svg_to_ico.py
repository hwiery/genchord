from PIL import Image
import cairosvg
import io
import os

def convert_svg_to_ico(svg_path, ico_path):
    # SVG를 PNG로 변환
    png_data = cairosvg.svg2png(url=svg_path, output_width=256, output_height=256)
    
    # PNG 데이터를 PIL Image로 변환
    img = Image.open(io.BytesIO(png_data))
    
    # ICO 파일로 저장
    img.save(ico_path, format='ICO', sizes=[(256, 256)])

if __name__ == '__main__':
    svg_path = os.path.abspath('assets/cute_icon.svg')
    ico_path = os.path.abspath('assets/cute_icon.ico')
    convert_svg_to_ico(svg_path, ico_path) 