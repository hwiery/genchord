GenChord/
├── data/
│   ├── input/
│   │   └── song_list.txt        # 아티스트와 곡 목록
│   └── output/
│       ├── images/              # 코드 진행 이미지
│       └── descriptions/        # 곡 설명 텍스트
├── src/
│   ├── main.py                 # 메인 실행 파일
│   ├── llm_handler.py          # Ollama 통합 관리
│   ├── chord_generator.py      # 코드 진행 생성 및 이미지 변환
│   ├── text_generator.py       # 설명문 생성
│   └── scheduler.py            # 스케줄링 관리
├── requirements.txt
└── README.md