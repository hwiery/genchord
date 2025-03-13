from PIL import Image, ImageDraw, ImageFont
import os

def create_cute_icon():
    # 256x256 크기의 이미지 생성
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 배경 원 그리기 (파스텔 핑크)
    draw.ellipse([10, 10, 246, 246], fill='#FFB6C1')
    
    # 음표 모양 그리기 (하얀색)
    note_points = [
        (128, 60),   # 상단
        (128, 160),  # 수직선
        (100, 160),  # 음표 머리 시작
        (100, 200),  # 음표 머리 끝
        (156, 200),  # 음표 머리 끝
        (156, 160),  # 음표 머리 시작
        (128, 160)   # 닫힘
    ]
    draw.line(note_points, fill='white', width=15)
    draw.ellipse([85, 170, 125, 200], fill='white')  # 음표 머리
    
    # ICO 파일로 저장
    icon_path = os.path.abspath('assets/cute_icon.ico')
    img.save(icon_path, format='ICO', sizes=[(256, 256)])
    
    return icon_path

if __name__ == '__main__':
    create_cute_icon() 