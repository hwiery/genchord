# GenChord 콘텐츠 이미지 변환기

이 프로젝트는 AI (Claude, ChatGPT, Perplexity 등)를 활용하여 아티스트와 곡 이름을 입력하면 전체 가사와 코드(코드 진행)를 출력받아,  
파일명에 "아티스트 - 곡 제목" 형식으로 **root/data/input** 폴더에 저장한 후,  
자동으로 해당 텍스트 파일을 "이미지"로 변환하여 콘텐츠 포스팅에 용이하도록 하는 오픈소스 도구입니다.

---

## 사용 방법

1. **AI를 통한 콘텐츠 생성**  
   - Claude, ChatGPT, Perplexity 등과 같은 AI에게 아티스트와 곡 이름을 기반으로 전체 가사와 코드 정보를 요청합니다.
   - 출력된 전체 가사와 코드를 복사하여, 파일명에 아티스트와 곡 제목(예: `이승철 - 그 사람`)을 사용하여 **root/data/input** 폴더에 텍스트 파일로 저장합니다.

2. **텍스트 파일을 이미지로 변환**  
   - 터미널(PowerShell)에서 다음 명령어를 실행합니다.
     ```powershell
     python convert_text_to_image.py data/input
     ```
   - 위 명령어를 실행하면 폴더 내의 모든 텍스트(또는 확장자가 없는) 파일이 이미지 파일로 변환되고,  
     원본 파일들과 생성된 이미지 파일 모두 `output` 폴더로 자동 이동됩니다.

3. **콘텐츠 포스팅**  
   - 변환된 이미지 파일은 블로그, 카페, SNS 등 다양한 곳에 손쉽게 포스팅할 수 있는 형태로 제작됩니다.

---

## 장점

- **매우 가벼움**  
  단순한 텍스트 파일을 이미지로 변환하는 기능만 포함하여 실행 속도와 자원 소모가 적습니다.

- **문제없이 구동됨**  
  별다른 설정 없이 텍스트 콘텐츠를 이미지로 안정적으로 변환할 수 있습니다.

- **다양한 포스팅 용도**  
  생성된 이미지는 블로그, 카페, SNS 등에서 바로 사용 가능해 콘텐츠 제작에 효율적입니다.

---

## 단점

- **자동 업로드 기능 실패**  
  API를 통해 자동으로 업로드를 시도하였으나, 자동 업로드 기능은 구현되지 않았습니다.

- **이미지 디자인 개선 필요**  
  기본적인 텍스트 배치 및 워터마크 추가 등은 되어 있으나, 고급 디자인 측면에서는 개선의 여지가 있습니다.

---

## 파일 구조

GenChord/
├── convert_text_to_image.py # 텍스트 파일을 이미지로 변환하는 스크립트
├── data/
│ └── input/ # AI를 통해 생성된 텍스트 파일들을 저장하는 폴더
└── output/ # 변환된 이미지 파일과 원본 텍스트 파일이 이동되는 폴더
---

## 개발/기여 안내

- 본 프로젝트는 오픈소스로 공개되어 있으며, 누구나 자유롭게 사용 및 개선할 수 있습니다.
- 개선점이나 버그가 있다면 이슈를 등록하거나 Pull Request를 보내주시기 바랍니다.
- 다양한 포스팅 플랫폼에 맞춘 디자인 개선 방안, 자동 업로드 기능 등의 추가 기능 기여도 환영합니다.

---

## 실행 환경

- Python 3.x  
- [Pillow](https://python-pillow.org/) (이미지 처리 라이브러리)
- Windows 환경: 한글 폰트(`malgun.ttf`, `malgunbd.ttf`) 사용

---

## 설치 및 실행 방법

1. **필수 패키지 설치 (Pillow)**
   ```powershell
   pip install pillow
   ```

2. **텍스트 파일 준비**  
   - 예: `data/input/이승철 - 그 사람.txt`  
   - 파일 내에는 AI로 생성된 전체 가사와 코드가 포함되어 있어야 합니다.

3. **이미지 변환 실행**
   ```powershell
   python convert_text_to_image.py data/input
   ```

4. **결과 확인**  
   - 변환된 이미지 파일과 원본 텍스트 파일은 `output` 폴더로 이동됩니다.

---

## 참고

- AI를 활용한 콘텐츠 생성과 텍스트 기반 이미지 변환을 효율적으로 결합하여, 사용자가 직접 콘텐츠를 제작 및 포스팅할 수 있도록 고안되었습니다.
- 본 도구는 간편하면서도 확장 가능한 구조를 가지고 있으므로, 자유롭게 기능 추가 및 개선이 가능합니다.

---

© 2023 GenChord - 모두의 콘텐츠 제작을 위한 오픈소스 프로젝트