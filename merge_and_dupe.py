import glob
import os
import re
import pandas as pd

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

# Standard US 2-letter state map
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

    # Check 2-letter uppercase postal code at end
    m = re.search(r"^(.*?)[,\s]+([A-Za-z]{2})$", loc)
    if m:
        city = m.group(1).rstrip(",").strip()
        state = m.group(2).upper()
        return city, state

    # Check full state name
    if "," in loc:
        parts = loc.rsplit(",", 1)
        st_candidate = parts[1].strip().lower()
        if st_candidate in STATE_MAP:
            return parts[0].strip(), STATE_MAP[st_candidate]

    return loc, ""


def extract_row_designations(row) -> set:
    found = set()
    for col in row.index:
        if "pill" in col.lower() or "desig" in col.lower():
            val = str(row[col]).strip()
            if val and val.lower() != "nan":
                cleaned = re.sub(r"[®™]", "", val).strip()
                if cleaned:
                    found.add(cleaned)
    return found


def main():
    # 1. Gather all CSVs in the folder
    csv_files = [f for f in glob.glob("*.csv") if not f.startswith("Submission")]
    print(f"Reading {len(csv_files)} CSV files: {csv_files}\n")

    if not csv_files:
        print("No CSV files found!")
        return

    # 2. Accumulate designations and profile records
    url_to_designations = {}
    url_to_record = {}

    for f in csv_files:
        try:
            df = pd.read_csv(f)
        except Exception as e:
            print(f"Skipping {f}: {e}")
            continue

        # Detect URL column
        url_col = None
        for col in df.columns:
            if "href" in col.lower() or "url" in col.lower():
                url_col = col
                break

        if not url_col:
            continue

        for _, row in df.iterrows():
            url = str(row.get(url_col, "")).strip()
            if not url or url.lower() == "nan":
                continue

            # Accumulate all unique badges/designations for this advisor
            pills = extract_row_designations(row)
            if url not in url_to_designations:
                url_to_designations[url] = set()
            url_to_designations[url].update(pills)

            # Store advisor metadata (first time seen)
            if url not in url_to_record:
                raw_name = str(row.get("fa-result-name", "")).strip()
                raw_meta = str(row.get("fa-result-meta", "")).strip()
                raw_since = str(row.get("fa-result-since", "")).strip()

                member_since = ""
                if raw_since and raw_since.lower() != "nan":
                    member_since = re.sub(r"^Since\s+", "", raw_since, flags=re.IGNORECASE).strip()

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

                url_to_record[url] = {
                    "profile_url": url,
                    "name": raw_name,
                    "title": title,
                    "firm": firm,
                    "city": city,
                    "state": state,
                    "phone": "",
                    "member_since": member_since,
                    "scraped_by": YOUR_NAME,
                }

    # 3. Assemble deduplicated records with merged designations
    final_rows = []
    for url, base_rec in url_to_record.items():
        all_desigs = sorted(list(url_to_designations.get(url, set())))
        base_rec["designations"] = ", ".join(all_desigs)
        final_rows.append(base_rec)

    # 4. Save to Excel
    out_df = pd.DataFrame(final_rows).reindex(columns=REQUIRED_COLUMNS).fillna("")
    out_df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")

    print("=" * 50)
    print(f"COMPLETE! Processed {len(csv_files)} files.")
    print(f"Total unique advisors: {len(out_df)}")
    print(f"Exported directly to: '{OUTPUT_FILE}'")
    print("=" * 50)


if __name__ == "__main__":
    main()