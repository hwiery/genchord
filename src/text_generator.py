import os
from datetime import datetime

class TextGenerator:
    def save_description(self, description, output_path):
        """설명문을 파일로 저장"""
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 현재 날짜와 시간 추가
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"생성 시간: {current_time}\n\n{description}"
        
        # UTF-8 인코딩으로 파일 저장
        with open(output_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(content) 