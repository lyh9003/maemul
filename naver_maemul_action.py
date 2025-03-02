import time
import requests
import json
import pandas as pd
import datetime
import re
import random

def get_sido_info():
    down_url = 'https://new.land.naver.com/api/regions/list?cortarNo=0000000000'
    r = requests.get(down_url, headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    try:
        temp = json.loads(r.text)
        return pd.DataFrame(temp['regionList'], columns=["cortarNo", "cortarName"])
    except Exception as e:
        print("Error parsing API response:", e)
        return pd.DataFrame(columns=["cortarNo", "cortarName"])
    
def get_gungu_info(sido_code):
    down_url = 'https://new.land.naver.com/api/regions/list?cortarNo=' + str(sido_code)
    r = requests.get(down_url, headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    try:
        temp = json.loads(r.text)
        return pd.DataFrame(temp['regionList'], columns=["cortarNo", "cortarName"])
    except Exception as e:
        print("Error parsing API response:", e)
        return pd.DataFrame(columns=["cortarNo", "cortarName"])

def get_dong_info(gungu_code):
    down_url = f'https://new.land.naver.com/api/regions/list?cortarNo={gungu_code}'
    r = requests.get(down_url, headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    try:
        temp = json.loads(r.text)
        return pd.DataFrame(temp['regionList'], columns=["cortarNo", "cortarName"])
    except Exception as e:
        print("Error parsing API response:", e)
        return pd.DataFrame(columns=["cortarNo", "cortarName"])

def get_apt_list(dong_code):
    down_url = f'https://new.land.naver.com/api/regions/complexes?cortarNo={dong_code}&realEstateType=APT&order='
    r = requests.get(down_url, headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    try:
        temp = json.loads(r.text)
        return pd.DataFrame(temp['complexList'], columns=["complexNo", "complexName"])
    except Exception as e:
        print("Error parsing API response:", e)
        return pd.DataFrame(columns=["complexNo", "complexName"])

# 한글 숫자 변환 함수
def convert_korean_price_to_number(price_str):
    if not price_str:
        return 0
    match = re.match(r"([\d,]+)(억)?(?:\s*([\d,]+)?)?", price_str)
    if not match:
        return 0
    billion_part = match.group(1)
    million_part = match.group(3)
    billion = int(billion_part.replace(',', '')) if billion_part else 0
    million = int(million_part.replace(',', '')) if million_part else 0
    return billion * 100000000 + million * 10000

def get_trade_info(apt_code):
    URL = "https://m.land.naver.com/complex/getComplexArticleList"
    parameter = {
        'hscpNo': apt_code,
        'tradTpCd': 'A1:B1:B2',
        'order': 'spc_',
    }
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.39',
        'Referer': 'https://m.land.naver.com/'
    }
    page = 0
    lands = []
    while True:
        page += 1
        parameter['page'] = page
        response = requests.get(URL, params=parameter, headers=header)
        if response.status_code != 200:
            print('Invalid status:', response.status_code)
            break
        data = json.loads(response.text)
        result = data['result']
        if result is None:
            print('No result')
            break
        for item in result['list']:
            tradTpNm = item.get('tradTpNm', '')
            price_info = item.get('prcInfo', '')
            numeric_price = (
                convert_korean_price_to_number(price_info) if tradTpNm != '월세' else price_info
            )
            lands.append([
                item.get('tradTpNm', ''),
                item.get('bildNm', ''),
                item.get('flrInfo', ''),
                numeric_price,
                item.get('spc1', ''),
                item.get('vrfcTpCd', ''),
                item.get('atclFetrDesc', ''),
                item.get('cfmYmd', ''),
                item.get('tagList', ''),
                item.get('direction', '')
            ])
        if result['moreDataYn'] == 'N':
            break
        time.sleep(random.uniform(2, 2.3))
    return pd.DataFrame(lands, columns=[
        'Trade Type', 'Building Name', 'Floor Info', 'Price (Numeric)', 'Area',
        'Owner', 'Desc', 'RegDate', 'Tag', 'Direction'
    ])

if __name__ == "__main__":
    # 자동으로 시도, 군구, 동 선택 (경기도, 화성시, 비봉면)
    sido_list = get_sido_info()
    selected_sido_df = sido_list[sido_list['cortarName'] == '경기도']
    if selected_sido_df.empty:
        print("경기도를 찾을 수 없습니다.")
        exit()
    selected_sido_row = selected_sido_df.iloc[0]
    selected_sido = selected_sido_row['cortarName']
    sido_code = selected_sido_row['cortarNo']
    print(f"자동 선택 Sido: {selected_sido}")

    gungu_list = get_gungu_info(sido_code)
    selected_gungu_df = gungu_list[gungu_list['cortarName'] == '화성시']
    if selected_gungu_df.empty:
        print("화성시를 찾을 수 없습니다.")
        exit()
    selected_gungu_row = selected_gungu_df.iloc[0]
    selected_gungu = selected_gungu_row['cortarName']
    gungu_code = selected_gungu_row['cortarNo']
    print(f"자동 선택 Gungu: {selected_gungu}")

    dong_list = get_dong_info(gungu_code)
    selected_dong_df = dong_list[dong_list['cortarName'] == '비봉면']
    if selected_dong_df.empty:
        print("비봉면을 찾을 수 없습니다.")
        exit()
    selected_dong_row = selected_dong_df.iloc[0]
    selected_dong = selected_dong_row['cortarName']
    dong_code = selected_dong_row['cortarNo']
    print(f"자동 선택 Dong: {selected_dong}")

    # 선택된 동에 대한 아파트 리스트 및 거래 정보 수집
    apt_list = get_apt_list(dong_code)
    all_trade_info = []
    for apt in apt_list.itertuples():
        print(f"Fetching trade info for: {apt.complexName}")
        trade_info = get_trade_info(apt.complexNo)
        trade_info['Sido'] = selected_sido
        trade_info['Gungu'] = selected_gungu
        trade_info['Dong'] = selected_dong
        trade_info['ComplexName'] = apt.complexName
        cols = ['Sido', 'Gungu', 'Dong', 'ComplexName'] + [col for col in trade_info.columns if col not in ['Sido', 'Gungu', 'Dong', 'ComplexName']]
        trade_info = trade_info[cols]
        all_trade_info.append(trade_info)
        print(trade_info)
        print("\n")
        time.sleep(random.uniform(4, 5))
    
    # 모든 거래 정보를 하나의 DataFrame으로 결합 및 CSV 저장
    if all_trade_info:
        combined_trade_info = pd.concat(all_trade_info, ignore_index=True)
        combined_trade_info['PPA'] = combined_trade_info.apply(
            lambda row: (
                float(row['Price (Numeric)']) / float(row['Area']) * 3.305785
                if pd.notnull(row['Price (Numeric)']) and pd.notnull(row['Area']) and row['Area'] != '0' and '/' not in str(row['Price (Numeric)'])
                else None
            ),
            axis=1
        )
        current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"trade_info_{current_datetime}.csv"
        combined_trade_info.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"Trade info saved to {filename}")
    else:
        print("수집된 거래 정보가 없습니다.")
