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
        print(f"API 호출 에러: {e}")
    return []

if __name__ == "__main__":
    current_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] 🚀 [ALLNAMEMBER] 출력명세서 기준 타격 개시...")
    
    final_profiles = []
    
    # 1~7페이지(역대 의원 6000명 전체)를 싹 뒤집니다.
    for i in range(1, 8):
        members = fetch_data("ALLNAMEMBER", {"pIndex": i, "pSize": 1000})
        if not members: break
        
        for m in members:
            # 💡 사령관님 지시사항 적용: GTELT_ERACO(당선대수)에 "22대"가 포함되어 있는지 확인
            eraco = str(m.get("GTELT_ERACO", ""))
            
            if "22대" in eraco:
                # 출력명세서의 NAAS_NM (국회의원명) 사용
                name = m.get("NAAS_NM", "").strip() 
                
                # 원본 사진 URL (조작 없이 그대로 가져옴)
                pic_url = m.get("NAAS_PIC", "")
                if not isinstance(pic_url, str): pic_url = ""
                pic_url = pic_url.strip()
                
                # 중복 방지 (이미 들어간 의원이면 패스)
                if not any(p["HG_NM"] == name for p in final_profiles):
                    # 자바스크립트가 읽을 수 있도록 기존 변수명으로 매핑하여 저장합니다.
                    final_profiles.append({
                        "HG_NM": name,                                  # 이름
                        "POLY_NM": m.get("PLPT_NM", ""),                # 정당명
                        "ORIG_NM": m.get("ELECD_NM", ""),               # 선거구명
                        "CMITS": m.get("BLNG_CMIT_NM", "") or m.get("CMIT_NM", ""), # 소속위원회명
                        "REELE_GBN_NM": m.get("RLCT_DIV_NM", ""),       # 재선구분명
                        "UNITS": eraco,                                 # 당선대수 (제22대)
                        "STAFF": m.get("AIDE_NM", ""),                  # 보좌관
                        "SECRETARY": m.get("CHF_SCRT_NM", ""),          # 선임비서관
                        "SECRETARY2": m.get("SCRT_NM", ""),             # 비서관
                        "MEM_TITLE": m.get("BRF_HST", ""),              # 약력
                        "HOMEPAGE": m.get("NAAS_HP_URL", ""),           # 홈페이지URL
                        "NAAS_PIC": pic_url                             # 💡 무적의 사진 원본 링크
                    })
                    
    with open("profiles_db.json", "w", encoding="utf-8") as f:
        json.dump(final_profiles, f, ensure_ascii=False)

    print(f"✅ 프로필 DB 구축 완료! (총 {len(final_profiles)}명, 출력명세서 매칭 완료)")
