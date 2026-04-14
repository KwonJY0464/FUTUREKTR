import json
import requests
import os
import time
import re
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. AI 설정 (일정 분석용)
gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. [핵심] 연구원님의 브라우저 정보를 100% 복제한 헤더
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://kiat.or.kr/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1'
}

BASE_URL = "https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e"

def run_scrapper():
    # 세션을 사용해 쿠키를 자동으로 관리합니다.
    session = requests.Session()
    
    print("🚶 1단계: KIAT 메인 페이지에 방문하여 '통행증(Cookie)'을 발급받습니다.")
    session.get("https://kiat.or.kr/front/user/main.do", headers=HEADERS, timeout=15)
    time.sleep(3) # 사람처럼 잠시 대기
    
    print("🌐 2단계: '기반구축' 공고 게시판으로 진입합니다.")
    response = session.get(BASE_URL, headers=HEADERS, timeout=20)
    
    # 인코딩 문제 해결 (한글 깨짐 방지)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # 모든 'a' 태그 중 contentsView 가 포함된 링크 수집
    all_links = soup.find_all('a', href=re.compile(r"contentsView"))
    print(f"📋 총 {len(all_links)}개의 게시글 링크를 발견했습니다.")

    events = []
    # 기존 데이터 로드 시도
    if os.path.exists('events.json'):
        with open('events.json', 'r', encoding='utf-8') as f:
            events = json.load(f)

    new_found = 0
    for link in all_links:
        title = link.text.strip()
        
        # [연구원님 커스텀 필터] 오직 '기반구축'만!
        if "기반구축" not in title:
            continue
            
        # 중복 체크
        if any(title in e.get('title', '') for e in events):
            continue

        print(f"✨ [새 사업 발견!] : {title}")
        
        # 상세 페이지 ID 추출
        cid_match = re.search(r"contentsView\('([^']+)'\)", link['href'])
        if cid_match:
            cid = cid_match.group(1)
            detail_url = f"https://kiat.or.kr/front/board/boardContentsView.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e&contents_id={cid}"
            
            # 상세 페이지 접속 및 AI 분석
            try:
                d_res = session.get(detail_url, headers=HEADERS, timeout=15)
                d_soup = BeautifulSoup(d_res.text, 'html.parser')
                body_text = d_soup.text.strip()[:2000] # 상단 2000자만 추출

                prompt = f"다음 사업공고 텍스트에서 '사업명', '시작일', '종료일'을 추출해서 JSON으로만 대답해. 날짜: YYYY-MM-DD. [{{\"title\": \"[KIAT] {title}\", \"start\": \"YYYY-MM-DD\", \"end\": \"YYYY-MM-DD\", \"color\": \"#d32f2f\", \"url\": \"{detail_url}\"}}] \n내용: {body_text}"
                ai_res = model.generate_content(prompt)
                
                # JSON 결과만 파싱
                json_str = ai_res.text.replace('```json', '').replace('```', '').strip()
                item = json.loads(json_str)
                events.extend(item)
                new_found += 1
                time.sleep(2)
            except Exception as e:
                print(f"❌ 분석 중 오류: {e}")

    # 최종 저장
    if new_found > 0:
        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print(f"🎉 업데이트 완료: {new_found}개의 일정이 추가되었습니다.")
    else:
        print("🤷‍♂️ 새로 추가할 기반구축 사업이 없습니다.")

if __name__ == "__main__":
    run_scrapper()
