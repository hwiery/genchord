# 텍스트 이미지 변환기 (Text to Image Converter)

## 🆕 업데이트 소식
- 사용자 친화적인 GUI 인터페이스 제공
- 드래그 앤 드롭으로 파일 선택 가능
- 실시간 미리보기 지원
- 원클릭 실행 가능한 패키지 제공

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
├── assets/                # 아이콘 및 리소스 파일
├── text_to_image_gui.py   # GUI 메인 프로그램
├── build_exe.py           # 실행 파일 생성 스크립트
├── requirements.txt
└── README.md
```

## ⚙️ 설정
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