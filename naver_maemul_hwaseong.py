import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import pandas as pd
import datetime
import re
import random

HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://m.land.naver.com/',
}

NAVER_COOKIES = os.environ.get('NAVER_COOKIES', '')
NID_AUT = os.environ.get('NID_AUT', '')
NID_SES = os.environ.get('NID_SES', '')
if NAVER_COOKIES:
    cookie = NAVER_COOKIES
    if NID_AUT and 'NID_AUT' not in NAVER_COOKIES:
        cookie = f'{NAVER_COOKIES}; NID_AUT={NID_AUT}'
    HEADERS['Cookie'] = cookie
    print(f'네이버 전체 쿠키 적용됨 (길이:{len(cookie)})')
elif NID_AUT and NID_SES:
    HEADERS['Cookie'] = f'NID_AUT={NID_AUT}; NID_SES={NID_SES}'
    print(f'네이버 NID 쿠키 적용됨 (NID_AUT 길이:{len(NID_AUT)}, NID_SES 길이:{len(NID_SES)})')
else:
    print('경고: 쿠키 없음 - NAVER_COOKIES 또는 NID_AUT/NID_SES Secret을 설정해주세요.')


def make_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET'],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session


SESSION = make_session()


def safe_get(url, params=None, headers=None, retries=3):
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, headers=headers or HEADERS, timeout=30)
            return r
        except requests.exceptions.ConnectionError as e:
            wait = (attempt + 1) * 5
            print(f'  연결 오류 (시도 {attempt+1}/{retries}), {wait}초 후 재시도: {e}')
            time.sleep(wait)
    raise RuntimeError(f'Failed after {retries} retries: {url}')


def get_region_list(cortar_no):
    url = f'https://m.land.naver.com/map/getRegionList?cortarNo={cortar_no}'
    r = safe_get(url)
    r.encoding = 'utf-8-sig'
    try:
        temp = json.loads(r.text)
        rows = [(item['CortarNo'], item['CortarNm']) for item in temp['result']['list']]
        return pd.DataFrame(rows, columns=['cortarNo', 'cortarName'])
    except Exception as e:
        print(f'Error getting region list for {cortar_no}:', e)
        print(f'  Response: {r.text[:200]}')
        return pd.DataFrame(columns=['cortarNo', 'cortarName'])


def get_apt_list(dong_code):
    url = 'https://m.land.naver.com/complex/ajax/complexListByCortarNo'
    r = safe_get(url, params={'cortarNo': dong_code, 'realEstateType': 'APT'})
    r.encoding = 'utf-8-sig'
    try:
        temp = json.loads(r.text)
        if not temp.get('result'):
            return pd.DataFrame(columns=['complexNo', 'complexName', 'cortarNo'])
        rows = [(str(item['hscpNo']), item['hscpNm'], item['cortarNo']) for item in temp['result']]
        return pd.DataFrame(rows, columns=['complexNo', 'complexName', 'cortarNo'])
    except Exception as e:
        print(f'Error getting apt list for dong {dong_code}:', e)
        return pd.DataFrame(columns=['complexNo', 'complexName', 'cortarNo'])


def convert_korean_price_to_number(price_str):
    if not price_str:
        return 0
    price_str = re.sub(r'<[^>]+>', '', str(price_str))
    match = re.match(r"([\d,]+)(억)?(?:\s*([\d,]+)?)?", price_str)
    if not match:
        return 0
    billion_part = match.group(1)
    million_part = match.group(3)
    billion = int(billion_part.replace(',', '')) if billion_part else 0
    million = int(million_part.replace(',', '')) if million_part else 0
    return billion * 100000000 + million * 10000


