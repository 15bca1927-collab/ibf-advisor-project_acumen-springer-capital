import pandas as pd
from bs4 import BeautifulSoup
from curl_cffi import requests

FILE_PATH = "Submission_File_IBF_advisor.xlsx"
df = pd.read_excel(FILE_PATH)

# Check remaining blanks
blanks = df[df["email"].isna() | (df["email"].astype(str).str.strip() == "")]
print(f"Total rows still without email: {len(blanks)}")

# Test the first 3 blank profiles
sample_urls = blanks["profile_url"].dropna().head(3).tolist()
for url in sample_urls:
    res = requests.get(url, impersonate="chrome124", timeout=12)
    soup = BeautifulSoup(res.text, "html.parser")
    btn = soup.select_one("button.advisor-email-reveal")
    has_email = bool(btn and btn.get("data-u"))
    print(f"URL: {url} -> Email element present: {has_email}")