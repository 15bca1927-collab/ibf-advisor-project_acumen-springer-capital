import os
import re
import pandas as pd

# Files configuration
INPUT_CSV = "icfs (1).csv"
OUTPUT_FILE = "Submission_File_IBF_advisor.xlsx"
YOUR_NAME = "Dhruv Ratnakar Shetty"

REQUIRED_COLUMNS = [
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

# Standard US states + territories for two-letter conversion
STATE_MAP = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH",
    "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC", "puerto rico": "PR", "guam": "GU",
}


def parse_location(loc_str: str) -> tuple[str, str]:
    loc = loc_str.strip()
    if not loc:
        return "", ""

    # Case 1: Trailing 2-letter uppercase postal code (e.g., "East Hanover, NJ")
    m = re.search(r"^(.*?)[,\s]+([A-Za-z]{2})$", loc)
    if m:
        city = m.group(1).rstrip(",").strip()
        state = m.group(2).upper()
        return city, state

    # Case 2: Full state name (e.g., "San Diego, California")
    if "," in loc:
        parts = loc.rsplit(",", 1)
        st_candidate = parts[1].strip().lower()
        if st_candidate in STATE_MAP:
            return parts[0].strip(), STATE_MAP[st_candidate]

    return loc, ""


def main() -> None:
    if not os.path.exists(INPUT_CSV):
        print(f"Error: '{INPUT_CSV}' not found. Place it in this folder and rerun.")
        return

    print(f"Reading '{INPUT_CSV}'...")
    df = pd.read_csv(INPUT_CSV)

    # 1. Deduplicate by profile URL
    url_col = "fa-result-card href"
    df.drop_duplicates(subset=[url_col], keep="first", inplace=True)

    records = []
    for _, row in df.iterrows():
        url = str(row.get(url_col, "")).strip()
        raw_name = str(row.get("fa-result-name", "")).strip()
        raw_meta = str(row.get("fa-result-meta", "")).strip()
        raw_desig = str(row.get("fa-result-desig-pill", "")).strip()
        raw_since = str(row.get("fa-result-since", "")).strip()

        # Clean Designations (strip symbol)
        designations = ""
        if raw_desig and raw_desig.lower() != "nan":
            designations = re.sub(r"[®™]", "", raw_desig).strip()

        # Clean Member Since (e.g., "Since 1990-06-12" -> "1990-06-12")
        member_since = ""
        if raw_since and raw_since.lower() != "nan":
            member_since = re.sub(r"^Since\s+", "", raw_since, flags=re.IGNORECASE).strip()

        # Parse Meta into Title, Firm, City, State
        title, firm, city, state = "", "", "", ""
        if raw_meta and raw_meta.lower() != "nan":
            parts = [p.strip() for p in raw_meta.split("·")]
            loc_candidate = parts[-1]
            city, state = parse_location(loc_candidate)

            non_loc = parts[:-1]
            if len(non_loc) == 1:
                p = non_loc[0]
                if "," in p:
                    sub = [s.strip() for s in p.split(",")]
                    title = sub[0]
                    firm = ", ".join(sub[1:])
                else:
                    title = p
            elif len(non_loc) >= 2:
                title = non_loc[0]
                firm = " · ".join(non_loc[1:])

        records.append({
            "profile_url": url,
            "name": raw_name,
            "title": title,
            "firm": firm,
            "city": city,
            "state": state,
            "phone": "",
            "designations": designations,
            "member_since": member_since,
            "scraped_by": YOUR_NAME,
        })

    # Assemble final dataframe with exact required columns
    out_df = pd.DataFrame(records).reindex(columns=REQUIRED_COLUMNS).fillna("")

    # Export to Excel
    out_df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")

    print("\n-------------------------------------------")
    print(f"SUCCESS! Created '{OUTPUT_FILE}'")
    print(f"Total rows written: {len(out_df)}")
    print("-------------------------------------------")


if __name__ == "__main__":
    main()