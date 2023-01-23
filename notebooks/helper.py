import requests
import pandas as pd

def create_holdings_df(cik_='1535392',fund_name_='Mangrove Partners'):
    #Pull Filing accessionNumbers
    headers_ = {'User-Agent':
           'StockFries stockfries@gmail.com'}
    cik_padded_ = '0001535392'
    url_submissions = f'https://data.sec.gov/submissions/CIK{cik_padded_}.json'
    #print(url_submissions)
    r_ = requests.get(url=url_submissions, headers=headers_)
    
    #Pull Latest 13F-HR Filing
    new_13F_level='None'
    old_13F_level='None'
    for index, filing_form in enumerate(r_.json()['filings']['recent']['form']):
        if (filing_form=='13F-HR') & (new_13F_level=='None'):
            new_13F_level = index
            continue
        elif ((filing_form=='13F-HR') & (new_13F_level!='None') & (old_13F_level=='None')):
            old_13F_level = index
            break
        #elif (new_13F_level!='None') & (new_13F_level!='None'):
        #    break
        else:
            continue
    #print('new_13F_level', 'old_13F_level')
    #print(new_13F_level, old_13F_level)
            
    new_accessionNumber=r_.json()['filings']['recent']['accessionNumber'][new_13F_level].replace('-','')
    new_filingDate = r_.json()['filings']['recent']['filingDate'][new_13F_level]
    new_reportDate = r_.json()['filings']['recent']['reportDate'][new_13F_level]
    new_form = r_.json()['filings']['recent']['form'][new_13F_level]
    old_accessionNumber=r_.json()['filings']['recent']['accessionNumber'][old_13F_level].replace('-','')
    old_filingDate = r_.json()['filings']['recent']['filingDate'][old_13F_level]
    old_reportDate = r_.json()['filings']['recent']['reportDate'][old_13F_level]
    old_form = r_.json()['filings']['recent']['form'][old_13F_level]
    
    url_filling_new = f"https://www.sec.gov/Archives/edgar/data/{cik_}/{new_accessionNumber}/infotable.xml"
    print(url_filling_new)
    r_filing_new = requests.get(url=url_filling_new, headers=headers_)
    df_new = pd.read_xml(r_filing_new.content)
    df_new['cik']=cik_
    df_new['filingDate']= new_filingDate
    df_new['reportDate']= new_reportDate
    
    #Pull Previous Filing
    url_filling_old = f"https://www.sec.gov/Archives/edgar/data/{cik_}/{old_accessionNumber}/infotable.xml"
    #print(url_filling_old)
    r_filing_old = requests.get(url=url_filling_old, headers=headers_)
    df_old = pd.read_xml(r_filing_old.content)
    df_old['cik']=cik_
    df_old['filingDate']= old_filingDate
    df_old['reportDate']= old_reportDate
    df_final = pd.concat([df_new, df_old])
    df_final['fund_name'] = fund_name_
    
    return df_final

def process_scraped_data(df_all_):
    periods = list(set(df_all_.reportDate.values))
    #print(periods[0])
    df_all_.reset_index().tail()
    df_all_[df_all_.reportDate == periods[0]].reset_index().tail()
    df_current = df_all_[df_all_.reportDate == max(periods)].reset_index(drop=True)
    df_previous = df_all_[df_all_.reportDate == min(periods)].reset_index(drop=True)
    df_current_g = df_current.groupby(['nameOfIssuer','cusip']).sum().sort_values('value', ascending=False)
    df_previous_g = df_previous.groupby(['nameOfIssuer','cusip']).sum().sort_values('value', ascending=False)
    df_diff = df_current_g - df_previous_g
    df_heavy_ = df_current_g
    df_hot_ = df_diff[df_diff.value > 0]
    df_cold_ = df_diff[df_diff.value < 0]
    
    return df_heavy_, df_hot_, df_cold_
    