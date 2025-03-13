import os
import glob

def remove_extra_newlines(file_path):
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 연속된 줄바꿈을 하나로 변경
        while '\n\n' in content:
            content = content.replace('\n\n', '\n')
        
        # 파일 다시 쓰기
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
            
        print(f'처리 완료: {os.path.basename(file_path)}')
    except Exception as e:
        print(f'에러 발생 ({os.path.basename(file_path)}): {str(e)}')

def process_all_files():
    # data/input 폴더 내의 모든 txt 파일 찾기
    input_path = os.path.join('input', '*.txt')
    files = glob.glob(input_path)
    
    print(f'총 {len(files)}개의 파일을 찾았습니다.')
    
    # 각 파일 처리
    for file_path in files:
        remove_extra_newlines(file_path)
    
    print('\n모든 파일 처리가 완료되었습니다.')

if __name__ == '__main__':
    process_all_files() 