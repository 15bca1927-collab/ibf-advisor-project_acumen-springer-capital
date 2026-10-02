import asyncio
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

FILE_PATH = "Submission_File_IBF_advisor.xlsx"

if not os.path.exists(FILE_PATH):
    print(f"Error: '{FILE_PATH}' not found in current folder.")
    exit(1)

# 1. Load Excel and maintain string/object dtype
df = pd.read_excel(FILE_PATH)
if "email" not in df.columns:
    df["email"] = ""
df["email"] = df["email"].astype(object).fillna("")

# 2. Gather only rows where email is still missing
to_process = []
for idx, row in df.iterrows():
    e = str(row.get("email", "")).strip()
    if not e or e.lower() in ["nan", "none", ""]:
        url = str(row.get("profile_url", "")).strip()
        if url.startswith("http"):
            to_process.append((idx, url))

already_done = len(df) - len(to_process)
print(f"Total rows in sheet: {len(df)}")
print(f"Already populated: {already_done}")
print(f"Remaining to fetch: {len(to_process)}")

if not to_process:
    print("All rows already have emails!")
    exit(0)

queue = asyncio.Queue()
for item in to_process:
    queue.put_nowait(item)

completed = 0
new_found = 0
total = len(to_process)
lock = asyncio.Lock()

# 5 workers with backoff avoids Cloudflare connection resets
CONCURRENCY = 5


async def fetch_profile(session, url, max_retries=5):
    for attempt in range(1, max_retries + 1):
        try:
            res = await session.get(url, timeout=20)
            if res.status_code == 200:
                return res.text
            elif res.status_code in [429, 503]:
                await asyncio.sleep(2 * attempt)
            else:
                await asyncio.sleep(1)
        except Exception:
            await asyncio.sleep(1.5 * attempt)
    return None


async def worker(worker_id):
    global completed, new_found
    async with AsyncSession(impersonate="chrome124") as session:
        while not queue.empty():
            try:
                idx, url = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            email = ""
            html = await fetch_profile(session, url)

            if html:
                soup = BeautifulSoup(html, "html.parser")

                # Match button.advisor-email-reveal
                btn = soup.select_one("button.advisor-email-reveal")
                if btn:
                    u = str(btn.get("data-u") or "").strip()
                    d = str(btn.get("data-d") or "").strip()
                    if u and d:
                        email = f"{u}@{d}"

                # Fallback to any element containing data-u and data-d
                if not email:
                    elem = soup.find(attrs={"data-u": True, "data-d": True})
                    if elem:
                        u = str(elem.get("data-u") or "").strip()
                        d = str(elem.get("data-d") or "").strip()
                        if u and d:
                            email = f"{u}@{d}"

                # Fallback regex
                if not email:
                    m = re.search(
                        r'data-u=["\']([^"\']+)["\'].*?data-d=["\']([^"\']+)["\']',
                        html,
                    )
                    if m:
                        email = f"{m.group(1).strip()}@{m.group(2).strip()}"

            async with lock:
                if email:
                    df.loc[idx, "email"] = str(email)
                    new_found += 1

                completed += 1
                if completed % 25 == 0 or completed == total:
                    # Save incremental progress
                    df.to_excel(FILE_PATH, index=False)
                    print(
                        f"[{completed}/{total}] Processed | Added this run:"
                        f" {new_found} | Total in Sheet:"
                        f" {already_done + new_found}"
                    )

            queue.task_done()
            # Small yield to prevent thread saturation
            await asyncio.sleep(0.05)


async def main():
    print(
        f"Starting sweep for remaining {total} profiles across {CONCURRENCY}"
        " workers..."
    )
    tasks = [asyncio.create_task(worker(i)) for i in range(CONCURRENCY)]
    await queue.join()
    for t in tasks:
        t.cancel()


# Run
asyncio.run(main())

# Final write
df.to_excel(FILE_PATH, index=False)
print("\nFINISHED!")
print(f"Total Emails Added in this run: {new_found}")
print(f"Grand Total in Sheet: {already_done + new_found} / {len(df)}")
print(f"Saved directly to '{FILE_PATH}'")