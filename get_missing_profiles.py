import asyncio
import os
import re
from typing import Any
import pandas as pd
from playwright.async_api import async_playwright

EXCEL_FILE = "Submission_File_IBF_advisor.xlsx"
YOUR_NAME = "Dhruv Ratnakar Shetty"

# All 50 US State postal codes + DC to exhaustively cover the entire directory
US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
]

COLUMNS = [
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

async def scrape_all() -> None:
    # Explicit type annotation prevents Hashable/invariant dictionary errors in Pylance
    existing_records: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Load existing records so already-scraped profiles are preserved without duplicates
    if os.path.exists(EXCEL_FILE):
        try:
            df_existing = pd.read_excel(EXCEL_FILE)
            records_raw = df_existing.to_dict(orient="records")
            for item in records_raw:
                record_dict: dict[str, Any] = {str(k): v for k, v in item.items()}
                existing_records.append(record_dict)
                url = str(record_dict.get("profile_url", "")).strip()
                if url:
                    seen_urls.add(url)
            print(f"Loaded {len(seen_urls)} existing advisors from {EXCEL_FILE}.")
        except Exception as e:
            print(f"Notice: Could not load existing Excel file ({e}). Starting fresh.")

    new_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for st in US_STATES:
            print(f"\n==========================================")
            print(f"Searching State: {st}")
            print(f"==========================================")

            page_num = 1
            while True:
                target_url = f"https://icfs.com/find-advisor?state={st}&page={page_num}"

                try:
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"Timeout on {target_url}, retrying once: {e}")
                    await asyncio.sleep(3)
                    try:
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    except Exception as retry_err:
                        print(f"Failed to load {target_url}: {retry_err}")
                        break

                cards = await page.query_selector_all(".fa-result-card, a[href*='/advisor/']")
                if not cards:
                    break

                page_new = 0

                for card in cards:
                    href = await card.get_attribute("href")
                    if not href or "/advisor/" not in href:
                        continue

                    profile_url = str(href).split("?")[0].rstrip("/")
                    if profile_url.startswith("/"):
                        profile_url = "https://icfs.com" + profile_url

                    if profile_url in seen_urls:
                        continue

                    name_elem = await card.query_selector(".fa-result-name")
                    name = (await name_elem.inner_text()).strip() if name_elem else ""

                    meta_elem = await card.query_selector(".fa-result-meta")
                    meta = (await meta_elem.inner_text()).strip() if meta_elem else ""

                    title = ""
                    city = ""
                    state_code = st
                    if "·" in meta:
                        parts = [p.strip() for p in meta.split("·")]
                        title = parts[0]
                        loc = parts[-1]
                    else:
                        loc = meta

                    if "," in loc:
                        loc_parts = loc.rsplit(",", 1)
                        city = loc_parts[0].strip()
                        state_code = loc_parts[1].strip().upper()
                    elif loc:
                        city = loc

                    pills = await card.query_selector_all(".fa-result-desig-pill")
                    desig_list: list[str] = []
                    for pill in pills:
                        txt = (await pill.inner_text()).strip()
                        txt = re.sub(r"[®™]", "", txt)
                        if txt and txt not in desig_list:
                            desig_list.append(txt)
                    designations = ", ".join(desig_list)

                    since_elem = await card.query_selector(".fa-result-since")
                    since_raw = (await since_elem.inner_text()).strip() if since_elem else ""
                    member_since = re.sub(r"^Since\s+", "", since_raw).strip()

                    rec: dict[str, Any] = {
                        "profile_url": profile_url,
                        "name": name,
                        "title": title,
                        "firm": "",
                        "city": city,
                        "state": state_code,
                        "phone": "",
                        "designations": designations,
                        "member_since": member_since,
                        "scraped_by": YOUR_NAME,
                    }

                    seen_urls.add(profile_url)
                    existing_records.append(rec)
                    new_count += 1
                    page_new += 1

                print(f"State {st} | Page {page_num}: Added {page_new} new advisors (Total collected: {len(seen_urls)})")

                if len(cards) < 20:
                    break

                page_num += 1

                # Checkpoint save every 50 additions
                if new_count > 0 and new_count % 50 == 0:
                    df_cp = pd.DataFrame(existing_records).reindex(columns=COLUMNS).fillna("")
                    df_cp.drop_duplicates(subset=["profile_url"], keep="first", inplace=True)
                    df_cp.to_excel(EXCEL_FILE, index=False)
                    print(f"--> [Checkpoint] Saved {len(df_cp)} records to {EXCEL_FILE}")

        await browser.close()

    # Final export
    final_df = pd.DataFrame(existing_records).reindex(columns=COLUMNS).fillna("")
    final_df.drop_duplicates(subset=["profile_url"], keep="first", inplace=True)
    final_df.to_excel(EXCEL_FILE, index=False)

    print("\n==========================================")
    print("EXTRACTION COMPLETE!")
    print(f"Total Unique Advisors across all states: {len(final_df)}")
    print(f"Newly added in this run: {new_count}")
    print(f"Saved to: {EXCEL_FILE}")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(scrape_all())