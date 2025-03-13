import asyncio
import time
import os
import json
import random
import re
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
PAGE_WAIT_TIME = random.uniform(3, 5)
# 최대 재시도 횟수
MAX_RETRIES = 3
# 페이지 로드 타임아웃 (초)
PAGE_LOAD_TIMEOUT = 30000  # 밀리초 단위 (30초)
# 코드와 가사를 저장할 디렉토리
OUTPUT_DIR = 'input'

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

def sanitize_filename(filename):
    """파일 이름에 사용할 수 없는 문자를 제거합니다."""
    # 파일 이름에 사용할 수 없는 문자 제거
    sanitized = re.sub(r'[\\/*?:"<>|]', '', filename)
    # 공백 문자를 언더스코어로 대체
    sanitized = sanitized.replace(' ', '_')
    return sanitized

def save_chord_and_lyrics(artist, song, content):
    """기타 코드와 가사를 파일로 저장합니다."""
    # 출력 디렉토리가 없으면 생성
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # 파일 이름 생성 (아티스트 - 노래.txt)
    filename = f"{artist} - {song}.txt"
    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(OUTPUT_DIR, sanitized_filename)
    
    # 파일에 내용 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    log_message(f"기타 코드와 가사를 저장했습니다: {file_path}")

async def navigate_to_page(page, url, description="페이지"):
    """지정된 URL로 이동합니다."""
    for retry in range(MAX_RETRIES):
        try:
            # 페이지 이동 (타임아웃 설정)
            await page.goto(url, timeout=PAGE_LOAD_TIMEOUT)
            
            # 페이지가 로드될 때까지 대기
            try:
                await page.wait_for_load_state('domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                log_message(f"{description} 기본 로드 완료: {url}")
            except Exception as e:
                log_message(f"{description} 로드 상태 대기 중 오류 발생: {str(e)}")
                # 오류가 발생해도 계속 진행
            
            # 추가 대기 (자바스크립트 로딩 등을 위해)
            await asyncio.sleep(random.uniform(1, 3))
            
            return True
        except Exception as e:
            log_message(f"{description} 로드 중 오류 발생 (시도 {retry+1}/{MAX_RETRIES}): {str(e)}")
            if retry < MAX_RETRIES - 1:
                await asyncio.sleep(PAGE_WAIT_TIME)
    
    return False

async def find_song_links(page):
    """페이지에서 노래 링크를 찾습니다."""
    try:
        # 여러 가능한 선택자 시도
        selectors = [
            'table tr td a[href*="/tabs/"]',  # 테이블 내 노래 링크
            'a[href*="/tabs/"]',              # 모든 노래 링크
            '.js-store a[href*="/tabs/"]',    # 스토어 내 노래 링크
            'div[class*="list"] a[href*="/tabs/"]'  # 리스트 내 노래 링크
        ]
        
        song_links = []
        for selector in selectors:
            try:
                links = await page.query_selector_all(selector)
                if links:
                    log_message(f"선택자 '{selector}'로 {len(links)}개의 노래 링크를 찾았습니다.")
                    
                    for link in links:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        
                        # 아티스트 정보 찾기
                        artist_elem = None
                        parent = await link.evaluate('node => node.parentElement')
                        parent_html = await page.evaluate('node => node.outerHTML', parent)
                        
                        # 부모 요소에서 아티스트 링크 찾기
                        artist_match = re.search(r'<a[^>]*href="[^"]*\/artist\/[^"]*"[^>]*>([^<]+)<\/a>', parent_html)
                        artist = artist_match.group(1).strip() if artist_match else "Unknown Artist"
                        
                        # 아티스트를 찾지 못한 경우 다른 방법 시도
                        if artist == "Unknown Artist":
                            # 테이블 행에서 첫 번째 셀이 아티스트일 가능성이 높음
                            try:
                                row = await link.evaluate('node => node.closest("tr")')
                                row_html = await page.evaluate('node => node.outerHTML', row)
                                
                                # 첫 번째 셀에서 텍스트 추출
                                first_cell_match = re.search(r'<td[^>]*>.*?<a[^>]*>([^<]+)<\/a>', row_html)
                                if first_cell_match:
                                    artist = first_cell_match.group(1).strip()
                            except:
                                pass
                        
                        song_links.append({
                            'url': href,
                            'song': text.strip(),
                            'artist': artist
                        })
                    
                    break
            except Exception as e:
                log_message(f"선택자 '{selector}' 검색 중 오류 발생: {str(e)}")
        
        # 중복 제거
        unique_links = []
        seen_urls = set()
        for link in song_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        log_message(f"총 {len(unique_links)}개의 고유한 노래 링크를 찾았습니다.")
        return unique_links
    
    except Exception as e:
        log_message(f"노래 링크 찾기 중 오류 발생: {str(e)}")
        return []

async def extract_chord_and_lyrics(page, url, artist, song):
    """노래 페이지에서 기타 코드와 가사를 추출합니다."""
    try:
        # 노래 페이지로 이동
        success = await navigate_to_page(page, url, f"노래 페이지 ({song})")
        if not success:
            log_message(f"노래 페이지 로드 실패: {url}")
            return False
        
        # 페이지 스크린샷 저장 (디버깅용)
        try:
            await page.screenshot(path=os.path.join(OUTPUT_DIR, f"{sanitize_filename(artist)}__{sanitize_filename(song)}_screenshot.png"))
        except Exception as e:
            log_message(f"스크린샷 저장 중 오류 발생: {str(e)}")
        
        # 코드와 가사 컨테이너 찾기 - 더 정확한 선택자 사용
        selectors = [
            'div[class*="Tablature"] pre',  # 탭 콘텐츠
            'div[data-content="tab"] pre',  # 탭 데이터 콘텐츠
            'div[class*="Tablature"] code', # 코드 블록
            'pre[class*="chord"]',          # 코드 pre 태그
            'div[class*="chord"]',          # 코드 div
            'div[class*="lyrics"]',         # 가사 div
            'div[class*="ugm-tab-content"]', # UG 탭 콘텐츠
            'div[class*="js-tab-content"]'   # JS 탭 콘텐츠
        ]
        
        content = ""
        for selector in selectors:
            try:
                container = await page.query_selector(selector)
                if container:
                    log_message(f"선택자 '{selector}'로 코드/가사 컨테이너를 찾았습니다.")
                    content = await container.inner_text()
                    break
            except Exception as e:
                log_message(f"선택자 '{selector}' 검색 중 오류 발생: {str(e)}")
        
        # 직접 JavaScript로 탭 콘텐츠 추출 시도
        if not content:
            try:
                content = await page.evaluate("""
                    () => {
                        // 다양한 방법으로 탭 콘텐츠 찾기
                        const tabContent = document.querySelector('div[data-content="tab"] pre') || 
                                          document.querySelector('div[class*="Tablature"] pre') ||
                                          document.querySelector('div[class*="ugm-tab-content"]') ||
                                          document.querySelector('div[class*="js-tab-content"]');
                        
                        if (tabContent) {
                            return tabContent.innerText;
                        }
                        
                        // 코드 블록 찾기
                        const codeBlocks = document.querySelectorAll('code, pre');
                        for (const block of codeBlocks) {
                            const text = block.innerText;
                            // 코드 패턴 확인 (예: Em G C)
                            if (/[A-G][#b]?m?(?:maj|min|aug|dim|sus|add)?[0-9]?/.test(text)) {
                                return text;
                            }
                        }
                        
                        return '';
                    }
                """)
                
                if content:
                    log_message("JavaScript로 탭 콘텐츠를 추출했습니다.")
            except Exception as e:
                log_message(f"JavaScript 탭 콘텐츠 추출 중 오류 발생: {str(e)}")
        
        # 페이지 소스 저장 (디버깅용)
        try:
            html_content = await page.content()
            with open(os.path.join(OUTPUT_DIR, f"{sanitize_filename(artist)}__{sanitize_filename(song)}_source.html"), 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            log_message(f"페이지 소스 저장 중 오류 발생: {str(e)}")
        
        if not content:
            # 페이지 전체 텍스트에서 코드와 가사 패턴 찾기
            page_text = await page.evaluate("document.body.innerText")
            
            # 코드 패턴 (예: Em G C)
            chord_pattern = r'([A-G][#b]?m?(?:maj|min|aug|dim|sus|add)?[0-9]?(?:\/[A-G][#b]?)?)'
            
            # 코드 라인 찾기
            chord_lines = []
            lines = page_text.split('\n')
            for line in lines:
                # 코드 패턴이 2개 이상 포함된 라인 찾기
                if len(re.findall(chord_pattern, line)) >= 2:
                    chord_lines.append(line)
            
            # 코드 라인 주변의 텍스트 추출 (가사로 가정)
            if chord_lines:
                # 첫 번째 코드 라인의 인덱스 찾기
                first_chord_line = chord_lines[0]
                try:
                    first_index = lines.index(first_chord_line)
                    # 코드 라인 앞뒤로 추출
                    start_index = max(0, first_index - 20)
                    end_index = min(len(lines), first_index + 100)
                    content = '\n'.join(lines[start_index:end_index])
                except ValueError:
                    content = '\n'.join(chord_lines)
        
        if content:
            # 내용 정리
            content = content.strip()
            
            # 불필요한 텍스트 제거
            content = re.sub(r'Transpose\s*\+\d+\s*\-\d+', '', content)
            content = re.sub(r'Print', '', content)
            content = re.sub(r'Report', '', content)
            content = re.sub(r'Favorite', '', content)
            
            # 파일로 저장
            save_chord_and_lyrics(artist, song, content)
            return True
        else:
            log_message(f"코드와 가사를 찾을 수 없습니다: {url}")
            return False
    
    except Exception as e:
        log_message(f"코드와 가사 추출 중 오류 발생: {str(e)}")
        return False

async def process_song_list_page(page, page_num):
    """노래 목록 페이지를 처리합니다."""
    # 페이지 URL 생성
    url = f"{BASE_URL}&page={page_num}"
    
    # 페이지로 이동
    success = await navigate_to_page(page, url, f"목록 페이지 {page_num}")
    if not success:
        log_message(f"페이지 {page_num}로 이동 실패")
        return False
    
    # 노래 링크 찾기
    song_links = await find_song_links(page)
    if not song_links:
        log_message(f"페이지 {page_num}에서 노래 링크를 찾을 수 없습니다.")
        return False
    
    # 각 노래 처리
    processed_count = 0
    for link in song_links:
        artist = link['artist']
        song = link['song']
        url = link['url']
        
        log_message(f"노래 처리 중: {artist} - {song}")
        
        # 아티스트와 노래 정보 저장
        save_data(artist, song)
        
        # 코드와 가사 추출
        success = await extract_chord_and_lyrics(page, url, artist, song)
        if success:
            processed_count += 1
        
        # 요청 간 대기
        await asyncio.sleep(random.uniform(1, 3))
    
    log_message(f"페이지 {page_num}에서 {processed_count}/{len(song_links)}개의 노래를 처리했습니다.")
    return processed_count > 0

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
    
    # 출력 디렉토리가 없으면 생성
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
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
                log_message(f"페이지 {current_page} 처리 중...")
                
                # 페이지 처리
                success = await process_song_list_page(page, current_page)
                
                if success:
                    save_last_page(current_page)
                    current_page += 1
                    await asyncio.sleep(PAGE_WAIT_TIME)  # 페이지 간 대기
                else:
                    log_message(f"페이지 {current_page} 처리 실패, 다음 실행 시 재시도합니다.")
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