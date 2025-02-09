import sys
import os
import shutil
from PIL import Image, ImageDraw, ImageFont

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
            # 원본 파일과 생성된 이미지 파일을 output 폴더로 이동
            shutil.move(file_path, os.path.join(output_dir, os.path.basename(file_path)))
            shutil.move(image_file, os.path.join(output_dir, os.path.basename(image_file)))
    
    print("모든 파일 변환 및 이동이 완료되었습니다.")

def convert_file(input_file, output_file=None):
    # 텍스트 파일 읽기 (양쪽 공백 제거)
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    lines = text.splitlines()
    if len(lines) == 0:
        print(f"파일에 내용이 없습니다: {input_file}")
        return

    # 파일명의 내용을 타이틀로 사용 (형식: "아티스트 - 제목")
    base_name = os.path.splitext(os.path.basename(input_file))[0]  # 예: "이승철 - 그 사람"
    title_text = base_name

    # 폰트 설정
    normal_font_size = 20
    title_font_size = normal_font_size * 2  # 40
    normal_font_path = r"C:\Windows\Fonts\malgun.ttf"      # 일반 폰트 (볼드 미적용)
    title_font_path  = r"C:\Windows\Fonts\malgunbd.ttf"      # 볼드 폰트

    try:
        normal_font = ImageFont.truetype(normal_font_path, normal_font_size)
        title_font = ImageFont.truetype(title_font_path, title_font_size)
    except IOError:
        print(f"폰트를 찾을 수 없습니다: {normal_font_path} 또는 {title_font_path}")
        sys.exit(1)

    # 콘솔에 폰트 정보 출력
    print(f"일반 텍스트 폰트: 사이즈 {normal_font_size}, 볼드: False (사용된 폰트: {normal_font_path})")
    print(f"타이틀 폰트: 사이즈 {title_font_size}, 볼드: True (사용된 폰트: {title_font_path})")
    
    # 라인 별 간격 설정 (픽셀 단위)
    line_spacing = 5
    title_spacing = 10

    # 더미 이미지를 생성하여 텍스트 크기를 측정
    dummy_img = Image.new("RGB", (1, 1))
    draw_dummy = ImageDraw.Draw(dummy_img)

    # 타이틀 텍스트 측정 (타이틀은 볼드, 사이즈 40)
    title_bbox = draw_dummy.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    # 본문(가사) 텍스트 측정 (일반 텍스트, 사이즈 20)
    max_width = title_width  # 타이틀 너비보다 클 수 있음
    content_line_heights = []
    for line in lines:
        bbox = draw_dummy.textbbox((0, 0), line, font=normal_font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        max_width = max(max_width, line_width)
        content_line_heights.append(line_height)
    
    if len(content_line_heights) > 0:
        total_content_height = sum(content_line_heights) + line_spacing * (len(content_line_heights) - 1)
    else:
        total_content_height = 0

    padding = 20
    image_width = max_width + padding * 2
    total_height = padding + title_height + title_spacing + total_content_height + padding

    # 최종 이미지 생성 (배경 색상: 밝은 회색)
    bg_color = "#f8f8f8"
    img = Image.new("RGB", (image_width, total_height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 타이틀 그리기
    current_y = padding
    draw.text((padding, current_y), title_text, fill="black", font=title_font)
    current_y += title_height + title_spacing

    # 본문(가사) 텍스트 그리기
    for i, line in enumerate(lines):
        draw.text((padding, current_y), line, fill="black", font=normal_font)
        current_y += content_line_heights[i] + line_spacing

    # 워터마크 추가: 워터마크 텍스트 및 폰트 설정
    watermark_text = "© GenChord"
    watermark_font_size = 15
    watermark_font = ImageFont.truetype(normal_font_path, watermark_font_size)
    
    # 이미지를 RGBA 모드로 변환한 후, 투명 overlay 생성
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(overlay)

    # 워터마크 텍스트 크기 측정
    watermark_bbox = watermark_draw.textbbox((0, 0), watermark_text, font=watermark_font)
    watermark_text_width = watermark_bbox[2] - watermark_bbox[0]
    watermark_text_height = watermark_bbox[3] - watermark_bbox[1]
    margin = 10

    # 워터마크 사각형 좌표 (오른쪽 하단에 여백(margin) 적용)
    x = img.width - watermark_text_width - margin * 2
    y = img.height - watermark_text_height - margin * 2

    # 반투명 배경 사각형 (검정색, alpha 100)
    rectangle_color = (0, 0, 0, 100)
    watermark_draw.rectangle([x, y, x + watermark_text_width + margin * 2, y + watermark_text_height + margin * 2], fill=rectangle_color)

    # 워터마크 텍스트 그리기 (밝은 흰색, alpha 200)
    text_x = x + margin
    text_y = y + margin
    watermark_draw.text((text_x, text_y), watermark_text, font=watermark_font, fill=(255, 255, 255, 200))

    # overlay와 합성 후 RGB 모드로 변환
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    
    if output_file is None:
        output_file = os.path.join(os.path.dirname(input_file), base_name + " 기타 코드 피아노 악보 가사.png")

    img.save(output_file)
    print(f"이미지가 저장되었습니다: {output_file}")
    return output_file

if __name__ == '__main__':
    main() 