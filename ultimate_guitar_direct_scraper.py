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
# 시작 URL (난이도 2인 탭, 인기순 정렬)
BASE_URL = 'https://www.ultimate-guitar.com/explore?difficulty[]=2&order=hitstotal_desc'
# 기본 시작 페이지
DEFAULT_START_PAGE = 1
# 페이지 간 대기 시간 (초)
PAGE_WAIT_TIME = random.uniform(3, 5)
# 최대 재시도 횟수
MAX_RETRIES = 3
# 페이지 로드 타임아웃 (초)
PAGE_LOAD_TIMEOUT = 60000  # 밀리초 단위 (60초)
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
            await asyncio.sleep(random.uniform(3, 5))
            
            return True
        except Exception as e:
            log_message(f"{description} 로드 중 오류 발생 (시도 {retry+1}/{MAX_RETRIES}): {str(e)}")
            if retry < MAX_RETRIES - 1:
                await asyncio.sleep(PAGE_WAIT_TIME)
    
    return False

async def find_song_links_by_color(page):
    """노란색 글씨로 된 노래 제목 링크를 찾습니다."""
    try:
        # 페이지 스크린샷 저장 (디버깅용)
        await page.screenshot(path='page_screenshot.png')
        log_message("페이지 스크린샷을 저장했습니다: page_screenshot.png")
        
        # 페이지 소스 저장 (디버깅용)
        html_content = await page.content()
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        log_message("페이지 소스를 저장했습니다: page_source.html")
        
        # 노란색 링크 또는 노래 제목 링크를 찾기 위한 여러 선택자 시도
        selectors = [
            'a[style*="color: yellow"]',  # 노란색 스타일을 가진 링크
            'a[style*="color: #ffff00"]',  # 노란색 16진수 코드를 가진 링크
            'a[class*="yellow"]',         # 노란색 클래스를 가진 링크
            'a[class*="song"]',           # song 클래스를 가진 링크
            'a[href*="/tabs/"]',          # /tabs/ 경로를 가진 링크
            'tr td:nth-child(2) a',       # 테이블의 두 번째 열에 있는 링크 (Song 컬럼)
            'tr a'                        # 테이블의 모든 링크
        ]
        
        song_links = []
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            log_message(f"선택자 '{selector}'로 {len(elements)}개의 요소를 찾았습니다.")
            
            if elements:
                for element in elements:
                    href = await element.get_attribute('href')
                    song_text = await element.inner_text()
                    
                    # 아티스트 정보 찾기
                    artist_text = "Unknown Artist"
                    
                    # 부모 요소에서 아티스트 정보 찾기
                    try:
                        parent_row = await element.evaluate('node => node.closest("tr")')
                        if parent_row:
                            # 첫 번째 열에서 아티스트 정보 찾기
                            artist_cell = await page.evaluate("""
                                (row) => {
                                    const cells = row.querySelectorAll('td');
                                    if (cells.length > 0) {
                                        const firstCell = cells[0];
                                        const artistLink = firstCell.querySelector('a');
                                        return artistLink ? artistLink.innerText.trim() : firstCell.innerText.trim();
                                    }
                                    return null;
                                }
                            """, parent_row)
                            
                            if artist_cell:
                                artist_text = artist_cell
                    except Exception as e:
                        log_message(f"아티스트 정보 찾기 중 오류 발생: {str(e)}")
                    
                    song_links.append({
                        'url': href,
                        'song': song_text.strip(),
                        'artist': artist_text.strip()
                    })
                
                # 링크를 찾았으면 반복 중단
                if song_links:
                    break
        
        # 링크를 찾지 못한 경우 JavaScript로 직접 찾기
        if not song_links:
            log_message("선택자로 링크를 찾지 못했습니다. JavaScript로 직접 찾습니다.")
            
            song_links_data = await page.evaluate("""
                () => {
                    // 모든 링크 요소 찾기
                    const allLinks = Array.from(document.querySelectorAll('a'));
                    
                    // 노래 링크 필터링
                    const songLinks = allLinks.filter(link => {
                        const href = link.getAttribute('href');
                        // 링크 URL이 /tabs/를 포함하거나 노란색 스타일을 가진 경우
                        return (href && href.includes('/tabs/')) || 
                               (link.style && (link.style.color === 'yellow' || link.style.color === '#ffff00')) ||
                               (link.className && link.className.includes('yellow'));
                    });
                    
                    // 링크 데이터 추출
                    return songLinks.map(link => {
                        // 링크 URL과 텍스트
                        const href = link.getAttribute('href');
                        const songText = link.innerText.trim();
                        
                        // 아티스트 정보 찾기
                        let artistText = "Unknown Artist";
                        
                        // 테이블 행에서 아티스트 찾기
                        const row = link.closest('tr');
                        if (row) {
                            const cells = Array.from(row.querySelectorAll('td'));
                            if (cells.length > 0) {
                                const firstCell = cells[0];
                                const artistLink = firstCell.querySelector('a');
                                if (artistLink) {
                                    artistText = artistLink.innerText.trim();
                                } else {
                                    artistText = firstCell.innerText.trim();
                                }
                            }
                        }
                        
                        return {
                            url: href,
                            song: songText,
                            artist: artistText
                        };
                    });
                }
            """)
            
            song_links = song_links_data
        
        # 중복 제거
        unique_links = []
        seen_urls = set()
        for link in song_links:
            if link['url'] and link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        log_message(f"총 {len(unique_links)}개의 고유한 노래 링크를 찾았습니다.")
        
        # 링크 정보 출력 (디버깅용)
        for i, link in enumerate(unique_links[:5]):  # 처음 5개만 출력
            log_message(f"링크 {i+1}: {link['artist']} - {link['song']} ({link['url']})")
        
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
        
        # 페이지 소스 저장 (디버깅용)
        try:
            html_content = await page.content()
            with open(os.path.join(OUTPUT_DIR, f"{sanitize_filename(artist)}__{sanitize_filename(song)}_source.html"), 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            log_message(f"페이지 소스 저장 중 오류 발생: {str(e)}")
        
        # 직접 JavaScript로 탭 콘텐츠 추출
        content = await page.evaluate("""
            () => {
                // 다양한 방법으로 탭 콘텐츠 찾기
                const tabContent = document.querySelector('div[data-content="tab"] pre') || 
                                  document.querySelector('div[class*="Tablature"] pre') ||
                                  document.querySelector('div[class*="ugm-tab-content"]') ||
                                  document.querySelector('div[class*="js-tab-content"]') ||
                                  document.querySelector('pre[class*="chord"]') ||
                                  document.querySelector('div[class*="chord"]') ||
                                  document.querySelector('div[class*="lyrics"]');
                
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
                
                // 페이지 전체 텍스트에서 코드 패턴 찾기
                const allText = document.body.innerText;
                const lines = allText.split('\\n');
                const chordLines = [];
                
                for (const line of lines) {
                    // 코드 패턴 확인 (예: Em G C)
                    const chordMatches = line.match(/[A-G][#b]?m?(?:maj|min|aug|dim|sus|add)?[0-9]?/g);
                    if (chordMatches && chordMatches.length >= 2) {
                        chordLines.push(line);
                    }
                }
                
                if (chordLines.length > 0) {
                    // 첫 번째 코드 라인 주변의 텍스트 추출
                    const firstChordLine = chordLines[0];
                    const firstIndex = lines.indexOf(firstChordLine);
                    
                    if (firstIndex !== -1) {
                        const startIndex = Math.max(0, firstIndex - 20);
                        const endIndex = Math.min(lines.length, firstIndex + 100);
                        return lines.slice(startIndex, endIndex).join('\\n');
                    } else {
                        return chordLines.join('\\n');
                    }
                }
                
                return '';
            }
        """)
        
        if content:
            log_message("JavaScript로 탭 콘텐츠를 추출했습니다.")
            
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
                    
                    # 내용 정리
                    content = content.strip()
                    
                    # 파일로 저장
                    save_chord_and_lyrics(artist, song, content)
                    return True
                except ValueError:
                    content = '\n'.join(chord_lines)
                    
                    # 내용 정리
                    content = content.strip()
                    
                    # 파일로 저장
                    save_chord_and_lyrics(artist, song, content)
                    return True
            
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
    song_links = await find_song_links_by_color(page)
    if not song_links:
        log_message(f"페이지 {page_num}에서 노래 링크를 찾을 수 없습니다.")
        return False
    
    # 각 노래 처리
    processed_count = 0
    for link in song_links:
        artist = link['artist']
        song = link['song']
        url = link['url']
        
        # URL이 상대 경로인 경우 절대 경로로 변환
        if url and not url.startswith('http'):
            url = f"https://www.ultimate-guitar.com{url}"
        
        log_message(f"노래 처리 중: {artist} - {song} ({url})")
        
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
        # 브라우저 시작 (헤드리스 모드 비활성화)
        browser = await p.chromium.launch(headless=False)
        
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