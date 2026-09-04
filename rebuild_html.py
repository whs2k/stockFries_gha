import re

def rebuild():
    # Read templates
    with open('navbar.html', 'r') as f:
        navbar = f.read()
    with open('footer.html', 'r') as f:
        footer = f.read()
    
    # We need the current most_recent_scrape_date. 
    # Let's extract it from existing index.html before overwriting
    with open('index.html', 'r') as f:
        index_content = f.read()
    
    # Extract date
    date_match = re.search(r'Most Recent Scrape Date:.*?>(\d{4}-\d{2}-\d{2})<', index_content)
    if date_match:
        scrape_date = date_match.group(1)
    else:
        scrape_date = "2026-09-04" # fallback
        
    footer = footer.replace('most_recent_scrape_date_html', scrape_date)

    pages = ['index.html', 'about.html', 'puts.html', 'blog.html']
    for page in pages:
        with open(page, 'r') as f:
            content = f.read()
        
        # Replace old footer with new footer
        # We find everything from <footer class="footer to </footer>
        new_content = re.sub(r'<footer class="footer.*?</footer>', footer.replace('</html>', ''), content, flags=re.DOTALL)
        
        with open(page, 'w') as f:
            f.write(new_content)

rebuild()
