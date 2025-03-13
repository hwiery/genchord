import requests
from bs4 import BeautifulSoup
import time
import json
import os
import random
from datetime import datetime

# 결과를 저장할 파일 경로
OUTPUT_FILE = 'scraped_songs.txt'
# 로그 파일 경로
LOG_FILE = 'scraper_log.txt'
# 마지막으로 스크래핑한 페이지를 저장할 파일
LAST_PAGE_FILE = 'last_page.txt'
# 시작 URL (난이도 2인 탭)
BASE_URL = 'https://www.ultimate-guitar.com/explore'
PARAMS = {'difficulty[]': '2'}
# 페이지 파라미터
PAGE_PARAM = 'page'
# 기본 시작 페이지
DEFAULT_START_PAGE = 1
# 요청 간 대기 시간 (초)
WAIT_TIME = random.uniform(5, 10)  # 대기 시간 증가
# 최대 재시도 횟수
MAX_RETRIES = 3
# 디버그 모드
DEBUG = True

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

def analyze_page_structure(html_content):
    """페이지 구조를 분석하여 테이블과 행을 찾는 함수"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 모든 테이블 찾기
    tables = soup.find_all('table')
    log_message(f"페이지에서 {len(tables)}개의 테이블을 찾았습니다.")
    
    for i, table in enumerate(tables):
        # 테이블 클래스 정보 기록
        table_classes = table.get('class', [])
        log_message(f"테이블 {i+1} 클래스: {' '.join(table_classes)}")
        
        # 행 개수 확인
        rows = table.find_all('tr')
        log_message(f"테이블 {i+1}에서 {len(rows)}개의 행을 찾았습니다.")
        
        # 첫 번째 행의 열 정보 확인
        if rows:
            first_row = rows[0]
            columns = first_row.find_all(['th', 'td'])
            column_texts = [col.get_text(strip=True) for col in columns]
            log_message(f"첫 번째 행의 열: {column_texts}")
    
    # 가능한 아티스트/노래 링크 패턴 찾기
    artist_links = soup.find_all('a', href=lambda href: href and '/artist/' in href)
    song_links = soup.find_all('a', href=lambda href: href and '/tabs/' in href)
    
    log_message(f"아티스트 링크 후보: {len(artist_links)}개")
    log_message(f"노래 링크 후보: {len(song_links)}개")
    
    return tables, artist_links, song_links

def get_random_user_agent():
    """랜덤 User-Agent를 반환합니다."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    ]
    return random.choice(user_agents)

def scrape_page(page_num):
    """지정된 페이지에서 아티스트와 노래 정보를 스크래핑합니다."""
    params = PARAMS.copy()
    params[PAGE_PARAM] = page_num
    
    for retry in range(MAX_RETRIES):
        try:
            # 랜덤 User-Agent 및 추가 헤더 설정
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.ultimate-guitar.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
            
            # 세션 사용
            session = requests.Session()
            
            # 먼저 메인 페이지 방문
            session.get('https://www.ultimate-guitar.com/', headers=headers)
            
            # 잠시 대기
            time.sleep(random.uniform(1, 3))
            
            # 실제 타겟 페이지 요청
            response = session.get(BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            
            # 디버그 모드에서 첫 페이지 구조 분석
            if DEBUG and page_num == DEFAULT_START_PAGE:
                log_message("페이지 구조 분석 중...")
                tables, artist_links, song_links = analyze_page_structure(response.text)
                
                # 페이지 소스 저장
                debug_file = f'page_{page_num}_source.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                log_message(f"페이지 소스를 {debug_file}에 저장했습니다.")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 여러 가능한 선택자 시도
            table_rows = []
            
            # 1. 클래스 이름으로 시도
            table_rows = soup.select('table tr')
            
            # 2. 아티스트/노래 링크 패턴으로 시도
            if not table_rows:
                artist_links = soup.find_all('a', href=lambda href: href and '/artist/' in href)
                song_links = soup.find_all('a', href=lambda href: href and '/tabs/' in href)
                
                # 아티스트와 노래 링크가 같은 수준에 있는지 확인
                if len(artist_links) > 0 and len(artist_links) == len(song_links):
                    log_message(f"링크 패턴으로 {len(artist_links)}개의 항목을 찾았습니다.")
                    
                    count = 0
                    for artist_link, song_link in zip(artist_links, song_links):
                        artist = artist_link.get_text(strip=True)
                        song = song_link.get_text(strip=True)
                        
                        if artist and song:
                            save_data(artist, song)
                            count += 1
                    
                    log_message(f"페이지 {page_num}에서 {count}개의 항목을 스크래핑했습니다.")
                    return True
            
            if not table_rows:
                log_message(f"페이지 {page_num}에서 테이블 데이터를 찾을 수 없습니다.")
                # 페이지 소스 확인을 위한 디버깅
                with open(f'page_{page_num}_source.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return False
            
            count = 0
            for row in table_rows:
                try:
                    # 헤더 행 건너뛰기
                    if row.find('th'):
                        continue
                        
                    # 아티스트와 노래 정보 추출 (여러 패턴 시도)
                    cells = row.find_all('td')
                    
                    if len(cells) >= 2:
                        # 첫 번째 셀에서 아티스트 찾기
                        artist_elem = cells[0].find('a')
                        # 두 번째 셀에서 노래 찾기
                        song_elem = cells[1].find('a')
                        
                        if artist_elem and song_elem:
                            artist = artist_elem.get_text(strip=True)
                            song = song_elem.get_text(strip=True)
                            
                            if artist and song:
                                save_data(artist, song)
                                count += 1
                except Exception as e:
                    log_message(f"행 파싱 중 오류 발생: {str(e)}")
            
            log_message(f"페이지 {page_num}에서 {count}개의 항목을 스크래핑했습니다.")
            return count > 0
            
        except requests.exceptions.RequestException as e:
            log_message(f"페이지 {page_num} 요청 중 오류 발생 (시도 {retry+1}/{MAX_RETRIES}): {str(e)}")
            time.sleep(WAIT_TIME * 2)  # 오류 발생 시 대기 시간 증가
    
    log_message(f"페이지 {page_num} 스크래핑 실패: 최대 재시도 횟수 초과")
    return False

def main():
    """메인 스크래핑 함수"""
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
    
    try:
        while True:
            log_message(f"페이지 {current_page} 스크래핑 중...")
            success = scrape_page(current_page)
            
            if success:
                save_last_page(current_page)
                current_page += 1
                time.sleep(WAIT_TIME)  # 요청 간 대기
            else:
                log_message(f"페이지 {current_page} 스크래핑 실패, 다음 실행 시 재시도합니다.")
                break
                
    except KeyboardInterrupt:
        log_message("사용자에 의해 스크래핑이 중단되었습니다.")
    except Exception as e:
        log_message(f"예상치 못한 오류 발생: {str(e)}")
    
    log_message(f"스크래핑 완료: 마지막 페이지 {current_page-1}")

if __name__ == "__main__":
    main() 