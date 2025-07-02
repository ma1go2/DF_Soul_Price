#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
from urllib.parse import quote
import time
from datetime import datetime
import pandas as pd
import os

# 🔑 API 키 불러오기
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    API_KEY = config["API_KEY"]

# 📁저장 폴더 위치
path = r"C:\Users\mangg\Documents\jupyternotebook\D&F\csv저장/".replace('\\','\\\\')
    
# 🔍 모니터링할 아이템 리스트
ITEM_LIST = [
    '레어 소울 결정',
    '유니크 소울 결정',
    '레전더리 소울 결정',
    '에픽 소울 결정',
    '태초 소울 결정'
]

# ⚙️ 검색 조건
limit = 150
wordType = 'match'
wordShort = 'true'

# 📦 경매장 데이터 수집 함수
def fetch_auction_data(item_name):
    itemName = quote(item_name)
    url = (
        f"https://api.neople.co.kr/df/auction?"
        f"itemName={itemName}&limit={limit}&wordType={wordType}"
        f"&wordShort={wordShort}&sort=unitPrice:asc&apikey={API_KEY}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ API 오류 ({item_name}): {response.status_code}")
        return pd.DataFrame()

    rows = response.json().get("rows", [])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    df = pd.DataFrame([{
        '조회시간': now,
        '등록넘버': row['auctionNo'],
        '아이템명': row['itemName'],
        '가격': row['unitPrice'],
        '수량': row['count'],
        '시세': row['averagePrice'],
        '등록일자': pd.to_datetime(row['regDate']).strftime("%Y-%m-%d %H:%M")
    } for row in rows])

    return df

# 📄 저장 함수 (일자별 파일 생성, 중복 제거)
def save_to_csv(new_df, item_name, path):
    # 저장 파일명 예: auction_레어 소울 결정_2025-06-30.csv
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_item_name = item_name.replace(" ", "_")
    filename = path+f"{safe_item_name}_{date_str}.csv"

    if os.path.exists(filename):
        # 기존 데이터 로드
        old_df = pd.read_csv(filename, encoding="utf-8-sig")
        
        # 중복 비교를 위해 문자열로 변환 (정수 overflow 방지)
        old_ids = set(old_df["등록넘버"].astype(str))
        new_unique_df = new_df[~new_df["등록넘버"].astype(str).isin(old_ids)]
        
        if not new_unique_df.empty:
            combined_df = pd.concat([old_df, new_unique_df], ignore_index=True)
            combined_df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"✅ {item_name}: {len(new_unique_df)}건 새로 추가됨 → 총 {len(combined_df)}건")
        else:
            print(f"🟡 {item_name}: 추가된 항목 없음 (중복)")
        
    else:
        # 첫 저장
        new_df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"✅ {item_name}: {len(new_df)}건 저장 (신규 파일 생성)")

# 🔁 주기적 실행
while True:
    print(datetime.now().strftime("%Y-%m-%d %H:%M"))
    try:
        for item in ITEM_LIST:
            df = fetch_auction_data(item)
            if not df.empty:
                save_to_csv(df, item, path)
    except Exception as e:
        print("⚠️ 예외 발생:", e)

    time.sleep(60)  # 1분 대기

