import asyncio
import time
import os
import json
import random
from datetime import datetime
from playwright.async_api import async_playwright

# 결과를 저장할 파일 경로
OUTPUT_FILE = 'scraped_songs.txt'
# 로그 파일 경로
LOG_FILE = 'scraper_log.txt'
# API 응답을 저장할 파일
API_RESPONSE_FILE = 'api_response.json'
# 시작 URL (난이도 2인 탭)
BASE_URL = 'https://www.ultimate-guitar.com/explore?difficulty[]=2'
# 페이지 로드 타임아웃 (초)
PAGE_LOAD_TIMEOUT = 30

def log_message(message):
    """로그 메시지를 파일에 기록합니다."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as log_file:
        log_file.write(log_entry)
    
    print(log_entry.strip())

def save_data(artist, song):
    """스크래핑한 데이터를 파일에 저장합니다."""
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{artist} - {song}\n")

async def monitor_api_requests(page):
    """API 요청을 모니터링하고 응답을 캡처합니다."""
    api_responses = []
    
    # 네트워크 요청 이벤트 리스너 설정
    async def on_response(response):
        try:
            url = response.url
            
            # API 응답으로 보이는 요청 필터링
            if 'api' in url.lower() or 'json' in url.lower() or 'data' in url.lower():
                log_message(f"API 응답 감지: {url}")
                
                try:
                    # JSON 응답 파싱 시도
                    json_response = await response.json()
                    api_responses.append({
                        'url': url,
                        'status': response.status,
                        'data': json_response
                    })
                    log_message(f"JSON 응답 캡처 성공: {url}")
                except:
                    # 텍스트 응답 파싱 시도
                    try:
                        text_response = await response.text()
                        api_responses.append({
                            'url': url,
                            'status': response.status,
                            'text': text_response[:1000]  # 텍스트가 너무 길 수 있으므로 일부만 저장
                        })
                        log_message(f"텍스트 응답 캡처 성공: {url}")
                    except:
                        log_message(f"응답 캡처 실패: {url}")
        except Exception as e:
            log_message(f"응답 처리 중 오류 발생: {str(e)}")
    
    # 이벤트 리스너 등록
    page.on('response', on_response)
    
    return api_responses

async def extract_data_from_api_responses(api_responses):
    """API 응답에서 아티스트와 노래 정보를 추출합니다."""
    count = 0
    
    # API 응답 저장
    with open(API_RESPONSE_FILE, 'w', encoding='utf-8') as f:
        json.dump(api_responses, f, indent=2)
    
    log_message(f"API 응답 {len(api_responses)}개를 {API_RESPONSE_FILE}에 저장했습니다.")
    
    # 각 API 응답 분석
    for response in api_responses:
        try:
            if 'data' in response:
                data = response['data']
                
                # 데이터 구조 분석
                if isinstance(data, dict):
                    # 가능한 데이터 구조 패턴 확인
                    if 'results' in data and isinstance(data['results'], list):
                        items = data['results']
                        log_message(f"'results' 키에서 {len(items)}개의 항목을 찾았습니다.")
                        
                        for item in items:
                            if isinstance(item, dict):
                                # 아티스트와 노래 정보 추출 시도
                                artist = None
                                song = None
                                
                                # 가능한 키 이름 시도
                                for artist_key in ['artist', 'artist_name', 'artistName', 'band', 'bandName']:
                                    if artist_key in item and item[artist_key]:
                                        artist = item[artist_key]
                                        break
                                
                                for song_key in ['song', 'song_name', 'songName', 'title', 'name', 'tab_title']:
                                    if song_key in item and item[song_key]:
                                        song = item[song_key]
                                        break
                                
                                if artist and song:
                                    save_data(artist, song)
                                    count += 1
                    
                    # 다른 가능한 데이터 구조 패턴
                    elif 'data' in data and isinstance(data['data'], list):
                        items = data['data']
                        log_message(f"'data' 키에서 {len(items)}개의 항목을 찾았습니다.")
                        
                        for item in items:
                            if isinstance(item, dict):
                                # 아티스트와 노래 정보 추출 시도
                                artist = None
                                song = None
                                
                                # 가능한 키 이름 시도
                                for artist_key in ['artist', 'artist_name', 'artistName', 'band', 'bandName']:
                                    if artist_key in item and item[artist_key]:
                                        artist = item[artist_key]
                                        break
                                
                                for song_key in ['song', 'song_name', 'songName', 'title', 'name', 'tab_title']:
                                    if song_key in item and item[song_key]:
                                        song = item[song_key]
                                        break
                                
                                if artist and song:
                                    save_data(artist, song)
                                    count += 1
        except Exception as e:
            log_message(f"API 응답 분석 중 오류 발생: {str(e)}")
    
    return count

async def main_async():
    """비동기 메인 스크래핑 함수"""
    # 로그 파일 초기화
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            pass
    
    # 출력 파일이 없으면 생성
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            pass
    
    log_message(f"API 스크래핑 시작")
    
    async with async_playwright() as p:
        # 브라우저 시작
        browser = await p.chromium.launch(headless=True)
        
        # 새 컨텍스트 생성 (쿠키, 캐시 등이 분리된 환경)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 자동화 감지 회피
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # 새 페이지 열기
        page = await context.new_page()
        
        try:
            # API 요청 모니터링 시작
            api_responses = []
            page.on('response', lambda response: asyncio.create_task(handle_response(response, api_responses)))
            
            async def handle_response(response, responses_list):
                try:
                    url = response.url
                    if 'api' in url.lower() or 'json' in url.lower() or 'data' in url.lower():
                        try:
                            json_response = await response.json()
                            responses_list.append({
                                'url': url,
                                'status': response.status,
                                'data': json_response
                            })
                            log_message(f"JSON 응답 캡처 성공: {url}")
                        except:
                            pass
                except:
                    pass
            
            # 페이지 이동
            log_message(f"페이지 로드 중: {BASE_URL}")
            await page.goto(BASE_URL, wait_until='networkidle')
            
            # 페이지가 완전히 로드될 때까지 대기
            log_message("페이지 로드 완료, 추가 네트워크 요청 대기 중...")
            await asyncio.sleep(10)  # 추가 API 요청을 위한 대기
            
            # 스크롤 다운하여 더 많은 API 요청 유도
            log_message("페이지 스크롤 중...")
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(2)
            
            # 페이지 스크린샷 저장
            await page.screenshot(path='page_screenshot.png')
            log_message("페이지 스크린샷을 저장했습니다: page_screenshot.png")
            
            # API 응답에서 데이터 추출
            log_message(f"API 응답 분석 중... ({len(api_responses)}개 응답)")
            count = await extract_data_from_api_responses(api_responses)
            
            if count > 0:
                log_message(f"총 {count}개의 항목을 스크래핑했습니다.")
            else:
                log_message("API 응답에서 데이터를 추출하지 못했습니다.")
                
                # 페이지 소스 저장
                html_content = await page.content()
                with open('page_source.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                log_message("페이지 소스를 저장했습니다: page_source.html")
                
        except Exception as e:
            log_message(f"예상치 못한 오류 발생: {str(e)}")
        finally:
            # 브라우저 종료
            await browser.close()
        
        log_message("API 스크래핑 완료")

def main():
    """메인 함수"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 