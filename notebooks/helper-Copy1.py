import requests
import pandas as pd
import xmltodict

def create_holdings_df(cik_='1535392',fund_name_='Mangrove Partners'):
    #Pull Filing accessionNumbers
    headers_ = {'User-Agent':
           'StockFries stockfries@gmail.com'}
    cik_padded_ = cik_.rjust(10, "0")#'0001535392'
    url_submissions = f'https://data.sec.gov/submissions/CIK{cik_padded_}.json'
    print(url_submissions)
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
    new_accessionNumber_dash=r_.json()['filings']['recent']['accessionNumber'][new_13F_level]
    new_filingDate = r_.json()['filings']['recent']['filingDate'][new_13F_level]
    new_reportDate = r_.json()['filings']['recent']['reportDate'][new_13F_level]
    new_form = r_.json()['filings']['recent']['form'][new_13F_level]
    old_accessionNumber=r_.json()['filings']['recent']['accessionNumber'][old_13F_level].replace('-','')
    old_accessionNumber_dash=r_.json()['filings']['recent']['accessionNumber'][old_13F_level]
    old_filingDate = r_.json()['filings']['recent']['filingDate'][old_13F_level]
    old_reportDate = r_.json()['filings']['recent']['reportDate'][old_13F_level]
    old_form = r_.json()['filings']['recent']['form'][old_13F_level]
    
    BASE_URL_FORM_TABLE = f'https://www.sec.gov/Archives/edgar/data/{cik_}/{new_accessionNumber_dash}.txt'
    print(BASE_URL_FORM_TABLE)
    r_filing_new = requests.get(url=BASE_URL_FORM_TABLE, headers=headers_)
    response_text_new = r_filing_new.text.split('<XML>\n')[2].split('\n</XML>')[0]#.replace('\n','')
    xml_doc_ = xmltodict.parse(response_text_new)
    df_new = pd.DataFrame(xml_doc_['informationTable']['infoTable'])
    
    sshPrnamtType_lists = []
    sshPrnamt_lists = []
    for element in xml_doc_['informationTable']['infoTable']:
        #print(element['shrsOrPrnAmt']['sshPrnamt'])
        sshPrnamt_lists.append(int(element['shrsOrPrnAmt']['sshPrnamt']))
        sshPrnamtType_lists.append(element['shrsOrPrnAmt']['sshPrnamtType'])
    df_new['sshPrnamt']= sshPrnamt_lists
    df_new['sshPrnamtType'] = sshPrnamtType_lists
    df_new['cik']=cik_
    df_new['filingDate']= new_filingDate
    df_new['reportDate']= new_reportDate
    
    #Pull Previous Filing
    BASE_URL_FORM_TABLE = f'https://www.sec.gov/Archives/edgar/data/{cik_}/{old_accessionNumber_dash}.txt'
    print(BASE_URL_FORM_TABLE)
    r_filing_old = requests.get(url=BASE_URL_FORM_TABLE, headers=headers_)
    response_text_old = r_filing_old.text.split('<XML>\n')[2].split('\n</XML>')[0]#.replace('\n','')
    xml_doc_ = xmltodict.parse(response_text_old)
    df_old = pd.DataFrame(xml_doc_['informationTable']['infoTable'])
    
    sshPrnamtType_lists = []
    sshPrnamt_lists = []
    for element in xml_doc_['informationTable']['infoTable']:
        #print(element['shrsOrPrnAmt']['sshPrnamt'])
        sshPrnamt_lists.append(int(element['shrsOrPrnAmt']['sshPrnamt']))
        sshPrnamtType_lists.append(element['shrsOrPrnAmt']['sshPrnamtType'])
    df_old['sshPrnamt']= sshPrnamt_lists
    df_old['sshPrnamtType'] = sshPrnamtType_lists

    df_old['cik']=cik_
    df_old['filingDate']= old_filingDate
    df_old['reportDate']= old_reportDate
    df_final = pd.concat([df_new, df_old])
    df_final['fund_name'] = fund_name_
    df_final['value'] = df_final['value'].astype('int')
    return df_final

def process_scraped_data(df_all_):
    df_all_['nameOfIssuer_link'] =df_all_['nameOfIssuer'].apply(
    lambda x: str('''<a href="http://www.google.com/search?q=stock price {}" 
        target="_blank">{}</a>'''.format(x, x)))
    periods = list(set(df_all_.reportDate.values))
    #print(periods[0])
    df_all_.reset_index().tail()
    df_all_[df_all_.reportDate == periods[0]].reset_index().tail()
    df_current = df_all_[df_all_.reportDate == max(periods)].reset_index(drop=True)
    df_previous = df_all_[df_all_.reportDate == min(periods)].reset_index(drop=True)
    df_current_g = df_current.groupby(['nameOfIssuer','nameOfIssuer_link','cusip']).sum().sort_values('value', ascending=False)
    df_previous_g = df_previous.groupby(['nameOfIssuer','nameOfIssuer_link','cusip']).sum().sort_values('value', ascending=False)
    df_diff = df_current_g - df_previous_g
    df_heavy_ = df_current_g
    df_hot_ = df_diff[df_diff.value > 0]
    df_cold_ = df_diff[df_diff.value < 0]
    
    return df_heavy_, df_hot_, df_cold_
    