import json
import requests
import os
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. API 및 기본 설정
gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

BASE_URL = "https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

# 2. 기존 데이터 로드
EVENTS_FILE = 'events.json'
try:
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        events = json.load(f)
    existing_titles = [event.get('title', '') for event in events]
except FileNotFoundError:
    events = []
    existing_titles = []

new_events_found = 0
page_index = 1
stop_crawling = False

print("🌐 KIAT 사업공고 탐색 시작 (2025년 3월 이후)")

while not stop_crawling:
    url = f"{BASE_URL}&pageIndex={page_index}"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 3. KIAT 게시판의 특수한 구조에 맞춘 정밀 타격
    # 클래스명에 공백이 많으므로 'td_title'이 포함된 모든 td를 찾습니다.
    rows = soup.find_all('tr')
    
    if not rows or page_index > 3: # 3페이지까지만 탐색
        break

    for row in rows:
        # 제목 태그 찾기 (td_title 클래스를 포함하는 td 안의 a 태그)
        td_title = row.find('td', class_=lambda x: x and 'td_title' in x)
        td_date = row.find('td', class_=lambda x: x and 'td_reg_date' in x)

        if not td_title or not td_date:
            continue

        title_elem = td_title.find('a')
        if not title_elem:
            continue

        raw_title = title_elem.text.strip()
        raw_date = td_date.text.strip()
        post_date_str = re.sub(r'[^0-9\-]', '', raw_date.replace('.', '-'))

        # 로그 출력 (봇이 지금 뭘 보고 있는지 CMD창에 강제로 띄웁니다)
        print(f"👀 발견한 공고: [{post_date_str}] {raw_title[:30]}...")

        # 시간 방어선
        if post_date_str < "2025-03-01":
            print(f"🛑 기준일 이전 공고 발견. 탐색 종료.")
            stop_crawling = True
            break
            
        # 키워드 필터링 (기반구축)
        if "기반구축" not in raw_title:
            continue

        if any(raw_title in existing_title for existing_title in existing_titles):
            print(f"⏩ 이미 등록됨: {raw_title}")
            continue

        print(f"✨ [대상 선정] 기반구축 공고 분석 시작!")
        
        # 자바스크립트 ID 추출 (연구원님이 주신 바로 그 ID!)
        href_val = title_elem.get('href', '')
        content_id_match = re.search(r"contentsView\('([^']+)'\)", href_val)
        
        if content_id_match:
            content_id = content_id_match.group(1)
            detail_url = f"https://kiat.or.kr/front/board/boardContentsView.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e&contents_id={content_id}"
            
            # 상세 페이지 분석
            detail_resp = requests.get(detail_url, headers=HEADERS)
            detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
            content_text = detail_soup.text.strip()[:2000]

            prompt = f"""
            정부 공고문에서 '사업명', '시작일', '종료일'을 추출해.
            날짜: YYYY-MM-DD. 
            예시: [ {{"title": "[KIAT] 사업명", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "color": "#0f9d58", "url": "{detail_url}"}} ]
            텍스트: {content_text}
            """

            try:
                ai_response = model.generate_content(prompt)
                clean_json = ai_response.text.replace('```json', '').replace('```', '').strip()
                new_item = json.loads(clean_json)
                events.extend(new_item)
                new_events_found += len(new_item)
                time.sleep(1)
            except Exception as e:
                print(f"❌ 분석 실패: {e}")

    page_index += 1

# 4. 결과 저장
if new_events_found > 0:
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"🎉 성공! {new_events_found}개의 공고를 달력에 넣었습니다.")
else:
    print("🤷‍♂️ 조건에 맞는 새로운 기반구축 사업이 없습니다.")
