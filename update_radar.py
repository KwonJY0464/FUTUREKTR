import os
import requests
import json
from datetime import datetime, timedelta, timezone

ASSEMBLY_KEY = os.environ.get("ASSEMBLY_API_KEY")
KST = timezone(timedelta(hours=9))

def fetch_data(url_id, extra_params=None):
    url = f"https://open.assembly.go.kr/portal/openapi/{url_id}"
    params = {"KEY": ASSEMBLY_KEY, "Type": "json", "pIndex": 1, "pSize": 1000}
    if extra_params:
        params.update(extra_params)
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
    print("국회 타겟 레이더 DB 구축 시작 ...")
    
    # 1. 제22대 현역 의원 프로필 원본 (nwvrqwxyaytdsfvhu)
    raw_profiles = fetch_data("nwvrqwxyaytdsfvhu", {"pSize": 300})
    
    # 2. 역대 의원 사진 통합 DB 수집 (ALLNAMEMBER)
    photo_dict = {}
    for p_idx in range(1, 10):
        history_members = fetch_data("ALLNAMEMBER", {"pIndex": p_idx, "pSize": 1000})
        if not history_members: break
        for m in history_members:
            name = m.get("HG_NM", "")
            bth_date = m.get("BTH_DATE", "")
            pic_url = m.get("NAAS_PIC", "")
            if name and bth_date:
                photo_dict[f"{name}_{bth_date}"] = pic_url
    
    # 💡 3. [최적화] 필요한 9가지 핵심 정보만 추출하여 다이어트된 프로필 생성
    lightweight_profiles = []
    for p in raw_profiles:
        key = f"{p.get('HG_NM')}_{p.get('BTH_DATE')}"
        pic_url = photo_dict.get(key, "")
        
        lightweight_profiles.append({
            "HG_NM": p.get("HG_NM", ""),
            "POLY_NM": p.get("POLY_NM", ""),
            "ORIG_NM": p.get("ORIG_NM", ""),
            "CMITS": p.get("CMITS", "") or p.get("CMIT_NM", ""),
            "REELE_GBN_NM": p.get("REELE_GBN_NM", ""),
            "UNITS": p.get("UNITS", ""),
            "STAFF": p.get("STAFF", ""),
            "SECRETARY": p.get("SECRETARY", ""),
            "SECRETARY2": p.get("SECRETARY2", ""),
            "MEM_TITLE": p.get("MEM_TITLE", ""),
            "HOMEPAGE": p.get("HOMEPAGE", ""), # 홈페이지 링크 추가
            "NAAS_PIC": pic_url,              # 사진 URL 텍스트만 저장
            "MONA_CD": p.get("MONA_CD", "")
        })
        
    print(f"✅ 프로필 다이어트 및 사진 매칭 완료.")
    
    # 4. 최근 활동 내역 싹쓸이 (법안, 회의록 - 22대 위주 최신순 1000건)
    bills = fetch_data("ALLBILL", {"pSize": 1000})
    minutes = fetch_data("ncwgseseafwbuheph", {"pSize": 1000})
    
    # 💡 5. 본회의 표결 싹쓸이 (무조건 22대 강제)
    print("본회의 표결 데이터 수집 중 (최근 30건)...")
    recent_plenary_bills = fetch_data("ncocpgfiaoituanbr", {"AGE": "22", "pSize": 30})
    
    votes_data = []
    if recent_plenary_bills:
        for bill in recent_plenary_bills:
            bill_id = bill.get("BILL_ID")
            if not bill_id: continue
            
            # 💡 nzmimeepazxkubdpn API에도 AGE=22 필수 적용
            bill_votes = fetch_data("nzmimeepazxkubdpn", {"BILL_ID": bill_id, "AGE": "22", "pSize": 300})
            for v in bill_votes:
                votes_data.append({
                    "HG_NM": v.get("HG_NM", ""),
                    "BILL_NM": v.get("BILL_NAME", bill.get("BILL_NAME", "의안명 없음")),
                    "RESULT_VOTE_NM": v.get("RESULT_VOTE_MOD", "확인불가"),
                    "VOTE_DATE": v.get("VOTE_DATE", "날짜없음")
                })
    
    # 6. 초경량 DB 병합
    db = {
        "profiles": lightweight_profiles,
        "bills": bills,
        "minutes": minutes,
        "votes": votes_data,
        "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("radar_db.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)
        
    print(f"✅ 레이더 DB 갱신 완료 (표결 데이터 {len(votes_data)}건 수집됨)")
