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
# 코드와 가사를 저장할 디렉토리
OUTPUT_DIR = 'input'
# 페이지 로드 타임아웃 (초)
PAGE_LOAD_TIMEOUT = 60000  # 밀리초 단위 (60초)
# 최대 재시도 횟수
MAX_RETRIES = 3

# 인기 있는 노래 URL 목록 (예시)
POPULAR_SONGS = [
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/oasis/wonderwall-chords-27596',
        'artist': 'Oasis',
        'song': 'Wonderwall'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/eagles/hotel-california-chords-46190',
        'artist': 'Eagles',
        'song': 'Hotel California'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-1086983',
        'artist': 'Radiohead',
        'song': 'Creep'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/bob-dylan/knockin-on-heavens-door-chords-66559',
        'artist': 'Bob Dylan',
        'song': 'Knockin On Heavens Door'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/4-non-blondes/whats-up-chords-1092984',
        'artist': '4 Non Blondes',
        'song': 'Whats Up'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/dolly-parton/jolene-chords-183029',
        'artist': 'Dolly Parton',
        'song': 'Jolene'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/nirvana/smells-like-teen-spirit-chords-807883',
        'artist': 'Nirvana',
        'song': 'Smells Like Teen Spirit'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/ben-e-king/stand-by-me-chords-1465412',
        'artist': 'Ben E. King',
        'song': 'Stand By Me'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/ed-sheeran/perfect-chords-1956589',
        'artist': 'Ed Sheeran',
        'song': 'Perfect'
    },
    {
        'url': 'https://tabs.ultimate-guitar.com/tab/john-legend/all-of-me-chords-1248282',
        'artist': 'John Legend',
        'song': 'All Of Me'
    }
]

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
                await asyncio.sleep(random.uniform(3, 5))
    
    return False

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
    
    log_message("인기 노래 스크래핑 시작")
    
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
            # 각 노래 처리
            processed_count = 0
            for song_info in POPULAR_SONGS:
                artist = song_info['artist']
                song = song_info['song']
                url = song_info['url']
                
                log_message(f"노래 처리 중: {artist} - {song} ({url})")
                
                # 아티스트와 노래 정보 저장
                save_data(artist, song)
                
                # 코드와 가사 추출
                success = await extract_chord_and_lyrics(page, url, artist, song)
                if success:
                    processed_count += 1
                
                # 요청 간 대기
                await asyncio.sleep(random.uniform(3, 5))
            
            log_message(f"총 {processed_count}/{len(POPULAR_SONGS)}개의 노래를 처리했습니다.")
                    
        except KeyboardInterrupt:
            log_message("사용자에 의해 스크래핑이 중단되었습니다.")
        except Exception as e:
            log_message(f"예상치 못한 오류 발생: {str(e)}")
        finally:
            # 브라우저 종료
            await browser.close()
        
        log_message("인기 노래 스크래핑 완료")

def main():
    """메인 함수"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 