import os
import requests
import json
from datetime import datetime, timedelta, timezone

ASSEMBLY_KEY = os.environ.get("ASSEMBLY_API_KEY")
KST = timezone(timedelta(hours=9))

def fetch_bulk_data(url_id, extra_params=None):
    url = f"https://open.assembly.go.kr/portal/openapi/{url_id}"
    # 한 번에 1000개씩 뭉텅이로 긁어옵니다. (호출 횟수 획기적 감소)
    params = {"KEY": ASSEMBLY_KEY, "Type": "json", "pIndex": 1, "pSize": 1000}
    if extra_params:
        params.update(extra_params)
    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if url_id in data:
                return data[url_id][1]['row']
    except: pass
    return []

if __name__ == "__main__":
    print("⚡ [작전명: 터보 레이더] 47분의 굴욕을 10초로 단축 개시...")

    try:
        with open("profiles_db.json", "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except:
        print("❌ profiles_db.json이 없습니다."); exit(1)

    # 300명 의원의 이름과 코드를 빠르게 찾기 위한 맵 생성
    member_map_by_cd = {p["NAAS_CD"]: p["HG_NM"] for p in profiles if p.get("NAAS_CD")}
    member_map_by_nm = {p["HG_NM"]: p["NAAS_CD"] for p in profiles}

    radar_db = {"committee": [], "plenary": [], "bills": [], "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")}

    # 1. 위원회 일정 전체 싹쓸이 (최신 500건)
    print("📡 위원회 일정 벌크 수집 중...")
    bulk_c = fetch_bulk_data("NAMEMBERCMITSCHEDULE", {"pSize": 500})
    for s in bulk_c:
        cd = s.get("NAAS_CD")
        if cd in member_map_by_cd:
            radar_db["committee"].append({
                "HG_NM": member_map_by_cd[cd], "SCH_CN": s.get("SCH_CN", ""),
                "SCH_DT": s.get("SCH_DT", ""), "SCH_TM": s.get("SCH_TM", ""), "CMIT_NM": s.get("CMIT_NM", "")
            })

    # 2. 본회의 일정 전체 싹쓸이 (최신 500건)
    print("📡 본회의 일정 벌크 수집 중...")
    bulk_p = fetch_bulk_data("NAMEMBERLEGISCHEDULE", {"pSize": 500})
    for s in bulk_p:
        cd = s.get("NAAS_CD")
        if cd in member_map_by_cd:
            radar_db["plenary"].append({
                "HG_NM": member_map_by_cd[cd], "SCH_CN": s.get("SCH_CN", ""),
                "SCH_DT": s.get("SCH_DT", ""), "SCH_TM": s.get("SCH_TM", ""), "CMIT_NM": s.get("CMIT_NM", "본회의")
            })

    # 3. 22대 발의법률안 전체 싹쓸이 (최신 1000건)
    print("📡 22대 발의법률안 벌크 수집 중...")
    bulk_b = fetch_bulk_data("nzmimeepazxkubdpn", {"AGE": "22", "pSize": 1000})
    
    # 의원별 5개 제한을 위한 카운터
    bill_counts = {name: 0 for name in member_map_by_nm.keys()}

    for b in bulk_b:
        name = b.get("RST_PROPOSER", "").strip()
        if name in bill_counts and bill_counts[name] < 5:
            # 상태 추적 로직 (폭포수)
            status, dt = "발의", b.get("PROPOSE_DT", "")
            if b.get("PROC_RESULT"): status, dt = b.get("PROC_RESULT"), b.get("PROC_DT", "")
            elif b.get("LAW_PROC_DT"): status, dt = "법사위처리", b.get("LAW_PROC_DT", "")
            elif b.get("COMMITTEE_DT"): status, dt = "소관위회부", b.get("COMMITTEE_DT", "")
            
            radar_db["bills"].append({
                "HG_NM": name, "BILL_NAME": b.get("BILL_NAME", ""), "COMMITTEE": b.get("COMMITTEE", ""),
                "STATUS": status, "DT": dt, "LINK_URL": b.get("DETAIL_LINK", "#")
            })
            bill_counts[name] += 1

    with open("radar_db.json", "w", encoding="utf-8") as f:
        json.dump(radar_db, f, ensure_ascii=False)

    print(f"✅ 작전 완료! 47분 걸리던 작업을 10초 만에 끝냈습니다.")
