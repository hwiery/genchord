import os
import re
from collections import defaultdict

def extract_version(filename):
    # 디버그 출력
    print(f"파일 분석: {filename}")
    
    # 버전 정보 추출 (예: "(ver 2)", "(version 3)", "v4")
    version_match = re.search(r'(?:\(ver(?:sion)?\s*(\d+)\)|v(\d+)(?!\S))', filename, re.IGNORECASE)
    if version_match:
        version = int(version_match.group(1) or version_match.group(2))
        print(f"추출된 버전: {version}")
        return version
    
    # 버전 번호가 없는 경우 버전 1로 처리
    print(f"버전 정보 없음, 버전 1로 처리")
    return 1

def get_base_song_name(filename):
    # 파일 확장자 제거
    filename = os.path.splitext(filename)[0]
    # 버전 정보 제거 (예: "(ver 2)", "(version 3)", "v4")
    base_name = re.sub(r'\s*(?:\(ver(?:sion)?\s*\d+\)|v\d+(?!\S))', '', filename, flags=re.IGNORECASE)
    print(f"기본 곡명 추출: {filename} -> {base_name}")
    return base_name

def main():
    input_dir = "data/input"
    if not os.path.exists(input_dir):
        print(f"디렉토리를 찾을 수 없습니다: {input_dir}")
        return

    print("파일 분석 시작...")
    # 파일들을 기본 곡 이름으로 그룹화
    song_versions = defaultdict(list)
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            base_name = get_base_song_name(filename)
            version = extract_version(filename)
            song_versions[base_name].append((version, filename))
            print(f"그룹화: {base_name} - 버전 {version}")

    # 삭제할 파일 목록 생성
    files_to_delete = []
    for base_name, versions in song_versions.items():
        if len(versions) > 1:
            print(f"\n{base_name}의 버전들:")
            for v, f in versions:
                print(f"- {f} (버전 {v})")
            
            # 버전별로 정렬
            versions.sort(key=lambda x: x[0])
            # 가장 높은 버전을 제외한 모든 파일을 삭제 목록에 추가
            for v, f in versions[:-1]:
                print(f"삭제 대상으로 표시: {f} (더 높은 버전 있음)")
                files_to_delete.append(f)

    if not files_to_delete:
        print("\n삭제할 이전 버전 파일이 없습니다.")
        return

    # 삭제할 파일 목록 표시
    print("\n삭제할 파일 목록:")
    for file in files_to_delete:
        print(f"- {file}")

    # 사용자 확인
    confirmation = input("\n위 파일들을 삭제하시겠습니까? (y/n): ")
    if confirmation.lower() == 'y':
        for file in files_to_delete:
            file_path = os.path.join(input_dir, file)
            try:
                os.remove(file_path)
                print(f"삭제됨: {file}")
            except Exception as e:
                print(f"오류 발생: {file} 삭제 실패 - {str(e)}")
        print("\n파일 삭제가 완료되었습니다.")
    else:
        print("작업이 취소되었습니다.")

if __name__ == "__main__":
    main() 