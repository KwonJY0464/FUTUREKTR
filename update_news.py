import os
import requests
import json
import re
from datetime import datetime
import google.generativeai as genai

# API 및 모델 설정
CLIENT_ID = os.environ.get("NAVID")
CLIENT_SECRET = os.environ.get("NAVPASS")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def get_ai_summary(title, description):
    """AI 요약 안정화: 실패하거나 헛소리할 경우 원문을 정제해서 반환"""
    try:
        clean_desc = re.sub('<[^>]*>', '', description).replace('&quot;', '"')
        prompt = f"뉴스 제목: {title}\n내용: {clean_desc}\n\n위 내용을 2줄 이내로 핵심만 요약해. 사용자에게 말을 걸지 말고 오직 요약문만 출력해."
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        # AI가 "요약해 드릴게요" 등 말을 걸 경우 필터링
        if any(msg in summary for msg in ["요약", "제공", "하겠습니다", "말씀"]):
            if len(summary) > 100: # 너무 길면 요약 실패로 간주
                return clean_desc[:90] + "..."
        return summary
    except:
        return re.sub('<[^>]*>', '', description)[:90] + "..."

def fetch_filtered_news(keyword, count=15):
    """제목에 키워드 포함 AND 요약문에 1회 이상 등장 조건 적용"""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    params = {"query": keyword, "display": 50, "sort": "date"} # 필터링을 위해 넉넉히 가져옴
    
    filtered_items = []
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            raw_items = res.json().get('items', [])
            for item in raw_items:
                title = item['title'].replace('<b>','').replace('</b>','')
                desc = item['description'].replace('<b>','').replace('</b>','')
                
                # 정밀 필터링 조건 (대소문자 무시)
                if keyword.lower() in title.lower() and keyword.lower() in desc.lower():
                    # 날짜 형식 변환: 04월 16일, 09시 16분
                    try:
                        dt = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
                        item['formatted_date'] = dt.strftime('%m월 %d일, %H시 %M분')
                    except:
                        item['formatted_date'] = item['pubDate']
                        
                    item['ai_summary'] = get_ai_summary(title, desc)
                    filtered_items.append(item)
                    if len(filtered_items) >= count: break
    except: pass
    return filtered_items

# 데이터 수집 (1번칸은 필터 없이 '속보' 전체, 2/3번은 정밀 필터 적용)
final_data = {
    "pane1": fetch_filtered_news("속보", 12),
    "pane2": {kw: fetch_filtered_news(kw, 10) for kw in ["산업부", "KIAT", "기후부", "산업혁신기반구축"]},
    "pane3": {kw: fetch_filtered_news(kw, 10) for kw in ["호르무즈", "트럼프", "유가", "코스피"]},
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)
