import os
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
INPUT_CSV = "icfs.csv"
OUTPUT_FILE = "Submission_File_IBF_advisor.xlsx"
YOUR_NAME = "Dhruv Shetty"

FINAL_COLUMNS = [
    "profile_url",
    "name",
    "title",
    "firm",
    "city",
    "state",
    "phone",
    "designations",
    "member_since",
    "scraped_by",
]

# Standard US 50 States + DC & Puerto Rico full-name to 2-letter uppercase mapping
STATE_MAP = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
    "DISTRICT OF COLUMBIA": "DC",
    "PUERTO RICO": "PR",
}


def parse_location(location_str: str):
    """Splits a combined location string into city and 2-letter uppercase state."""
    clean_loc = location_str.replace(",,", ",").strip()
    city = clean_loc
    state = ""

    if "," in clean_loc:
        parts = clean_loc.rsplit(",", 1)
        city = parts[0].strip()
        candidate = parts[1].strip()

        # Check if already a 2-letter code (e.g. 'NJ')
        if len(candidate) == 2 and candidate.isalpha():
            state = candidate.upper()
        # Check if full state name (e.g. 'New Jersey' -> 'NJ')
        elif candidate.upper() in STATE_MAP:
            state = STATE_MAP[candidate.upper()]

    return city, state


if not os.path.exists(INPUT_CSV):
    print(f"Error: Could not find '{INPUT_CSV}'. Make sure it is in the same folder.")
    exit(1)

df = pd.read_csv(INPUT_CSV)
print(f"Loaded {len(df)} rows from {INPUT_CSV}")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

session = requests.Session()
session.headers.update(headers)

records = []
total = len(df)

for idx, (_, row) in enumerate(df.iterrows(), start=1):
    profile_url = str(row.get("fa-result-card href", "")).strip()
    raw_name = str(row.get("fa-result-name", "")).strip()
    raw_meta = str(row.get("fa-result-meta", "")).strip()
    raw_desig = str(
        row.get("fa-result-desig-pill", row.get("fa-result-desig", ""))
    ).strip()
    raw_since = str(row.get("fa-result-since", "")).strip()

    # 1. Clean Name (strip trailing designations and registered marks)
    name = re.sub(r"[®™]", "", raw_name)
    if "," in name:
        name = name.split(",")[0].strip()

    # 2. Clean Designations
    clean_desig = ""
    if raw_desig and raw_desig.lower() != "nan":
        clean_desig = re.sub(r"[®™]", "", raw_desig).strip()

    # 3. Clean Member Since (extract year or date)
    since_match = re.search(r"(\d{4}(?:-\d{2}-\d{2})?)", raw_since)
    member_since = (
        since_match.group(1)
        if since_match
        else raw_since.replace("Since", "").strip()
    )

    # 4. Parse Meta: Title, Firm, City, State
    title = ""
    firm = ""
    city = ""
    state = ""

    if raw_meta and raw_meta.lower() != "nan":
        meta_parts = [p.strip() for p in raw_meta.split("·")]

        # Last segment always holds Location
        city, state = parse_location(meta_parts[-1])

        # Remaining segments hold Title and/or Firm
        other_parts = meta_parts[:-1]
        if len(other_parts) == 1:
            part = other_parts[0]
            if any(
                t in part.lower()
                for t in [
                    "advisor",
                    "planner",
                    "president",
                    "partner",
                    "consultant",
                    "director",
                    "officer",
                    "manager",
                ]
            ):
                title = part
            else:
                firm = part
        elif len(other_parts) >= 2:
            title = other_parts[0]
            firm = other_parts[1]

    # 5. Fetch Phone directly from Profile Page
    phone = ""
    if profile_url.startswith("http"):
        try:
            res = session.get(profile_url, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                phone_tag = soup.select_one("a[href^='tel:']")
                if phone_tag:
                    phone = phone_tag.get_text().strip()
                else:
                    phone_match = re.search(
                        r"PHONE[:\s]+([(\d\s\-.xEXT)]+)",
                        soup.get_text(),
                        re.IGNORECASE,
                    )
                    if phone_match:
                        phone = phone_match.group(1).strip()
        except Exception:
            phone = ""

    records.append({
        "profile_url": profile_url,
        "name": name,
        "title": title,
        "firm": firm,
        "city": city,
        "state": state,
        "phone": phone,
        "designations": clean_desig,
        "member_since": member_since,
        "scraped_by": YOUR_NAME,
    })

    if idx % 50 == 0 or idx == total:
        print(f"Processed {idx}/{total} advisors...")
        time.sleep(0.2)

# --- Save to Excel ---
final_df = pd.DataFrame(records)
final_df = final_df.drop_duplicates(subset=["profile_url"], keep="first")
final_df = final_df.reindex(columns=FINAL_COLUMNS).fillna("")

final_df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")
print(f"\nDone! Successfully generated '{OUTPUT_FILE}' with {len(final_df)} rows.")