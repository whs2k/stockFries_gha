import requests
import pandas as pd
import xmltodict
from datetime import datetime
from config import fund_dict
import traceback
import time

def get_historical_holdings(cik_, fund_name_):
    headers_ = {'User-Agent': 'StockFries stockfries@gmail.com'}
    cik_padded_ = cik_.rjust(10, "0")
    url_submissions = f'https://data.sec.gov/submissions/CIK{cik_padded_}.json'
    print(url_submissions)
    
    for attempt in range(3):
        try:
            r_ = requests.get(url=url_submissions, headers=headers_, timeout=10)
            if r_.status_code == 200:
                break
            time.sleep(1)
        except Exception as e:
            if attempt == 2:
                print(f"Failed to fetch {url_submissions}")
                return pd.DataFrame()
            time.sleep(1)
            
    if r_.status_code != 200:
        return pd.DataFrame()
        
    data = r_.json()
    recent_filings = data['filings']['recent']
    
    df_list = []
    
    for i, form in enumerate(recent_filings['form']):
        if form == '13F-HR':
            reportDate = recent_filings['reportDate'][i]
            if reportDate < '2018-01-01':
                continue
                
            accessionNumber_dash = recent_filings['accessionNumber'][i]
            filingDate = recent_filings['filingDate'][i]
            
            BASE_URL_FORM_TABLE = f'https://www.sec.gov/Archives/edgar/data/{cik_}/{accessionNumber_dash}.txt'
            print(f"  Fetching: {BASE_URL_FORM_TABLE}")
            
            for attempt in range(3):
                try:
                    r_filing = requests.get(url=BASE_URL_FORM_TABLE, headers=headers_, timeout=10)
                    if r_filing.status_code == 200:
                        break
                    time.sleep(0.5)
                except Exception as e:
                    if attempt == 2:
                        break
                    time.sleep(0.5)
                    
            if r_filing.status_code != 200 or '<XML>\n' not in r_filing.text:
                continue
                
            try:
                parts = r_filing.text.split('<XML>\n')
                if len(parts) < 3:
                    continue
                response_text = parts[2].split('\n</XML>')[0]
                xml_doc_ = xmltodict.parse(response_text)
                
                infoTable = xml_doc_.get('informationTable', {}).get('infoTable', [])
                if not infoTable:
                    continue
                    
                if not isinstance(infoTable, list):
                    infoTable = [infoTable]
                
                df_filing = pd.DataFrame(infoTable)
                df_filing.columns = [col.split(':')[-1] for col in df_filing.columns]
                
                sshPrnamtType_lists = []
                sshPrnamt_lists = []
                for element in infoTable:
                    shrs = element.get('shrsOrPrnAmt', {})
                    if 'ns1:sshPrnamt' in shrs:
                        sshPrnamt_lists.append(int(shrs.get('ns1:sshPrnamt', 0)))
                        sshPrnamtType_lists.append(shrs.get('ns1:sshPrnamtType', ''))
                    elif 'sshPrnamt' in shrs:
                        sshPrnamt_lists.append(int(shrs.get('sshPrnamt', 0)))
                        sshPrnamtType_lists.append(shrs.get('sshPrnamtType', ''))
                    else:
                        sshPrnamt_lists.append(0)
                        sshPrnamtType_lists.append('')
                        
                df_filing['sshPrnamt'] = sshPrnamt_lists
                df_filing['sshPrnamtType'] = sshPrnamtType_lists
                df_filing['cik'] = cik_
                df_filing['filingDate'] = filingDate
                df_filing['reportDate'] = reportDate
                df_filing['filingLink'] = BASE_URL_FORM_TABLE
                df_filing['fund_name'] = fund_name_
                df_filing['fundAllFillingsSECLink'] = 'https://www.sec.gov/edgar/browse/?CIK=' + cik_
                
                if 'value' in df_filing.columns:
                    df_filing['value'] = pd.to_numeric(df_filing['value'], errors='coerce').fillna(0).astype('int')
                
                df_list.append(df_filing)
                time.sleep(0.12)
            except Exception as e:
                print(f"    Error parsing {BASE_URL_FORM_TABLE}: {e}")
                continue
                
    if len(df_list) > 0:
        return pd.concat(df_list, ignore_index=True)
    return pd.DataFrame()

def run_backfill():
    df_all = pd.DataFrame()
    total_funds = len(fund_dict)
    print(f"Starting backfill for {total_funds} funds...")
    
    for i, fund in enumerate(fund_dict):
        try:
            fund_name = fund
            cik = fund_dict[fund].split('CIK=')[1].split('&')[0]
            print(f"[{i+1}/{total_funds}] Processing {fund_name} (CIK: {cik})")
            df_fund = get_historical_holdings(cik, fund_name)
            if not df_fund.empty:
                df_all = pd.concat([df_all, df_fund]).reset_index(drop=True)
                print(f' -> Added {len(df_fund)} rows for {fund_name}')
            else:
                print(f' -> No data retrieved for {fund_name}')
        except Exception as e:
            print('Issue with: ', fund)
            print(traceback.format_exc())
            continue

    if not df_all.empty:
        # We append to the existing or overwrite? The user says: 
        # "create a backfill of 'data_by_stocks.csv' going back to 2018? I'll then upload it to the repo"
        # Since it goes back to 2018, it will include recent filings too. 
        # But wait, does SEC EDGAR contain the current filings? Yes, recent filings up to 1000.
        # So we can just overwrite `data_by_stocks.csv` with our comprehensive historical list.
        df_all.to_csv('data_by_stocks.csv', index=False)
        print(f"Backfill completed! Total rows: {len(df_all)}. Saved to data_by_stocks.csv")
    else:
        print("Backfill failed: No data fetched.")

if __name__ == "__main__":
    run_backfill()
