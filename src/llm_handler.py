import requests
import json

class LLMHandler:
    def __init__(self):
        self.api_base = "http://localhost:11434/api"
        self.model = "deepseek-coder:6.7b"
        
    def _generate(self, prompt):
        """Ollama API를 사용하여 텍스트 생성"""
        response = requests.post(
            f"{self.api_base}/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 더 정확한 결과를 위해 낮춤
                    "top_p": 0.8,
                    "top_k": 40,
                    "num_ctx": 4096
                }
            }
        )
        return response.json()["response"]
        
    def generate_chord_progression(self, artist, title):
        """코드 진행 생성"""
        prompt = f"""당신은 전문 기타리스트이자 음악 전문가입니다. 
다음 곡의 실제 기타 코드와 가사를 정확하게 알려주세요.
실제 곡의 정보만을 제공하고, 없는 정보는 제공하지 마세요.

아티스트: {artist}
제목: {title}

출력 형식:
{artist} - {title}

[Intro]
Am    Em    (실제 인트로 코드만 표시)

[Verse 1]
C              G
실제 가사 첫째 줄
Am             Em
실제 가사 둘째 줄

[Chorus]
F              G
실제 가사 첫째 줄
Am             Em
실제 가사 둘째 줄

주의사항:
1. 실제 곡의 정확한 코드와 가사만 표시
2. 확실하지 않은 정보는 포함하지 않음
3. 가사는 한글로 정확하게 표기
4. 코드는 기타 코드로 표기
5. 섹션은 명확히 구분
6. 코드와 가사의 정렬을 맞춰서 표시

실제 곡의 코드와 가사 정보만을 제공해주세요."""
        
        return self._generate(prompt)
        
    def generate_song_description(self, artist, title, chord_progression):
        """곡 설명 생성"""
        prompt = f"""당신은 음악 블로거이자 기타리스트입니다. 
다음 곡에 대한 실제 정보를 바탕으로 블로그 글을 작성해주세요.
추측성 내용이나 불확실한 정보는 제외하고, 실제 사실만을 포함해주세요.

아티스트: {artist}
제목: {title}

작성할 내용:

🎸 안녕하세요!
- 방문자 인사
- 오늘 소개할 곡 간단 소개

🎵 곡 정보
- 발매 연도
- 수록 앨범
- 작사, 작곡가
- 장르
- 대중적 인기도

✨ 연주 정보
- 기본 연주 난이도
- 주요 코드 진행
- 주의할 부분
- 초보자를 위한 팁

💝 마무리
- 곡의 특징 요약
- 응원 메시지

📝 코드 진행
{chord_progression}

주의사항:
- 실제 사실만 포함
- 한글로 작성
- 친근한 어조 사용
- 이모지 활용
- 명확한 정보만 전달"""
        
        return self._generate(prompt) 