import os
import requests
import json
from datetime import datetime

# 1. API 설정
ASSEMBLY_API_KEY = os.environ.get("ASSEMBLY_API_KEY")
SERVICE_ID = "ALLSCHEDULE"
# 이번 달 전체 및 미래 일정을 위해 사이즈를 충분히 확보 (1000건)
URL = f"https://open.assembly.go.kr/portal/openapi/{SERVICE_ID}?KEY={ASSEMBLY_API_KEY}&Type=json&pIndex=1&pSize=1000"

def fetch_filtered_assembly_data():
    try:
        response = requests.get(URL)
        data = response.json()
        
        if SERVICE_ID not in data:
            print(f"⚠️ API 응답 확인 불가: {data}")
            return []
            
        rows = data[SERVICE_ID][1].get('row', [])
        
        # 💡 날짜 설정: 이번 달 1일부터 추출
        now = datetime.now()
        start_of_month = now.replace(day=1).strftime("%Y-%m-%d")
        
        # 💡 지시하신 키워드 리스트
        target_keywords = [
            "반도체", "이차전지", "산업", "산업부", "산업통상부", 
            "기후부", "풍력", "태양력", "재생에너지", "환경", 
            "에너지", "전체회의", "탄소중립"
        ]
        
        processed_data = []
        
        for row in rows:
            dt = row.get('SCH_DT', '')
            cmit = row.get('CMIT_NM') or ""
            title = row.get('SCH_CN') or ""
            
            # 1. 날짜 필터 (이번 달 1일 이후 모든 데이터)
            if dt < start_of_month:
                continue
                
            # 2. 위원회 및 키워드 매칭 로직
            is_sanja = False
            is_gihyu = False
            
            # 산자중기위 관련 (명칭 및 키워드)
            if "산업통상자원중소벤처기업위원회" in cmit or any(kw in title for kw in ["산업", "산업부", "산업통상부", "반도체", "이차전지"]):
                is_sanja = True
                
            # 기후환노위 관련 (명칭 및 키워드)
            if "기후에너지환경노동위원회" in cmit or any(kw in title for kw in ["기후부", "풍력", "태양력", "재생에너지", "환경", "에너지", "탄소중립"]):
                is_gihyu = True
            
            # 공통 키워드 (전체회의 등) 포함 여부 확인
            is_keyword_match = any(kw in title for kw in target_keywords)
            
            # 결과 분류 및 데이터 추출
            if is_sanja or is_gihyu or is_keyword_match:
                # 색상 구분을 위한 타입 지정 (산자 우선순위)
                cat = "session"
                if is_sanja: cat = "sanja"
                elif is_gihyu: cat = "gihyu"
                
                processed_data.append({
                    "date": dt,
                    "time": row.get('SCH_TM', ''),
                    "title": title,
                    "committee": cmit,
                    "location": row.get('EV_PLC', ''),
                    "type": cat
                })
        
        return processed_data
    except Exception as e:
        print(f"❌ 수집 중 오류: {e}")
        return []

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%m월')} 국회 일정 정밀 수집 개시...")
    
    schedules = fetch_filtered_assembly_data()
    
    # 💡 젬마 요약 연결 중단 (테스트용 고정 메시지)
    test_summary = "현재 정밀 키워드 수집 시험 중입니다. AI 분석 결과는 데이터 검증 후 복구 예정입니다."
    
    # JSON 파일 저장
    with open("assembly.json", "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "schedules": schedules,
            "summary": test_summary
        }, f, ensure_ascii=False, indent=2)
        
    print(f"💾 수집 완료: {len(schedules)}건의 데이터가 assembly.json에 기록되었습니다.")
