import os
import requests
import json

ASSEMBLY_KEY = os.environ.get("ASSEMBLY_API_KEY")

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
    print("1. 22대 의원 기본 정보 수집 중...")
    profiles = fetch_data("nwvrqwxyaytdsfvhu", {"pSize": 300})

    print("2. 역대 의원 6000명 중 22대 사진(NAAS_PIC)만 추출 중...")
    photo_map = {}
    
    # API가 필터를 무시하므로 1~6페이지(6000명)를 전부 뒤집니다.
    for i in range(1, 7):
        photos = fetch_data("ALLNAMEMBER", {"pIndex": i, "pSize": 1000})
        if not photos: break
        
        for m in photos:
            name = m.get("HG_NM", "").strip()
            pic = m.get("NAAS_PIC", "").strip()
            unit = str(m.get("UNIT_NM", "")) + str(m.get("UNIT_CD", ""))
            
            # 22대 의원의 사진 링크(.png/.jpg)를 1도 건드리지 않고 그대로 맵핑
            if name and pic and "22" in unit:
                photo_map[name] = pic

    print("3. 데이터 1:1 직결 병합 중...")
    final_profiles = []
    for p in profiles:
        name = p.get("HG_NM", "").strip()
        
        # 💡 사령관님 지시사항: 여기서 아무 짓도 안 하고 딱 가져옴
        exact_pic_url = photo_map.get(name, "")

        final_profiles.append({
            "HG_NM": name,
            "POLY_NM": p.get("POLY_NM", ""),
            "ORIG_NM": p.get("ORIG_NM", ""),
            "CMITS": p.get("CMITS") or p.get("CMIT_NM", ""),
            "REELE_GBN_NM": p.get("REELE_GBN_NM", ""),
            "UNITS": p.get("UNITS", ""),
            "STAFF": p.get("STAFF", ""),
            "SECRETARY": p.get("SECRETARY", ""),
            "SECRETARY2": p.get("SECRETARY2", ""),
            "MEM_TITLE": p.get("MEM_TITLE", ""),
            "HOMEPAGE": p.get("HOMEPAGE", ""),
            "NAAS_PIC": exact_pic_url  # 어떤 덮어쓰기도 없음. 원본 URL 그대로.
        })

    with open("profiles_db.json", "w", encoding="utf-8") as f:
        json.dump(final_profiles, f, ensure_ascii=False)

    print(f"✅ 프로필 전용 DB (profiles_db.json) 생성 완료! (총 {len(final_profiles)}명)")
