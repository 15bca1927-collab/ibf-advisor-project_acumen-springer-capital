# US Advisor Intelligence: Data Extraction & Prospecting Dashboard

An end-to-end data pipeline and interactive business dashboard built to scrape, enrich, and visualize contact information for ~2,400 advisor firms across the United States from `icfs.com`.

---

## 📌 Project Overview

This project is divided into two operational phases:

1. **Part 1 – High-Resilience Data Extraction:** Automated web scraping pipeline built to extract complete phone numbers (with extensions) and direct email addresses, bypassing Cloudflare protections and de-obfuscating dynamic HTML button payloads.
2. **Part 2 – Interactive Prospecting Dashboard:** A standalone, responsive analytics dashboard designed for sales, marketing, and research teams to filter advisor firms by geography and digital presence.

---

## 🛠️ Tech Stack & Dependencies

* **Networking & Anti-Bot Bypass:** `curl_cffi` (impersonating Chrome TLS/JA3/HTTP2 fingerprints).
* **Concurrency:** `asyncio` for multi-worker scheduling with rate-limit backoff.
* **HTML Parsing:** `BeautifulSoup4` (`bs4`) and Regular Expressions (`re`).
* **Data Processing & I/O:** `pandas`, `openpyxl`.
* **Dashboard Technologies:** Standalone HTML5 / Bootstrap 5 / DataTables.js, with an optional `streamlit` interface.

---

## 🚀 Getting Started

### 1. Installation

Clone this repository and install the dependencies:

```bash
git clone [https://github.com/](https://github.com/)<15bca1927-collab>/<ibf-advisor-project_acumen-springer-capital>.git
cd <ibf-advisor-project_acumen-springer-capital>
pip install -r requirements.txt
```

---

## ⚙️ Running the Project

### Phase 1: Data Scraping & Enrichment
To run the crawler pass that populates missing emails and phone numbers into the master file:

```bash
python fast_fetch.py
```
* **Output:** Progressively updates `Submission_File_IBF_advisor.xlsx` with automatic checkpointing every 25 rows.

### Phase 2: Generating & Launching the Dashboard

#### Option A: Standalone HTML Dashboard (Zero Configuration)
Generate the self-contained dashboard:

```bash
python dashboard_generator.py
```
* Double-click `dashboard.html` or open it in any web browser.
* Provides live metric recalculations, multi-field dropdown filters (State, City, ZIP, Digital Presence), and filtered CSV exports.

#### Option B: Streamlit Web App
To run the local Streamlit server:

```bash
streamlit run app.py
```

---

## 📊 Key Dashboard Features

* **Real-Time KPIs:** Dynamic counters for *Total Advisor Pool*, *Filtered Count*, *Unique States*, *Unique Cities*, *Unique ZIPs*, *Firms with Email*, and *Firms with Website*.
* **Multi-Tier Filtering:** Header-level controls to slice data across geographic and digital indicators simultaneously.
* **Prospecting Export:** One-click CSV export of the active filtered shortlist for direct sales outreach.

---

## 📄 Documentation

A complete technical breakdown—covering the Cloudflare 403 bypass, pandas data typing resolutions, and DOM email button de-obfuscation (`data-u` and `data-d` tags)—is available in `Approach_Documentation_Part1.docx`. whcich is submitted to the mentor/assigner Wirg Prajapati