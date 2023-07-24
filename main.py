from config import fund_dict
import requests
import pandas as pd
from helper import create_holdings_df, process_scraped_data
import traceback
import numpy as np
import datetime

def main():
	df_all = pd.DataFrame()
	for fund in fund_dict:
		try:
			fund_name = fund
			cik = fund_dict[fund].split('CIK=')[1].split('&')[0]
			df_fund = create_holdings_df(cik_=cik,fund_name_=fund_name)
			df_all = pd.concat([df_all, df_fund]).reset_index(drop=True)
			print('Fund: {} CIK: {} added to df  '.format(fund_name, cik))
			#print(df_all.tail())
		except:
			print('Issue with: ', fund)
			print(traceback.format_exc())
			continue

	df_all.to_csv('data_by_stocks.csv',index=False)
	most_recent_filing_date = str(df_all.filingDate.max())
	print('most recent filing date: ', most_recent_filing_date)

	df_heavy, df_hot, df_cold, df_puts = process_scraped_data(df_all)

	df_heavy_formatted = df_heavy.reset_index()[['nameOfIssuer_link','value']]
	df_heavy_formatted['value'] = df_heavy_formatted['value'].replace(r'^\s*$', '0', regex=True)#.apply(lambda x: x * 1000)

	int_frmt = lambda x: '${:,}'.format(x)
	float_frmt = lambda x: '{:,.0f}'.format(x) if x > 1e3 else '{:,.2f}'.format(x)
	frmt_map = {np.dtype('int64'):int_frmt, np.dtype('float64'):float_frmt}
	frmt = {col:frmt_map[df_heavy_formatted.dtypes[col]] for col in df_heavy_formatted.columns if df_heavy_formatted.dtypes[col] in frmt_map.keys()}

	df_hot_formatted = df_hot.reset_index()[['nameOfIssuer_link','value']]
	df_hot_formatted['value'] = df_hot_formatted['value'].replace(r'^\s*$', '0', regex=True)#.apply(lambda x: x * 1000)
	frmt_hot = {col:frmt_map[df_hot_formatted.dtypes[col]] for col in df_hot_formatted.columns if df_hot_formatted.dtypes[col] in frmt_map.keys()}

	df_cold_formatted = df_cold.reset_index()[['nameOfIssuer_link','value']]
	df_cold_formatted['value'] = df_cold_formatted['value'].replace(r'^\s*$', '0', regex=True)#.apply(lambda x: x * 1000)
	frmt_cold = {col:frmt_map[df_cold_formatted.dtypes[col]] for col in df_cold_formatted.columns if df_cold_formatted.dtypes[col] in frmt_map.keys()}

	df_puts_formatted = df_puts.reset_index()[['nameOfIssuer_link','value','fund_name']]
	df_puts_formatted['value'] = df_puts_formatted['value'].replace(r'^\s*$', '0', regex=True)#.apply(lambda x: x * 1000)


	table_html_heavy = df_heavy_formatted \
	    .sort_values('value', ascending=False).head(35) \
	    .rename(columns={'nameOfIssuer_link':'Stock Link'}) \
	    .to_html(classes="table table-hover table-condensed",
	        #formatters=frmt,
	        index=False,render_links=True, justify="center", escape=False, 
	        max_rows=50, border=4) \
	    #.replace('<td>','<td style = "background-color: hsl(25, 75%, 75%)">')

	table_html_hot = df_hot_formatted \
	    .sort_values('value', ascending=False).head(35) \
	    .rename(columns={'nameOfIssuer_link':'Stock Link'}) \
	    .to_html(classes="table table-hover table-condensed",
	        #formatters=frmt,
	        index=False,render_links=True, justify="center", escape=False, 
	        max_rows=50, border=4) \
	    #.replace('<td>','<td style = "background-color: hsl(25, 75%, 75%)">')

	table_html_cold = df_cold_formatted \
	    .sort_values('value', ascending=True).head(35) \
	    .rename(columns={'nameOfIssuer_link':'Stock Link'}) \
	    .to_html(classes="table table-hover table-condensed",
	        #formatters=frmt,
	        index=False,render_links=True, justify="center", escape=False, 
	        max_rows=50, border=4) \
	    #.replace('<td>','<td style = "background-color: hsl(25, 75%, 75%)">')

	
	table_html_puts = df_puts_formatted \
	    .sort_values('value', ascending=False).head(35) \
	    .rename(columns={'nameOfIssuer_link':'Stock Link','fund_name':'Hedge Funds'}) \
	    .to_html(classes="table table-hover table-condensed",
	        #formatters=frmt,
	        index=False,render_links=True, justify="center", escape=False, 
	        max_rows=50, border=4) \
	    #.replace('<td>','<td style = "background-color: hsl(25, 75%, 75%)">')



	with open('footer.html', 'r') as file:
	    footer = file.read().replace('\n', '')
	with open('navbar.html', 'r') as file:
	    header = file.read().replace('\n', '')
	with open('body.html', 'r') as file:
	    body_string = file.read().replace('\n', '')
	with open('about_body.html', 'r') as file:
	    about_body_string = file.read().replace('\n', '')
	with open('body_shorts.html', 'r') as file:
		puts_body_string = file.read().replace('\n', '')
	
	print('now: ', str(datetime.datetime.now()))
	header = header.format(most_recent_filing_date,'{}')#str(df_all.reportDate.max()))
	footer = footer.format(most_recent_scrape_date=(str(datetime.datetime.now())))
	about_body = about_body_string.format(funds_list=fund_dict).replace("',","',\n")
	body = body_string %(table_html_heavy, table_html_hot, table_html_cold)
	puts_body = puts_body_string %(table_html_puts)

	

	final = header +body+ footer 
	final_about = header+about_body+footer
	final_puts_string = header+puts_body+footer

	with open('index.html', 'w') as file:
	    file.write(final)
	with open('about.html', 'w') as file:
	    file.write(final_about)
	with open('puts.html', 'w') as file:
		file.write(final_puts_string)
	
if __name__ == "__main__":
	main()

