import os
import re

def is_valid_content(line):
    # 섹션 헤더 확인 (Intro, Verse, Chorus 등)
    section_pattern = r'^\s*[\[\(]*(intro|verse|bridge|chorus|outro|pre-chorus|hook|refrain|interlude|instrumental|solo)[\]\)]*\s*\d*\s*$'
    if re.match(section_pattern, line, re.IGNORECASE):
        return True
    
    # Capo 정보 확인
    if re.match(r'^\s*capo\s*\d+\s*$', line.lower()):
        return True
    
    # 코드 라인 확인 (예: Am  G  F)
    chord_pattern = r'^[\s]*([A-G][#mb]?(maj|min|aug|dim|sus|add)?[0-9]?\s*)+$'
    if re.match(chord_pattern, line):
        return True
    
    # 코드와 가사가 함께 있는 라인 확인
    chord_lyric_pattern = r'^[\s]*[A-G][#mb]?(maj|min|aug|dim|sus|add)?[0-9]?.*[a-zA-Z가-힣]+.*$'
    if re.match(chord_lyric_pattern, line):
        return True
    
    # 일반 가사 확인
    line = line.strip()
    if line and not is_metadata_line(line):
        return True
        
    return False

def is_metadata_line(line):
    metadata_patterns = [
        r'written by', r'performed by', r'produced by', r'recorded by',
        r'mixed by', r'mastered by', r'published by', r'lyrics by',
        r'music by', r'arranged by', r'composed by', r'original by',
        r'cover by', r'tab by', r'chords by', r'@', r'©', r'=',
        r'artist:', r'album:', r'year:', r'genre:', r'key:', 
        r'tempo:', r'difficulty:', r'tuning:', r'note:', 
        r'transcribed by', r'tabbed by', r'created by',
        r'copyright', r'all rights reserved', r'source:', 
        r'duration:', r'length:', r'release:', r'label:',
        r'http[s]?://', r'www\.', r'youtube\.com', r'spotify\.com',
        r'ultimate-guitar\.com', r'credits:', r'original version',
        r'version:', r'original artist', r'original song'
    ]
    
    line_lower = line.lower()
    return any(re.search(pattern.lower(), line_lower) for pattern in metadata_patterns)

def clean_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='cp949') as f:
                lines = f.readlines()
        except:
            print(f"파일을 읽을 수 없습니다: {file_path}")
            return False

    # 파일 내용 정리
    cleaned_lines = []
    content_started = False
    consecutive_empty_lines = 0
    
    for line in lines:
        line_strip = line.strip()
        
        # 빈 줄 처리
        if not line_strip:
            if content_started:
                consecutive_empty_lines += 1
                if consecutive_empty_lines <= 2:  # 최대 2개의 연속된 빈 줄만 허용
                    cleaned_lines.append(line)
            continue
        
        consecutive_empty_lines = 0
        
        if is_valid_content(line_strip):
            content_started = True
            cleaned_lines.append(line)
    
    # 파일 시작과 끝의 불필요한 빈 줄 제거
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    # 최소 내용 확인
    if len(cleaned_lines) < 2:  # 최소 2줄 이상의 내용이 있어야 함
        return False
    
    if cleaned_lines:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            print(f"파일 정리 완료: {file_path}")
            return True
        except Exception as e:
            print(f"파일 쓰기 오류: {file_path} - {str(e)}")
            return False
    
    return False

def main():
    input_dir = "data/input"
    if not os.path.exists(input_dir):
        print(f"입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        return

    processed_count = 0
    cleaned_count = 0
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            processed_count += 1
            file_path = os.path.join(input_dir, filename)
            if clean_file_content(file_path):
                cleaned_count += 1
    
    print(f"\n처리 완료:")
    print(f"총 처리된 파일: {processed_count}")
    print(f"정리된 파일: {cleaned_count}")

if __name__ == '__main__':
    main() 