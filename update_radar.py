import os
import requests
import json
from datetime import datetime, timedelta, timezone

ASSEMBLY_KEY = os.environ.get("ASSEMBLY_API_KEY")
KST = timezone(timedelta(hours=9))

def fetch_data(url_id, p_size=1000):
    url = f"https://open.assembly.go.kr/portal/openapi/{url_id}"
    params = {"KEY": ASSEMBLY_KEY, "Type": "json", "pIndex": 1, "pSize": p_size}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            if url_id in data:
                return data[url_id][1]['row']
    except Exception as e:
        print(f"API 호출 에러 ({url_id}): {e}")
    return []

if __name__ == "__main__":
    print("국회 타겟 레이더 DB 구축 시작...")
    
    # 1. 현역 의원 300명 프로필 싹쓸이 (300명이므로 pSize=300)
    profiles = fetch_data("nwvrqwxyaytdsfvhu", 300)
    
    # 2. 최근 전체 활동 내역 싹쓸이 (각 1000건씩)
    bills = fetch_data("ALLBILL", 1000)
    minutes = fetch_data("ncwgseseafwbuheph", 1000)
    votes = fetch_data("nvqbvtdqakfgtuowc", 1000)
    
    # 3. 하나의 JSON DB로 병합
    db = {
        "profiles": profiles,
        "bills": bills,
        "minutes": minutes,
        "votes": votes,
        "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("radar_db.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)
        
    print(f"✅ 레이더 DB 갱신 완료 (프로필 {len(profiles)}명, 법안 {len(bills)}건, 회의 {len(minutes)}건, 투표 {len(votes)}건)")
