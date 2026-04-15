import os
import requests
import json
from datetime import datetime

# 깃허브 Secrets에서 키 불러오기
CLIENT_ID = os.environ.get("NAVID")
CLIENT_SECRET = os.environ.get("NAVPASS")

def get_news(keyword):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {"query": keyword, "display": 10, "sort": "date"}
    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        return res.json().get('items', [])
    return []

# 3개 섹션 뉴스 수집
news_data = {
    "major": get_news("속보"),       # 첫 번째 칸: 주요뉴스(속보)
    "industry": get_news("산업부"),  # 두 번째 칸: 산업부
    "trump": get_news("트럼프"),     # 세 번째 칸: 트럼프
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# news.json 파일로 저장
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)

print("✅ 뉴스 데이터 업데이트 완료!")
