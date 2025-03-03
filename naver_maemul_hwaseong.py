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
        return 0  # 빈 문자열은 0으로 처리
    
    match = re.match(r"([\d,]+)(억)?(?:\s*([\d,]+)?)?", price_str)
    if not match:
        return 0  # 매칭되지 않을 경우 0으로 처리
    
    billion_part = match.group(1)  # 억 단위
    million_part = match.group(3)  # 천 단위
    
    billion = int(billion_part.replace(',', '')) if billion_part else 0
    million = int(million_part.replace(',', '')) if million_part else 0
    
    return billion * 100000000 + million * 10000  # 억 단위는 10^8, 천 단위는 10^4

# get_trade_info 함수
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

        time.sleep(random.uniform(2, 2.3))  # 요청 간 딜레이

    return pd.DataFrame(lands, columns=[
        'Trade Type', 'Building Name', 'Floor Info', 'Price (Numeric)', 'Area',
        'Owner', 'Desc', 'RegDate', 'Tag', 'Direction'
    ])

if __name__ == "__main__":
    # 시도 정보를 가져와서 경기도 자동 선택
    sido_list = get_sido_info()
    try:
        sido_idx = sido_list[sido_list['cortarName'] == "경기도"].index[0]
    except Exception as e:
        print("경기도를 찾을 수 없습니다. 종료합니다.")
        exit(1)
    selected_sido = "경기도"
    print("자동 선택된 시도:", selected_sido)

    # 경기도의 모든 군구 정보 가져오기
    gungu_list = get_gungu_info(sido_list.iloc[sido_idx]['cortarNo'])
    # 군구는 전체 선택(즉, 사용자가 군구 선택을 생략)
    gungu_input = '44'
    print("자동 선택된 군구:", gungu_input)

    all_trade_info = []  # 모든 거래 정보를 저장할 리스트

    if gungu_input == '0':
        # 전체 군구 선택 시 각 군구의 동 정보 가져오기 및 부모 군구 이름 추가
        selected_gungu = '전체'
        all_dong_list = pd.DataFrame()
        for _, g in gungu_list.iterrows():
            dong_df = get_dong_info(g['cortarNo'])
            dong_df['parent_gungu'] = g['cortarName']  # 부모 군구 이름 추가
            all_dong_list = pd.concat([all_dong_list, dong_df], ignore_index=True)
        # 동은 전체 선택 (사용자 입력 없이)
        dong_input = '0'
        if dong_input == '0':
            dong_to_process = all_dong_list
        else:
            dong_choice = int(dong_input) - 1
            dong_to_process = all_dong_list.iloc[[dong_choice]]
        
        # 모든 동에 대해 아파트 및 거래 정보 크롤링
        for _, dong in dong_to_process.iterrows():
            apt_list = get_apt_list(dong['cortarNo'])
            print(f"Processing Dong: {dong['cortarName']}")
            for apt in apt_list.itertuples():
                print(f"Fetching trade info for: {apt.complexName}")
                trade_info = get_trade_info(apt.complexNo)

                trade_info['Sido'] = selected_sido
                trade_info['Gungu'] = dong['parent_gungu']
                trade_info['Dong'] = dong['cortarName']  # 실제 동 이름 사용
                trade_info['ComplexName'] = apt.complexName

                cols = ['Sido', 'Gungu', 'Dong', 'ComplexName'] + [col for col in trade_info.columns if col not in ['Sido', 'Gungu', 'Dong', 'ComplexName']]
                trade_info = trade_info[cols]

                all_trade_info.append(trade_info)
                print(trade_info)
                print("\n")
                time.sleep(random.uniform(4, 5))  # 요청 간 딜레이

    # (만약 개별 군구 선택 로직이 필요없다면 else 부분은 제거해도 됩니다.)

    else:
    # 개별 군구 선택한 경우
    gungu_choice = int(gungu_input) - 1
    selected_gungu = gungu_list.iloc[gungu_choice]['cortarName']
    dong_list = get_dong_info(gungu_list.iloc[gungu_choice]['cortarNo'])
    print(f"Select a Dong for Gungu: {selected_gungu}")
    print("0.전체")
    for i, dong in enumerate(dong_list.itertuples(), 1):
        print(f"{i}. {dong.cortarName}")
    dong_input = input("Enter the number of your choice (or 0 for 전체): ").strip()

    if dong_input == '0':
        dong_to_process = dong_list
    else:
        dong_choice = int(dong_input) - 1
        dong_to_process = dong_list.iloc[[dong_choice]]
    
    # 선택한 군구 내의 동에 대해 처리
    for _, dong in dong_to_process.iterrows():
        apt_list = get_apt_list(dong['cortarNo'])
        print(f"Processing Dong: {dong['cortarName']}")
        for apt in apt_list.itertuples():
            print(f"Fetching trade info for: {apt.complexName}")
            trade_info = get_trade_info(apt.complexNo)

            trade_info['Sido'] = selected_sido
            trade_info['Gungu'] = selected_gungu
            trade_info['Dong'] = dong['cortarName']  # 실제 dong 이름 사용
            trade_info['ComplexName'] = apt.complexName

            cols = ['Sido', 'Gungu', 'Dong', 'ComplexName'] + [col for col in trade_info.columns if col not in ['Sido', 'Gungu', 'Dong', 'ComplexName']]
            trade_info = trade_info[cols]

            all_trade_info.append(trade_info)
            print(trade_info)
            print("\n")
            time.sleep(random.uniform(4, 5))  # 요청 간 딜레이


    
    # 모든 거래 정보를 하나의 DataFrame으로 결합
    combined_trade_info = pd.concat(all_trade_info, ignore_index=True)

    # 평당가(PPA) 계산
    combined_trade_info['PPA'] = combined_trade_info.apply(
        lambda row: (
            float(row['Price (Numeric)']) / float(row['Area']) * 3.305785
            if pd.notnull(row['Price (Numeric)']) and pd.notnull(row['Area']) and row['Area'] != '0' and '/' not in str(row['Price (Numeric)'])
            else None
        ),
        axis=1
    )

    # CSV 파일로 저장
    current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"trade_info_{selected_sido}_{gungu_input}_{current_datetime}.csv"
    combined_trade_info.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"Trade info saved to {filename}")

    
