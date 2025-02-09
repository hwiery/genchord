from PIL import Image, ImageDraw, ImageFont
import os
import math

class ChordGenerator:
    def __init__(self):
        self.title_font_size = 48
        self.font_size = 40
        self.padding = 20
        self.chord_spacing = 80
        
        # A4 크기 설정 (300 DPI 기준)
        self.a4_width = 2480  # 210mm * 300DPI / 25.4
        self.a4_height = 3508  # 297mm * 300DPI / 25.4
        
        # 한글 폰트 설정
        font_paths = [
            "C:/Windows/Fonts/malgunbd.ttf",  # 맑은 고딕 Bold
            "C:/Windows/Fonts/malgun.ttf",    # 맑은 고딕
            "C:/Windows/Fonts/gulim.ttc",     # 굴림
        ]
        
        self.title_font = None
        self.font = None
        
        # 제목용 볼드 폰트
        for font_path in font_paths:
            try:
                self.title_font = ImageFont.truetype(font_path, self.title_font_size)
                self.font = ImageFont.truetype(font_path, self.font_size)
                break
            except:
                continue
                
        if self.title_font is None:
            self.title_font = ImageFont.load_default()
            self.font = ImageFont.load_default()
            
    def create_chord_image(self, chord_progression, output_path):
        """코드 진행을 이미지로 변환"""
        lines = chord_progression.split('\n')
        
        # 제목 추출 (첫 번째 줄)
        title = lines[0] if lines else ""
        content_lines = lines[1:] if lines else []
        
        # 실제 사용 가능한 영역 계산 (여백 제외)
        usable_width = self.a4_width - (self.padding * 2)
        usable_height = self.a4_height - (self.padding * 2)
        
        # 제목 높이 계산
        title_height = self.title_font_size + (self.padding * 2)
        
        # 한 페이지당 들어갈 수 있는 줄 수 계산 (제목 공간 제외)
        content_height = usable_height - title_height
        lines_per_page = math.floor(content_height / (self.font_size + self.padding))
        
        # 총 필요한 페이지 수 계산
        total_pages = math.ceil(len(content_lines) / lines_per_page)
        
        for page in range(total_pages):
            # 현재 페이지의 라인들
            start_idx = page * lines_per_page
            end_idx = min((page + 1) * lines_per_page, len(content_lines))
            current_lines = content_lines[start_idx:end_idx]
            
            # 이미지 생성
            image = Image.new('RGB', (self.a4_width, self.a4_height), 'white')
            draw = ImageDraw.Draw(image)
            
            # 제목 그리기 (첫 페이지에만)
            if page == 0:
                draw.text((self.padding, self.padding), title, 
                         font=self.title_font, fill='black')
            
            # 내용 그리기
            y = title_height + self.padding if page == 0 else self.padding
            for line in current_lines:
                if not line.strip():
                    continue
                    
                draw.text((self.padding, y), line, font=self.font, fill='black')
                y += self.font_size + self.padding
                
            # 페이지 번호 추가
            if total_pages > 1:
                page_num_text = f"Page {page + 1}/{total_pages}"
                draw.text((self.a4_width - 200, self.a4_height - 50), 
                         page_num_text, font=self.font, fill='black')
            
            # 파일 저장
            if total_pages > 1:
                base_name, ext = os.path.splitext(output_path)
                current_output = f"{base_name}_page{page + 1}{ext}"
            else:
                current_output = output_path
                
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(current_output), exist_ok=True)
            
            # 이미지 저장
            image.save(current_output) 