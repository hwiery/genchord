import os
import re

def extract_version(filename):
    # 다양한 버전 패턴 매칭
    patterns = [
        r'\(ver(?:sion)?\s*(\d+)\)',  # (ver 2) or (version 2)
        r'v(\d+)(?!\S)',              # v2 (끝에 있는 경우)
        r'\[ver(?:sion)?\s*(\d+)\]',  # [ver 2] or [version 2]
        r'ver(?:sion)?\s*(\d+)',      # ver 2 or version 2
    ]
    
    print(f"파일 분석 중: {filename}")
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            version = int(match.group(1))
            print(f"버전 정보 발견: {version} (패턴: {pattern})")
            return version
            
    print("버전 정보 없음")
    return 1

def get_base_song_name(filename):
    # 파일 확장자 제거
    name = os.path.splitext(filename)[0]
    
    # 버전 정보 제거
    patterns = [
        r'\s*\(ver(?:sion)?\s*\d+\)',
        r'\s*v\d+(?!\S)',
        r'\s*\[ver(?:sion)?\s*\d+\]',
        r'\s*ver(?:sion)?\s*\d+',
    ]
    
    original_name = name
    for pattern in patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    if original_name != name:
        print(f"기본 곡 이름 추출: {original_name} -> {name}")
    
    return name

def main():
    # 현재 디렉토리의 모든 .txt 파일 처리
    files = [f for f in os.listdir('.') if f.endswith('.txt')]
    
    # 버전 정보가 있는 파일 찾기
    files_with_versions = []
    for file in files:
        version = extract_version(file)
        if version > 1:  # 버전 1이 아닌 경우만 저장
            files_with_versions.append((file, version))
    
    if not files_with_versions:
        print("\n버전 정보를 포함한 파일이 없습니다.")
        return
    
    print("\n발견된 버전 파일들:")
    for file, version in files_with_versions:
        print(f"{file} (버전: {version})")
    
    # 사용자 확인
    response = input("\n이 파일들의 버전 정보를 제거하시겠습니까? (y/n): ")
    if response.lower() != 'y':
        print("작업이 취소되었습니다.")
        return
    
    # 파일 이름 변경
    for old_name, _ in files_with_versions:
        try:
            new_name = get_base_song_name(old_name) + os.path.splitext(old_name)[1]
            os.rename(old_name, new_name)
            print(f"파일 이름 변경: {old_name} -> {new_name}")
        except Exception as e:
            print(f"오류 발생: {old_name} 파일 이름 변경 실패 - {str(e)}")

if __name__ == '__main__':
    main() 