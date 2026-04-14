import requests
from bs4 import BeautifulSoup

# 연구원님이 캡처해주신 그 헤더 그대로 사용
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Referer': 'https://kiat.or.kr/'
}

BASE_URL = "https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e"

def diagnostic():
    session = requests.Session()
    # 1. 일단 접속
    res = session.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 2. 진단 결과 출력
    print(f"📡 응답 상태 코드: {res.status_code}") # 200이 나와야 정상
    print(f"📄 페이지 제목: {soup.title.text if soup.title else '제목 없음'}")
    print(f"📊 전체 글자 수: {len(res.text)}자")
    
    # 3. 만약 0개라면, 'iframe' 태그가 있는지 확인
    iframes = soup.find_all('iframe')
    print(f"🖼️ 발견된 아이프레임 개수: {len(iframes)}개")
    for i, f in enumerate(iframes):
        print(f"   -> 아이프레임 주소 {i+1}: {f.get('src')}")

    # 4. 본문 내용 살짝 엿보기 (가장 중요)
    print("-" * 30)
    print("👀 봇이 보고 있는 본문 (상단 500자):")
    print(res.text[:500])
    print("-" * 30)

if __name__ == "__main__":
    diagnostic()
