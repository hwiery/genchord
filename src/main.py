import os
import schedule
import time
from datetime import datetime
from llm_handler import LLMHandler
from chord_generator import ChordGenerator
from text_generator import TextGenerator

def process_song():
    """곡 처리 메인 함수"""
    input_file = "data/input/song_list.txt"
    
    if not os.path.exists(input_file):
        print(f"입력 파일이 없습니다: {input_file}")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        songs = f.readlines()
    
    llm = LLMHandler()
    chord_gen = ChordGenerator()
    text_gen = TextGenerator()
    
    for song in songs:
        song = song.strip()
        if not song:
            continue
            
        try:
            artist, title = song.split(' - ')
            
            # 파일명 형식 생성
            file_name = f"{artist} - {title} 기타 코드 피아노 악보 가사"
            
            # 코드 진행 생성
            chord_progression = llm.generate_chord_progression(artist, title)
            
            # 이미지 생성
            image_path = f"data/output/images/{file_name}.png"
            chord_gen.create_chord_image(chord_progression, image_path)
            
            # 설명문 생성
            description = llm.generate_song_description(artist, title, chord_progression)
            text_path = f"data/output/descriptions/{file_name}.txt"
            text_gen.save_description(description, text_path)
            
            print(f"처리 완료: {artist} - {title}")
            
        except Exception as e:
            print(f"에러 발생 ({artist} - {title}): {str(e)}")
        
        time.sleep(5)  # API 호출 간 딜레이

def main():
    """메인 스케줄러 함수"""
    print("GenChord 시작...")
    
    # 매일 오전 9시에 실행
    schedule.every().day.at("09:00").do(process_song)
    
    # 시작 시 한 번 실행
    process_song()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 