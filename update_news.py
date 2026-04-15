import os
import requests
import json
from datetime import datetime, timedelta

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
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get('items', [])
    except:
        pass
    return []

# 데이터 수집
# 1번칸: 속보 (최신순으로 가져와서 48시간 라벨링)
pane1_news = get_news("속보", 30)

# 2번칸: 부처/기관 소식 합산
combined_keywords = "산업부 KIAT 기후부 산업혁신기반구축"
pane2_news = get_news(combined_keywords, 30)

# 3번칸: 개별 키워드 모니터링 (클릭 시 전환용)
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

print("✅ news.json 업데이트 완료")
