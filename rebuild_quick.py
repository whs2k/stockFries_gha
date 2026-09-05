import datetime
import re
from config import fund_dict

with open('footer.html', 'r') as file:
    footer = file.read().replace('\n', '')
with open('navbar.html', 'r') as file:
    header = file.read().replace('\n', '')
with open('body.html', 'r') as file:
    body_string = file.read().replace('\n', '')
with open('about_body.html', 'r') as file:
    about_body_string = file.read().replace('\n', '')

# We need the tables for body.html. Let's extract them from existing index.html
with open('index.html', 'r') as file:
    index_content = file.read()

tables = re.findall(r'<table.*?</table>', index_content, re.DOTALL)
if len(tables) >= 3:
    table_html_heavy, table_html_hot, table_html_cold = tables[0], tables[1], tables[2]
else:
    table_html_heavy, table_html_hot, table_html_cold = "", "", ""

body = body_string % (table_html_heavy, table_html_hot, table_html_cold)

date_match = re.search(r'Most Recent Filing Date: <a>(.*?)</a>', index_content)
most_recent_filing_date = date_match.group(1) if date_match else '2026-08-14'
header = header.replace('most_recent_filing_date_html', most_recent_filing_date)

today_date_str = datetime.date.today().strftime('%Y-%m-%d')
footer = footer.replace('{most_recent_scrape_date}', today_date_str).replace('most_recent_scrape_date_html', today_date_str)

funds_items = []
for name, url in fund_dict.items():
    cik = url.split('CIK=')[1].split('&')[0] if 'CIK=' in url else ''
    cik_badge = f'<span class="badge badge-light text-muted border mr-2">CIK: {cik}</span>' if cik else ''
    item_html = (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
        f'class="list-group-item list-group-item-action d-flex justify-content-between align-items-center py-2 px-3">'
        f'<div><strong class="text-dark">{name}</strong></div>'
        f'<div>{cik_badge}<span class="btn btn-outline-primary btn-sm py-1 px-2" style="font-size: 0.75rem;">'
        f'SEC Filings <i class="fa fa-external-link ml-1"></i></span></div>'
        f'</a>'
    )
    funds_items.append(item_html)
funds_list_html = "\n".join(funds_items)
about_body = about_body_string.format(funds_list=funds_list_html)

final = header + body + footer 
final_about = header + about_body + footer

with open('index.html', 'w') as file:
    file.write(final)
with open('about.html', 'w') as file:
    file.write(final_about)
print("Quick rebuild complete.")
