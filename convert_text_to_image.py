import sys
import os
import shutil
from PIL import Image, ImageDraw, ImageFont
import unicodedata
import re

def is_cjk(char):
    code = ord(char)
    return any([
        0x3000 <= code <= 0x303F,     # CJK 부호
        0x3040 <= code <= 0x309F,     # 히라가나
        0x30A0 <= code <= 0x30FF,     # 가타카나
        0x4E00 <= code <= 0x9FFF,     # CJK 통합 한자
        0xFF00 <= code <= 0xFFEF,     # 전각 문자
        0xAC00 <= code <= 0xD7AF      # 한글 음절
    ])

def get_text_language(text):
    # 텍스트의 주요 언어 판별
    jp_count = 0
    cn_count = 0
    ko_count = 0
    
    for char in text:
        if not is_cjk(char):
            continue
            
        code = ord(char)
        if 0xAC00 <= code <= 0xD7AF:  # 한글 음절 범위
            ko_count += 1
        else:
            char_name = unicodedata.name(char, '').lower()
            if 'hiragana' in char_name or 'katakana' in char_name:
                jp_count += 1
            elif 'cjk' in char_name:
                cn_count += 1
    
    # 가중치를 둔 언어 판별
    if ko_count > 0:  # 한글이 있으면 우선 한국어로 판단
        return 'ko'
    elif jp_count > cn_count:
        return 'jp'
    elif cn_count > jp_count:
        return 'cn'
    return 'ko'  # 기본값은 한국어

def is_section_header(line):
    # 섹션 헤더 패턴 매칭 (대소문자 무관)
    pattern = r'^\s*[\[\(]*(chorus|verse|bridge|intro|outro|pre-chorus|hook|refrain|interlude|간주|후렴|브릿지)[\]\)]*\s*$'
    return bool(re.match(pattern, line, re.IGNORECASE))

def clean_text(text):
    # 특수 공백 문자들을 일반 공백으로 변환
    text = re.sub(r'[\u3000\u2003\u2002\u2000\u2001\u2004-\u200A\u205F\u00A0]', ' ', text)
    # 여러 개의 연속된 공백을 하나로 통일
    text = re.sub(r'\s+', ' ', text)
    return text

def clean_line(line):
    # 줄 단위 텍스트 정제
    # 앞뒤 공백 제거 및 특수 공백 처리
    line = clean_text(line.strip())
    # 코드 구분을 위한 최소 2개의 공백 유지
    line = re.sub(r'([A-G][#mb]?(?:maj|min|aug|dim|sus|[0-9])?)\s*([A-G][#mb]?(?:maj|min|aug|dim|sus|[0-9])?)', r'\1  \2', line)
    return line

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_text_to_image.py <input_directory>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    if not os.path.isdir(input_path):
        print(f"입력 경로는 디렉터리여야 합니다: {input_path}")
        sys.exit(1)
        
    # output 폴더 생성 (없으면 생성)
    output_dir = os.path.join(os.path.dirname(input_path), "output")
    os.makedirs(output_dir, exist_ok=True)

    # .txt 파일뿐만 아니라 확장자가 없는 파일도 모두 변환
    for filename in os.listdir(input_path):
        file_path = os.path.join(input_path, filename)
        if os.path.isfile(file_path) and (filename.lower().endswith(".txt") or os.path.splitext(filename)[1] == ""):
            image_file = convert_file(file_path)
            if image_file:  # 변환이 성공한 경우에만 이동
                # 원본 파일과 생성된 이미지 파일을 output 폴더로 이동
                shutil.move(file_path, os.path.join(output_dir, os.path.basename(file_path)))
                shutil.move(image_file, os.path.join(output_dir, os.path.basename(image_file)))
    
    print("모든 파일 변환 및 이동이 완료되었습니다.")

