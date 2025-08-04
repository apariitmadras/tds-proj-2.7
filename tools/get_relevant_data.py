# /// script
# requires-python = ">=3.11"
# dependencies = ["beautifulsoup4"]
# ///
from bs4 import BeautifulSoup

with open("scraped_content.html", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Grab the first wikitable inside <main>
table = soup.select_one("main#content table.wikitable")
rows  = table.select("tr")[1:]  # skip header

for row in rows:
    cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
    print(cols)
