import time
import os
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

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
# 페이지 로드 타임아웃 (초)
PAGE_LOAD_TIMEOUT = 30

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

def setup_driver():
    """Selenium 웹드라이버를 설정합니다."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 헤드리스 모드 (화면 표시 없음)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    # 랜덤 User-Agent 설정
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # 자동화 감지 회피
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    try:
        # 웹드라이버 관리자를 사용하여 드라이버 설치 및 서비스 생성
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        return driver
    except WebDriverException as e:
        log_message(f"웹드라이버 설정 중 오류 발생: {str(e)}")
        raise

def navigate_to_page(driver, page_num):
    """특정 페이지로 이동합니다."""
    url = f"{BASE_URL}&page={page_num}"
    
    for retry in range(MAX_RETRIES):
        try:
            driver.get(url)
            
            # 페이지가 로드될 때까지 대기
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 추가 대기 (자바스크립트 로딩 등을 위해)
            time.sleep(random.uniform(2, 5))
            
            return True
        except (TimeoutException, WebDriverException) as e:
            log_message(f"페이지 {page_num} 로드 중 오류 발생 (시도 {retry+1}/{MAX_RETRIES}): {str(e)}")
            if retry < MAX_RETRIES - 1:
                time.sleep(PAGE_WAIT_TIME)
    
    return False

def scrape_page_data(driver, page_num):
    """현재 페이지에서 아티스트와 노래 정보를 스크래핑합니다."""
    try:
        # 테이블 찾기 시도
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        # 테이블 행 찾기
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        if not rows:
            log_message(f"페이지 {page_num}에서 테이블 행을 찾을 수 없습니다.")
            # 디버깅을 위해 페이지 소스 저장
            with open(f'page_{page_num}_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            return False
        
        count = 0
        # 첫 번째 행은 헤더일 수 있으므로 건너뜁니다
        for row in rows[1:]:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) >= 2:
                    # 첫 번째 셀에서 아티스트 찾기
                    artist_elem = cells[0].find_element(By.TAG_NAME, "a")
                    # 두 번째 셀에서 노래 찾기
                    song_elem = cells[1].find_element(By.TAG_NAME, "a")
                    
                    artist = artist_elem.text.strip()
                    song = song_elem.text.strip()
                    
                    if artist and song:
                        save_data(artist, song)
                        count += 1
            except (NoSuchElementException, IndexError) as e:
                log_message(f"행 파싱 중 오류 발생: {str(e)}")
        
        log_message(f"페이지 {page_num}에서 {count}개의 항목을 스크래핑했습니다.")
        return count > 0
        
    except (TimeoutException, NoSuchElementException) as e:
        log_message(f"페이지 {page_num} 데이터 스크래핑 중 오류 발생: {str(e)}")
        
        # 디버깅을 위해 페이지 소스 저장
        with open(f'page_{page_num}_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        # 다른 방법으로 시도 (링크 패턴)
        try:
            artist_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/artist/')]")
            song_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/tabs/')]")
            
            if len(artist_links) > 0 and len(artist_links) == len(song_links):
                log_message(f"링크 패턴으로 {len(artist_links)}개의 항목을 찾았습니다.")
                
                count = 0
                for artist_link, song_link in zip(artist_links, song_links):
                    artist = artist_link.text.strip()
                    song = song_link.text.strip()
                    
                    if artist and song:
                        save_data(artist, song)
                        count += 1
                
                log_message(f"페이지 {page_num}에서 {count}개의 항목을 스크래핑했습니다.")
                return count > 0
        except Exception as e2:
            log_message(f"대체 스크래핑 방법 중 오류 발생: {str(e2)}")
        
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
    
    driver = None
    try:
        # 웹드라이버 설정
        driver = setup_driver()
        
        while True:
            log_message(f"페이지 {current_page} 스크래핑 중...")
            
            # 페이지로 이동
            if not navigate_to_page(driver, current_page):
                log_message(f"페이지 {current_page}로 이동 실패")
                break
            
            # 페이지 데이터 스크래핑
            success = scrape_page_data(driver, current_page)
            
            if success:
                save_last_page(current_page)
                current_page += 1
                time.sleep(PAGE_WAIT_TIME)  # 페이지 간 대기
            else:
                log_message(f"페이지 {current_page} 스크래핑 실패, 다음 실행 시 재시도합니다.")
                break
                
    except KeyboardInterrupt:
        log_message("사용자에 의해 스크래핑이 중단되었습니다.")
    except Exception as e:
        log_message(f"예상치 못한 오류 발생: {str(e)}")
    finally:
        # 웹드라이버 종료
        if driver:
            driver.quit()
    
    log_message(f"스크래핑 완료: 마지막 페이지 {current_page-1}")

if __name__ == "__main__":
    main() 