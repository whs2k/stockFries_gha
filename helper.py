import requests
import pandas as pd
import xmltodict
from datetime import datetime, timedelta

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
    df_new['filingLink']=BASE_URL_FORM_TABLE

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
    df_old['filingLink']=BASE_URL_FORM_TABLE
    df_final = pd.concat([df_new, df_old])
    df_final['fund_name'] = fund_name_
    df_final['value'] = df_final['value'].astype('int')
    df_final['fundAllFillingsSECLink']='https://www.sec.gov/edgar/browse/?CIK='+cik_
    return df_final

def process_scraped_data(df_all_):
    lookback_period = 90
    df_all_['nameOfIssuer_link'] =df_all_['nameOfIssuer'].apply(
    lambda x: str('''<a href="http://www.google.com/search?q=stock price {}" 
        target="_blank">{}</a>'''.format(x, x)))
    periods = list(set(df_all_.filingDate.values))
    current_filign_periods = []
    previous_filing_periods = []
    ninty_days_ago = (datetime.today() - timedelta(days=lookback_period)).strftime('%Y-%m-%d')
    oneeighty_days_ago = (datetime.today() - timedelta(days=lookback_period*2)).strftime('%Y-%m-%d')
    for period in periods:
        if period > ninty_days_ago:
            #periods.remove(period)
            current_filign_periods.append(period)
        elif ((period > oneeighty_days_ago) & (period < ninty_days_ago)):
            previous_filing_periods.append(period)
    periods.sort(reverse=True)
    print('current_filign_periods: ', current_filign_periods)
    print('previous_filing_periods: ', previous_filing_periods)
    df_all_.reset_index().tail()
    #df_all_[df_all_.reportDate == periods[0]].reset_index().tail()
    #df_current = df_all_[((df_all_.putCall.isnull()) & (df_all_.reportDate == periods[0]))] \
    df_current = df_all_[((df_all_.putCall.isnull()) & (df_all_.filingDate.isin(current_filign_periods)))] \
        .reset_index(drop=True)
    df_puts_current = df_all_[((df_all_.putCall=='Put') & (df_all_.filingDate.isin(current_filign_periods)))] \
        .reset_index(drop=True)
    #df_previous = df_all_[((df_all_.putCall.isnull()) & (df_all_.reportDate == periods[1]))] \
    df_previous = df_all_[((df_all_.putCall.isnull()) & (df_all_.filingDate.isin(previous_filing_periods)))] \
        .reset_index(drop=True)
    df_puts_current_g = df_puts_current.groupby(['nameOfIssuer','nameOfIssuer_link','cusip']) \
        .agg({'value':'sum','fund_name':lambda x: list(x)}).sort_values('value', ascending=False)
    df_current_g = df_current.groupby(['nameOfIssuer','nameOfIssuer_link','cusip']).sum().sort_values('value', ascending=False)
    df_previous_g = df_previous.groupby(['nameOfIssuer','nameOfIssuer_link','cusip']).sum().sort_values('value', ascending=False)
    df_diff = df_current_g - df_previous_g
    df_heavy_ = df_current_g
    df_hot_ = df_diff[df_diff.value > 0]
    df_cold_ = df_diff[df_diff.value < 0]
    
    return df_heavy_, df_hot_, df_cold_, df_puts_current_g

def send_tweet(tweet_text, consumer_key_,consumer_secret_,access_token_,access_token_secret):

    # In your terminal please set your environment variables by running the following lines of code.
    # export 'CONSUMER_KEY'='<your_consumer_key>'
    # export 'CONSUMER_SECRET'='<your_consumer_secret>'

    consumer_key = consumer_key_#os.environ.get("CONSUMER_KEY")
    consumer_secret = consumer_secret_#os.environ.get("CONSUMER_SECRET")

    # Be sure to add replace the text of the with the text you wish to Tweet. You can also add parameters to post polls, quote Tweets, Tweet with reply settings, and Tweet to Super Followers in addition to other features.
    payload = {"text": tweet_text}

    access_token = access_token_#oauth_tokens["oauth_token"]
    access_token_secret = access_token_secret#oauth_tokens["oauth_token_secret"]

    # Making the request
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        raise Exception(
            "Request returned an error: {} {}".format(response.status_code, response.text)
        )

    print("Response code: {}".format(response.status_code))

    # Saving the response as JSON
    json_response = response.json()
    print(json.dumps(json_response, indent=4, sort_keys=True))
    