import os
import requests
import json
import concurrent.futures
import threading
from datetime import datetime, timedelta, timezone

ASSEMBLY_KEY = os.environ.get("ASSEMBLY_API_KEY")
KST = timezone(timedelta(hours=9))
db_lock = threading.Lock()

def fetch_data(url_id, extra_params=None):
    url = f"https://open.assembly.go.kr/portal/openapi/{url_id}"
    params = {"KEY": ASSEMBLY_KEY, "Type": "json", "pIndex": 1, "pSize": 10}
    if extra_params: params.update(extra_params)
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if url_id in data: return data[url_id][1]['row']
    except: pass
    return []

# [멀티스레드 전용] 의원별 일정 수집 일꾼
def collect_schedules(p, radar_db):
    name = p.get("HG_NM", "").strip()
    naas_cd = p.get("NAAS_CD", "").strip()
    if not naas_cd: return

    # 위원회 일정 & 본회의 일정 수집
    c_schedules = fetch_data("NAMEMBERCMITSCHEDULE", {"NAAS_CD": naas_cd})
    p_schedules = fetch_data("NAMEMBERLEGISCHEDULE", {"NAAS_CD": naas_cd})

    with db_lock:
        for s in c_schedules:
            radar_db["committee"].append({
                "HG_NM": name, "SCH_CN": s.get("SCH_CN", ""), "SCH_DT": s.get("SCH_DT", ""),
                "SCH_TM": s.get("SCH_TM", ""), "CMIT_NM": s.get("CMIT_NM", "")
            })
        for s in p_schedules:
            radar_db["plenary"].append({
                "HG_NM": name, "SCH_CN": s.get("SCH_CN", ""), "SCH_DT": s.get("SCH_DT", ""),
                "SCH_TM": s.get("SCH_TM", ""), "CMIT_NM": s.get("CMIT_NM", "본회의")
            })

if __name__ == "__main__":
    print("⚡ 일정 복구 개시...")

    try:
        with open("profiles_db.json", "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except: print("❌ profiles_db.json 없음"); exit(1)

    radar_db = {"committee": [], "plenary": [], "bills": [], "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")}

    # 1. 일정 수집 (멀티스레딩 20명 동시 투입 - 약 30초~1분 소요)
    print(f"📡 300명의 위원회/본회의 일정을 정밀 추적 중...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(collect_schedules, p, radar_db) for p in profiles]
        concurrent.futures.wait(futures)

    # 2. 법안 수집 (벌크로 한 방에 - 1초 소요)
    print("📡 22대 발의법률안 1,000건 벌크 수집 중...")
    bulk_b = fetch_data("nzmimeepazxkubdpn", {"AGE": "22", "pSize": 1000})
    
    # 의원별 5개 제한용 카운터
    bill_counts = {}
    for b in bulk_b:
        name = b.get("RST_PROPOSER", "").strip()
        if not name: continue
        
        bill_counts[name] = bill_counts.get(name, 0)
        if bill_counts[name] < 5:
            # 상태 추적 로직
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

    print(f"✅ 작전 완료! 이제 일정과 법안이 모두 완벽하게 출력됩니다.")
