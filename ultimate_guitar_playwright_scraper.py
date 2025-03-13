import asyncio
import time
import os
import random
from datetime import datetime
from playwright.async_api import async_playwright

# 결과를 저장할 파일 경로
OUTPUT_FILE = 'scraped_songs.txt'
# 로그 파일 경로
LOG_FILE = 'scraper_log.txt'
# 마지막으로 스크래핑한 페이지를 저장할 파일
LAST_PAGE_FILE = 'last_page.txt'
# 시작 URL (난이도 2인 탭)
BASE_URL = 'https://www.ultimate-guitar.com/explore?difficulty[]=2'
# 기본 시작 페이지
DEFAULT_START_PAGE = 1
# 페이지 간 대기 시간 (초)
PAGE_WAIT_TIME = random.uniform(5, 10)
# 최대 재시도 횟수
MAX_RETRIES = 3

def log_message(message):
    """로그 메시지를 파일에 기록합니다."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as log_file:
        log_file.write(log_entry)
    
    print(log_entry.strip())

def save_last_page(page_num):
    """마지막으로 스크래핑한 페이지 번호를 저장합니다."""
    with open(LAST_PAGE_FILE, 'w') as f:
        f.write(str(page_num))

def get_last_page():
    """마지막으로 스크래핑한 페이지 번호를 가져옵니다."""
    if os.path.exists(LAST_PAGE_FILE):
        with open(LAST_PAGE_FILE, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return DEFAULT_START_PAGE
    return DEFAULT_START_PAGE

def save_data(artist, song):
    """스크래핑한 데이터를 파일에 저장합니다."""
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{artist} - {song}\n")

async def navigate_to_page(page, page_num):
    """특정 페이지로 이동합니다."""
    url = f"{BASE_URL}&page={page_num}"
    
    for retry in range(MAX_RETRIES):
        try:
            # 페이지 이동
            await page.goto(url, wait_until='domcontentloaded')
            
            # 페이지가 로드될 때까지 대기
            await page.wait_for_load_state('networkidle')
            
            # 추가 대기 (자바스크립트 로딩 등을 위해)
            await asyncio.sleep(random.uniform(2, 5))
            
            return True
        except Exception as e:
            log_message(f"페이지 {page_num} 로드 중 오류 발생 (시도 {retry+1}/{MAX_RETRIES}): {str(e)}")
            if retry < MAX_RETRIES - 1:
                await asyncio.sleep(PAGE_WAIT_TIME)
    
    return False

async def scrape_page_data(page, page_num):
    """현재 페이지에서 아티스트와 노래 정보를 스크래핑합니다."""
    try:
        # 페이지 소스 저장 (디버깅용)
        html_content = await page.content()
        with open(f'page_{page_num}_source.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 테이블 찾기 시도
        table = await page.query_selector('table')
        
        if not table:
            log_message(f"페이지 {page_num}에서 테이블을 찾을 수 없습니다.")
            
            # 다른 방법으로 시도 (링크 패턴)
            return await scrape_using_links(page, page_num)
        
        # 테이블 행 찾기
        rows = await table.query_selector_all('tr')
        
        if not rows:
            log_message(f"페이지 {page_num}에서 테이블 행을 찾을 수 없습니다.")
            return await scrape_using_links(page, page_num)
        
        count = 0
        # 첫 번째 행은 헤더일 수 있으므로 건너뜁니다
        for row in rows[1:]:
            try:
                # 셀 찾기
                cells = await row.query_selector_all('td')
                
                if len(cells) >= 2:
                    # 첫 번째 셀에서 아티스트 찾기
                    artist_elem = await cells[0].query_selector('a')
                    # 두 번째 셀에서 노래 찾기
                    song_elem = await cells[1].query_selector('a')
                    
                    if artist_elem and song_elem:
                        artist = await artist_elem.text_content()
                        song = await song_elem.text_content()
                        
                        artist = artist.strip()
                        song = song.strip()
                        
                        if artist and song:
                            save_data(artist, song)
                            count += 1
            except Exception as e:
                log_message(f"행 파싱 중 오류 발생: {str(e)}")
        
        log_message(f"페이지 {page_num}에서 {count}개의 항목을 스크래핑했습니다.")
        return count > 0
        
    except Exception as e:
        log_message(f"페이지 {page_num} 데이터 스크래핑 중 오류 발생: {str(e)}")
        return await scrape_using_links(page, page_num)

async def scrape_using_links(page, page_num):
    """링크 패턴을 사용하여 아티스트와 노래 정보를 스크래핑합니다."""
    try:
        # 아티스트 링크 찾기
        artist_links = await page.query_selector_all('a[href*="/artist/"]')
        # 노래 링크 찾기
        song_links = await page.query_selector_all('a[href*="/tabs/"]')
        
        if len(artist_links) > 0 and len(song_links) > 0:
            log_message(f"링크 패턴으로 아티스트 링크 {len(artist_links)}개, 노래 링크 {len(song_links)}개를 찾았습니다.")
            
            # 링크 텍스트 추출
            artists = []
            for link in artist_links:
                text = await link.text_content()
                artists.append(text.strip())
            
            songs = []
            for link in song_links:
                text = await link.text_content()
                songs.append(text.strip())
            
            # 아티스트와 노래 매칭
            count = 0
            for i in range(min(len(artists), len(songs))):
                artist = artists[i]
                song = songs[i]
                
                if artist and song:
                    save_data(artist, song)
                    count += 1
            
            log_message(f"페이지 {page_num}에서 {count}개의 항목을 스크래핑했습니다.")
            return count > 0
        else:
            log_message(f"페이지 {page_num}에서 링크 패턴을 찾을 수 없습니다.")
            return False
    except Exception as e:
        log_message(f"링크 패턴 스크래핑 중 오류 발생: {str(e)}")
        return False

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
    
    # 마지막으로 스크래핑한 페이지 가져오기
    start_page = get_last_page()
    current_page = start_page
    
    log_message(f"스크래핑 시작: 페이지 {current_page}부터")
    
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
            while True:
                log_message(f"페이지 {current_page} 스크래핑 중...")
                
                # 페이지로 이동
                if not await navigate_to_page(page, current_page):
                    log_message(f"페이지 {current_page}로 이동 실패")
                    break
                
                # 페이지 데이터 스크래핑
                success = await scrape_page_data(page, current_page)
                
                if success:
                    save_last_page(current_page)
                    current_page += 1
                    await asyncio.sleep(PAGE_WAIT_TIME)  # 페이지 간 대기
                else:
                    log_message(f"페이지 {current_page} 스크래핑 실패, 다음 실행 시 재시도합니다.")
                    break
                    
        except KeyboardInterrupt:
            log_message("사용자에 의해 스크래핑이 중단되었습니다.")
        except Exception as e:
            log_message(f"예상치 못한 오류 발생: {str(e)}")
        finally:
            # 브라우저 종료
            await browser.close()
        
        log_message(f"스크래핑 완료: 마지막 페이지 {current_page-1}")

def main():
    """메인 함수"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 