def get_trade_info(apt_code, cortar_no=''):
    URL = 'https://m.land.naver.com/complex/getComplexArticleList'
    parameter = {
        'hscpNo': apt_code,
        'cortarNo': cortar_no,
        'tradTpCd': '',
        'ptpNo': '',
        'bildNo': '',
        'order': 'spc_',
        'showR0': 'N',
        'page': 1,
    }
    header = {
        **HEADERS,
        'Referer': f'https://m.land.naver.com/complex/info/{apt_code}',
    }
    page = 0
    lands = []

    while True:
        page += 1
        parameter['page'] = page

        response = safe_get(URL, params=parameter, headers=header)
        if response.status_code != 200:
            print(f'  Invalid status: {response.status_code} for complex {apt_code}')
            break

        raw = response.text.strip()
        if page == 1 and not lands:
            print(f'  DEBUG response[{apt_code}]: {raw[:150]}')
        if raw == 'null' or not raw:
            print(f'  No article data for complex {apt_code} (null - login cookie required)')
            break

        data = json.loads(raw)
        if data is None:
            break

        result = data.get('result')
        if result is None:
            print(f'  No result for complex {apt_code}')
            break

        for item in result.get('list', []):
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
                item.get('direction', ''),
            ])

        if result.get('moreDataYn') == 'N':
            break

        time.sleep(random.uniform(2, 2.3))

    return pd.DataFrame(lands, columns=[
        'Trade Type', 'Building Name', 'Floor Info', 'Price (Numeric)', 'Area',
        'Owner', 'Desc', 'RegDate', 'Tag', 'Direction',
    ])


if __name__ == '__main__':
    sido_list = get_region_list('0000000000')
    try:
        sido_idx = sido_list[sido_list['cortarName'] == '경기도'].index[0]
    except Exception:
        print('경기도를 찾을 수 없습니다. 종료합니다.')
        exit(1)
    selected_sido = '경기도'
    sido_cortar = sido_list.iloc[sido_idx]['cortarNo']
    print('자동 선택된 시도:', selected_sido)

    gungu_list = get_region_list(sido_cortar)

    gungu_input = '44'
    gungu_choice = int(gungu_input) - 1
    selected_gungu = gungu_list.iloc[gungu_choice]['cortarName']
    gungu_cortar = gungu_list.iloc[gungu_choice]['cortarNo']
    print('자동 선택된 군구:', selected_gungu)

    dong_list = get_region_list(gungu_cortar)
    print(f'총 {len(dong_list)}개 동 처리 시작')

    all_trade_info = []
    null_count = 0

    for _, dong in dong_list.iterrows():
        apt_list = get_apt_list(dong['cortarNo'])
        print(f'Processing Dong: {dong["cortarName"]} ({len(apt_list)} 단지)')

        for apt in apt_list.itertuples():
            print(f'  Fetching: {apt.complexName} (No. {apt.complexNo})')
            trade_info = get_trade_info(apt.complexNo, apt.cortarNo)

            if trade_info.empty:
                null_count += 1
                continue

            trade_info['Sido'] = selected_sido
            trade_info['Gungu'] = selected_gungu
            trade_info['Dong'] = dong['cortarName']
            trade_info['ComplexName'] = apt.complexName

            cols = ['Sido', 'Gungu', 'Dong', 'ComplexName'] + [
                col for col in trade_info.columns
                if col not in ['Sido', 'Gungu', 'Dong', 'ComplexName']
            ]
            trade_info = trade_info[cols]
            all_trade_info.append(trade_info)
            print(f'  -> {len(trade_info)} rows')
            time.sleep(random.uniform(4, 5))

    if null_count > 0:
        print(f'\n경고: {null_count}개 단지에서 매물 데이터를 가져오지 못했습니다.')

    if not all_trade_info:
        print('수집된 데이터가 없습니다. 로그인 쿠키를 설정해주세요.')
        exit(1)

    combined_trade_info = pd.concat(all_trade_info, ignore_index=True)

    combined_trade_info['PPA'] = combined_trade_info.apply(
        lambda row: (
            float(row['Price (Numeric)']) / float(row['Area']) * 3.305785
            if pd.notnull(row['Price (Numeric)']) and pd.notnull(row['Area'])
            and row['Area'] != '0' and '/' not in str(row['Price (Numeric)'])
            else None
        ),
        axis=1
    )

    current_datetime = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'trade_info_{selected_sido}_{gungu_input}_{current_datetime}.csv'
    combined_trade_info.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f'Trade info saved to {filename} ({len(combined_trade_info)} rows)')
