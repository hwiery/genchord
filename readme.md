# 텍스트 이미지 변환기 (Text to Image Converter)

## 🆕 업데이트 소식
기존 CLI 버전에서 사용자 친화적인 GUI 버전으로 업그레이드되었습니다!
- 귀여운 디자인의 GUI 인터페이스 추가
- 드래그 앤 드롭으로 쉬운 파일 선택
- 실시간 미리보기 기능
- 원클릭 실행 가능한 패키지 버전 제공

## 📦 실행 방법

### 패키지 버전 (권장)
1. `dist` 폴더의 `text_to_image_converter.exe` 파일을 실행하세요.
2. 텍스트 파일을 드래그 앤 드롭하거나 파일 선택 버튼을 클릭하세요.
3. 변환 버튼을 클릭하면 이미지가 생성됩니다.

### 소스코드 실행
1. Python 3.11 이상 설치
2. 필요한 라이브러리 설치:
```bash
pip install -r requirements.txt
```
3. `text_to_image_gui.py` 실행:
```bash
python text_to_image_gui.py
```

## 📚 필요한 라이브러리
- PyQt5==5.15.9
- Pillow==10.0.0
- numpy==1.24.3
- cairosvg==2.7.0
- pyinstaller==6.12.0 (패키징용)

## 📁 폴더 구조
```
.
├── assets/          # 아이콘 및 리소스 파일
├── data/           # 텍스트 파일 및 생성된 이미지 저장 폴더 (자동 생성)
├── text_to_image_gui.py    # GUI 메인 프로그램
├── build_exe.py    # 실행 파일 생성 스크립트
└── requirements.txt
```

## ⚙️ 설정
- `data` 폴더는 자동으로 생성되며, 텍스트 파일과 생성된 이미지가 저장됩니다.
- 기본 이미지 크기: 800x600
- 지원 파일 형식: .txt

## 🔨 개발자를 위한 정보
- Python 3.11 이상 권장
- 실행 파일 생성:
```bash
python build_exe.py
```

## 📝 라이선스
MIT License