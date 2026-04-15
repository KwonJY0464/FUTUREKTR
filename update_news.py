import os
import requests
import json
from datetime import datetime
import google.generativeai as genai

# API 키 설정
CLIENT_ID = os.environ.get("NAVID")
CLIENT_SECRET = os.environ.get("NAVPASS")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_summary(text):
    try:
        prompt = f"다음 뉴스 내용을 2줄 이내의 아주 간결한 문장으로 요약해줘. 불필요한 수식어는 빼고 팩트만 전달해: {text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return text[:100] + "..." # 에러 시 원문 일부 반환

def get_news(keyword, display=15):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    params = {"query": keyword, "display": display, "sort": "date"}
    items = []
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            raw_items = res.json().get('items', [])
            for item in raw_items:
                # 네이버 뉴스 API는 썸네일을 직접 주지 않으므로, 
                # 여기서는 기본 이미지나 간단한 뉴스 아이콘을 매칭하거나 
                # 원문 링크에서 메타 정보를 추출해야 하지만, 속도를 위해 기본 처리합니다.
                item['ai_summary'] = get_ai_summary(item['description'])
                items.append(item)
    except: pass
    return items

# 수집 로직 (기존과 동일하되 AI 요약 포함)
pane1_news = get_news("속보", 10)
pane2_keywords = ["산업부", "KIAT", "기후부", "산업혁신기반구축"]
pane2_data = {kw: get_news(kw, 10) for kw in pane2_keywords}
pane3_keywords = ["호르무즈", "트럼프", "유가", "코스피"]
pane3_data = {kw: get_news(kw, 10) for kw in pane3_keywords}

final_data = {
    "pane1": pane1_news, "pane2": pane2_data, "pane3": pane3_data,
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)
