import os
import requests
import json
from datetime import datetime

# 깃허브 Secrets에서 키 불러오기
CLIENT_ID = os.environ.get("NAVID")
CLIENT_SECRET = os.environ.get("NAVPASS")

def get_news(keyword, display=20):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {"query": keyword, "display": display, "sort": "date"}
    try:
        print(f"[{keyword}] 키워드 네이버에 요청 중...")
        # 💡 바로 이 부분! params=params 를 빼먹어서 에러가 났던 것을 수정했습니다.
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 200:
            print(f" ✅ 성공! ({len(res.json().get('items', []))}개 기사 수집)")
            return res.json().get('items', [])
        else:
            print(f" ❌ 에러 발생 (코드: {res.status_code}): {res.text}")
    except Exception as e:
        print(f" ❌ 치명적 오류: {e}")
    return []

# 데이터 수집
pane1_news = get_news("속보", 30)
combined_keywords = "산업부 KIAT 기후부 산업혁신기반구축"
pane2_news = get_news(combined_keywords, 30)
keywords = ["호르무즈", "트럼프", "유가", "코스피"]
pane3_data = {kw: get_news(kw, 20) for kw in keywords}

# 통합 데이터 구조 생성
final_data = {
    "pane1": pane1_news,
    "pane2": pane2_news,
    "pane3": pane3_data,
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# 파일 저장
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print("✅ news.json 업데이트 시도 완료")
