import requests
import json
import os
from datetime import datetime

# =========================================================
# 1. 설정 정보
# =========================================================
G2B_API_KEY = os.environ.get("G2B_API_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# 필터링 키워드
KEYWORDS_POSITIVE = ['영상', '홍보', '콘텐츠', '기획','미디어', '유튜브', '숏폼', '제작', '비디오', '모션', '촬영']
KEYWORDS_NEGATIVE = [
    '인터넷제작', '홈페이지', '웹사이트', '신문', '정기발행', '인쇄', '출판', 
    '유지보수', '공사', '건설', '폐기물', '청소', '급식', '구매'
]
TARGET_REGIONS = ['경기', '구리', '남양주', '서울']

# 파일 경로
DATA_FILE = "bids.json"
HTML_FILE = "index.html"

# =========================================================
# 2. 데이터 관리 함수
# =========================================================

def load_bids():
    """기존 bids.json 파일을 읽어옵니다."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_bids(bids):
    """bids 리스트를 파일에 저장합니다."""
    # 최신순 정렬 (입찰공고번호 역순 or 등록일시 역순)
    # 여기서는 간단히 리스트 앞쪽이 최신이라고 가정하고 저장
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(bids, f, ensure_ascii=False, indent=2)

def send_slack_message(item):
    """새로운 공고 알림을 슬랙으로 전송합니다."""
    try:
        # 날짜 포맷
        end_date = item.get('bidPsNtceEndDt', '')
        if len(end_date) == 12:
            formatted_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]} {end_date[8:10]}:{end_date[10:]}"
        else:
            formatted_date = end_date

        msg = {
            "text": f"📢 *[새로운 공고]* {item['bidNtceNm']}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📢 *<{item.get('link')}|{item['bidNtceNm']}>*\n"
                                f"🏢 {item['dminsttNm']} | 📍 {item.get('prtcptPsblRgnNm', '전국')}\n"
                                f"⏰ 마감: {formatted_date}"
                    }
                }
            ]
        }
        requests.post(SLACK_WEBHOOK_URL, json=msg)
    except Exception as e:
        print(f"Slack 전송 실패: {e}")

# =========================================================
# 3. HTML 생성 함수
# =========================================================

def generate_html(bids):
    """bids 데이터를 기반으로 예쁜 반응형 index.html을 생성합니다."""
    
    # HTML 템플릿 (f-string 사용)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 카드 아이템 생성
    cards_html = ""
    for bid in bids:
        # 날짜 포맷팅
        end_date = bid.get('bidPsNtceEndDt', '마감일 없음')
        if len(end_date) == 12:
            end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]} {end_date[8:10]}:{end_date[10:]}"
        
        region = bid.get('prtcptPsblRgnNm', '')
        if not region: region = "전국"

        cards_html += f"""
        <div class="card">
            <div class="badge">{region}</div>
            <div class="agency">{bid.get('dminsttNm')}</div>
            <h2 class="title">{bid.get('bidNtceNm')}</h2>
            <div class="meta">
                <span>⏰ 마감: {end_date}</span>
                <span>💰 {bid.get('bdgtAmt', '0')}원</span>
            </div>
            <a href="{bid.get('link')}" target="_blank" class="btn">공고 보러가기</a>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>나라장터 입찰 공고 대시보드</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px 0;
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
            color: var(--text);
        }}
        .update-time {{
            color: var(--text-light);
            font-size: 0.9rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            flex-direction: column;
            position: relative;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}
        .badge {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: #e2e8f0;
            color: #475569;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .agency {{
            color: var(--primary);
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 8px;
        }}
        .title {{
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0 0 16px 0;
            line-height: 1.4;
            flex-grow: 1; /* 제목이 길어도 버튼을 아래로 밀어줌 */
        }}
        .meta {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 20px;
        }}
        .btn {{
            display: block;
            width: 100%;
            padding: 12px;
            background: var(--primary);
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: background 0.2s;
            box-sizing: border-box; /* padding 포함 너비 계산 */
        }}
        .btn:hover {{
            background: #1d4ed8;
        }}
        @media (max-width: 600px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            h1 {{
                font-size: 1.75rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏛️ 유니트미디어 입찰 공고 대시보드</h1>
            <div class="update-time">최근 업데이트: {now_str}</div>
        </header>
        
        <div class="grid">
            {cards_html}
        </div>
    </div>
</body>
</html>
    """
    
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Index.html 생성 완료 ({len(bids)}개 공고)")

# =========================================================
# 4. 메인 로직
# =========================================================

def main():
    print(f"[{datetime.now()}] 작업 시작")
    
    # 1. 기존 데이터 로드
    existing_bids = load_bids()
    existing_ids = {item['bidNtceNo'] for item in existing_bids}
    
    # 2. 오늘 날짜 API 조회
    today = datetime.now().strftime("%Y%m%d")
    url = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch"
    params = {
        "serviceKey": G2B_API_KEY,
        "numOfRows": "200", # 한번에 많이 조회
        "pageNo": "1",
        "inqryDiv": "1",
        "inqryBgnDt": today + "0000",
        "inqryEndDt": today + "2359",
        "type": "json"
    }
    
    new_items_count = 0
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            print("API 조회 결과 없음")
            items = []
            
        # 3. 필터링 및 추가
        new_bids = []
        for item in items:
            bid_no = item.get('bidNtceNo')
            bid_name = item.get('bidNtceNm', '')
            region = item.get('prtcptPsblRgnNm', '')
            
            # 이미 저장된 공고면 패스
            if bid_no in existing_ids:
                continue
                
            # 필터링 로직
            if any(neg in bid_name for neg in KEYWORDS_NEGATIVE):
                continue
            if not any(pos in bid_name for pos in KEYWORDS_POSITIVE):
                continue
            if region:
                if not any(reg in region for reg in TARGET_REGIONS):
                    continue
            
            # 새 공고 발견!
            item['link'] = f"https://www.g2b.go.kr:8101/ep/invitation/publish/bidInfoDtl.do?bidno={bid_no}"
            new_bids.append(item)
            existing_ids.add(bid_no)
            
            # Slack 알림 즉시 전송
            send_slack_message(item)
            new_items_count += 1
            
        # 4. 데이터 병합 (새 공고가 위로 오게)
        # 기존 데이터 + 새 데이터 -> 다시 정렬이 필요할 수 있으나, 
        # 여기선 간단히 [새데이터] + [기존데이터] 로 합침
        all_bids = new_bids + existing_bids
        
        # 5. 저장 및 페이지 생성
        save_bids(all_bids)
        generate_html(all_bids)
        
        print(f"새로 추가된 공고: {new_items_count}건")
        print("작업 완료")
        
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    main()