def convert_file(input_file, output_file=None):
    # 텍스트 파일 읽기 (여러 인코딩 시도)
    encodings = ['utf-8', 'cp949', 'euc-kr', 'shift_jis', 'gb2312', 'big5', 'latin1']
    text = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                text = f.read().strip()
                used_encoding = encoding
                break
        except UnicodeDecodeError:
            continue
    
    if text is None:
        print(f"파일을 읽을 수 없습니다 (인코딩 문제): {input_file}")
        return None
    
    print(f"사용된 인코딩: {used_encoding}")
    
    # 텍스트 정제
    lines = [clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]  # 빈 줄 제거
    
    if len(lines) == 0:
        print(f"파일에 내용이 없습니다: {input_file}")
        return None

    # 파일명의 내용을 타이틀로 사용
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    title_text = base_name

    # 텍스트 언어 감지
    main_language = get_text_language(text)
    print(f"감지된 주 언어: {main_language}")

    # 폰트 설정
    normal_font_size = 20
    title_font_size = normal_font_size * 2  # 40
    section_font_size = int(normal_font_size * 1.2)  # 섹션 헤더용 폰트 크기

    # 언어별 폰트 매핑
    font_paths = {
        'ko': {
            'normal': r"C:\Windows\Fonts\malgun.ttf",
            'bold': r"C:\Windows\Fonts\malgunbd.ttf"
        },
        'jp': {
            'normal': r"C:\Windows\Fonts\msgothic.ttc",
            'bold': r"C:\Windows\Fonts\msgothic.ttc"
        },
        'cn': {
            'normal': r"C:\Windows\Fonts\simsun.ttc",
            'bold': r"C:\Windows\Fonts\simsun.ttc"
        }
    }

    # 선택된 언어의 폰트 로드
    try:
        normal_font = ImageFont.truetype(font_paths[main_language]['normal'], normal_font_size)
        title_font = ImageFont.truetype(font_paths[main_language]['bold'], title_font_size)
        section_font = ImageFont.truetype(font_paths[main_language]['bold'], section_font_size)
    except IOError:
        print(f"기본 {main_language} 폰트를 찾을 수 없습니다. 한글 폰트로 대체합니다.")
        normal_font = ImageFont.truetype(font_paths['ko']['normal'], normal_font_size)
        title_font = ImageFont.truetype(font_paths['ko']['bold'], title_font_size)
        section_font = ImageFont.truetype(font_paths['ko']['bold'], section_font_size)

    # 라인 별 간격 설정 (픽셀 단위)
    line_spacing = 8  # 기본 줄 간격 증가
    title_spacing = 20
    section_spacing = 40  # 섹션 간격 증가

    # A4 사이즈 설정 (72dpi 기준, 210mm x 297mm)
    a4_width = 595  # A4 너비는 고정
    
    # 로고 이미지 로드 및 크기 조정 (워터마크용)
    watermark_width = int(a4_width * 0.5)  # 워터마크 크기 조정
    try:
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path)
            ratio = watermark_width / logo_img.width
            watermark_height = int(logo_img.height * ratio)
            logo_img = logo_img.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
            
            if logo_img.mode != 'RGBA':
                logo_img = logo_img.convert('RGBA')
            
            data = logo_img.getdata()
            new_data = []
            for item in data:
                new_data.append((item[0], item[1], item[2], int(255 * 0.15)))  # 투명도 15%로 감소
            logo_img.putdata(new_data)
        else:
            print("로고 이미지(assets/logo.png)를 찾을 수 없습니다.")
            logo_img = None
    except Exception as e:
        print(f"로고 이미지를 로드할 수 없습니다: {e}")
        logo_img = None

    # 더미 이미지를 생성하여 텍스트 크기를 측정
    dummy_img = Image.new("RGB", (1, 1))
    draw_dummy = ImageDraw.Draw(dummy_img)

    # 타이틀 텍스트 측정
    title_bbox = draw_dummy.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    # 본문(가사) 텍스트 측정 및 섹션 구분
    max_width = 0
    content_line_heights = []
    is_section_start = []
    
    for line in lines:
        is_section = is_section_header(line)
        is_section_start.append(is_section)
        
        # 섹션 헤더는 다른 폰트 사용
        current_font = section_font if is_section else normal_font
        
        bbox = draw_dummy.textbbox((0, 0), line, font=current_font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        max_width = max(max_width, line_width)
        content_line_heights.append(line_height)
    
    if len(content_line_heights) > 0:
        total_content_height = sum(content_line_heights)
        # 라인 간격과 섹션 간격 추가
        for i in range(len(lines)):
            if is_section_start[i]:
                total_content_height += section_spacing
            else:
                total_content_height += line_spacing
    else:
        total_content_height = 0

    padding = 40
    top_padding = 40
    bottom_padding = 60  # A4 문서 하단 여백 추가
    
    # 전체 높이 계산
    total_height = top_padding + title_height + title_spacing + total_content_height + padding + bottom_padding
    
    # 최종 이미지 생성
    bg_color = "#f8f8f8"
    img = Image.new("RGB", (a4_width, total_height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    current_y = top_padding
    
    # 타이틀 그리기 (중앙 정렬)
    title_x = (a4_width - title_width) // 2
    draw.text((title_x, current_y), title_text, fill="black", font=title_font)
    current_y += title_height + title_spacing

    # 워터마크 로고 반복 그리기
    if logo_img:
        watermark_spacing_y = watermark_height * 3  # 워터마크 간격 증가
        y_position = watermark_height
        while y_position < total_height - watermark_height:
            logo_x = (a4_width - watermark_width) // 2
            img.paste(logo_img, (logo_x, y_position), logo_img)
            y_position += watermark_spacing_y

    # 본문(가사) 텍스트 그리기
    for i, line in enumerate(lines):
        # 섹션 시작이면 추가 간격 삽입
        if is_section_start[i]:
            current_y += section_spacing
            # 섹션 헤더는 중앙 정렬 및 다른 폰트 사용
            bbox = draw_dummy.textbbox((0, 0), line, font=section_font)
            text_width = bbox[2] - bbox[0]
            text_x = (a4_width - text_width) // 2
            draw.text((text_x, current_y), line, fill="black", font=section_font)
        else:
            # 일반 텍스트는 좌측 정렬
            draw.text((padding, current_y), line, fill="black", font=normal_font)
        
        # 마지막 줄이 아닐 경우에만 줄 간격 추가
        if i < len(lines) - 1:
            current_y += content_line_heights[i] + line_spacing
        else:
            current_y += content_line_heights[i]  # 마지막 줄은 줄 간격 추가하지 않음
    
    if output_file is None:
        output_file = os.path.join(os.path.dirname(input_file), base_name + " 기타 코드 피아노 악보 가사.png")

    img.save(output_file)
    print(f"이미지가 저장되었습니다: {output_file}")
    return output_file

if __name__ == '__main__':
    main() 