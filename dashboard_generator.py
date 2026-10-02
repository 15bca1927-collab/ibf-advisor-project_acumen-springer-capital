import json
import os
import pandas as pd

FILE_PATH = "Submission_File_IBF_advisor.xlsx"

if not os.path.exists(FILE_PATH):
    print(f"Error: Could not find '{FILE_PATH}' in current directory.")
    exit(1)

# 1. Load Part-1 Master Dataset
df = pd.read_excel(FILE_PATH)
df.columns = [str(c).strip() for c in df.columns]

col_map = {str(c).lower(): str(c) for c in df.columns}


def find_col(keywords: list[str]) -> str | None:
    for k in keywords:
        for c_lower, c_orig in col_map.items():
            if k in c_lower:
                return c_orig
    return None


name_col = find_col(["advisor_name", "advisor name", "full_name", "name"]) or df.columns[0]
firm_col = find_col(["firm", "company", "broker", "organization"]) or df.columns[1]
city_col = find_col(["city"]) or "city"
state_col = find_col(["state"]) or "state"
zip_col = find_col(["zip", "postal"]) or "zip"
phone_col = find_col(["phone", "tel"]) or "phone"
email_col = find_col(["email", "mail"]) or "email"
web_col = find_col(["website", "web", "url"]) or "website"


def is_valid_entry(val) -> bool:
    if pd.isna(val):
        return False
    s = str(val).strip().lower()
    return s not in ["", "nan", "none", "n/a", "null"]


# 2. Build Records cleanly without triggering Pylance 'Never' type issues
records: list[dict] = []
for _, row in df.iterrows():
    val_name = str(row.get(name_col, "")).strip() if not pd.isna(row.get(name_col)) else ""
    val_firm = str(row.get(firm_col, "")).strip() if not pd.isna(row.get(firm_col)) else ""
    val_city = str(row.get(city_col, "")).strip() if not pd.isna(row.get(city_col)) else ""
    val_state = str(row.get(state_col, "")).strip() if not pd.isna(row.get(state_col)) else ""
    val_zip = str(row.get(zip_col, "")).strip() if not pd.isna(row.get(zip_col)) else ""
    val_phone = str(row.get(phone_col, "")).strip() if not pd.isna(row.get(phone_col)) else ""
    val_email = str(row.get(email_col, "")).strip() if not pd.isna(row.get(email_col)) else ""
    val_web = str(row.get(web_col, "")).strip() if not pd.isna(row.get(web_col)) else ""

    records.append(
        {
            "name": val_name,
            "firm": val_firm,
            "city": val_city,
            "state": val_state,
            "zip": val_zip,
            "phone": val_phone,
            "email": val_email,
            "has_email": is_valid_entry(val_email),
            "has_phone": is_valid_entry(val_phone),
            "has_website": is_valid_entry(val_web),
        }
    )

json_data = json.dumps(records)
total_count = len(records)

# 3. Generate HTML template
html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>US Advisor Prospecting Dashboard</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
  <style>
    body {{ background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    .kpi-card {{ border: none; border-radius: 10px; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.06); padding: 16px; border-left: 4px solid #1f4e79; }}
    .kpi-title {{ font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #6c757d; margin-bottom: 4px; }}
    .kpi-val {{ font-size: 1.6rem; font-weight: 700; color: #1f4e79; }}
    .filter-panel {{ background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); padding: 20px; margin-bottom: 20px; }}
    .table-container {{ background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); padding: 20px; }}
    .badge-no {{ background-color: #ffebee; color: #c62828; font-weight: 600; padding: 4px 8px; border-radius: 6px; font-size: 0.85rem; }}
  </style>
</head>
<body class="p-4">
  <div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="fw-bold mb-1" style="color: #1f4e79;"><i class="bi bi-pie-chart-fill me-2"></i>US Advisor Prospecting Dashboard</h2>
        <span class="text-muted">Master Dataset: <code>Submission_File_IBF_advisor.xlsx</code> | Total Advisors: <strong>{total_count:,}</strong></span>
      </div>
      <div>
        <button class="btn btn-outline-danger btn-sm me-2" onclick="resetAllFilters()"><i class="bi bi-arrow-counterclockwise"></i> Reset Filters</button>
        <button class="btn btn-primary btn-sm" onclick="exportFilteredCSV()"><i class="bi bi-download"></i> Export Filtered CSV</button>
      </div>
    </div>

    <!-- Step 3: Dynamic KPI Metrics -->
    <div class="row g-3 mb-4">
      <div class="col-md-3 col-sm-6">
        <div class="kpi-card" style="border-left-color: #1f4e79;">
          <div class="kpi-title">Filtered Advisor Count</div>
          <div class="kpi-val" id="metric-filtered">{total_count:,}</div>
        </div>
      </div>
      <div class="col-md-3 col-sm-6">
        <div class="kpi-card" style="border-left-color: #0288d1;">
          <div class="kpi-title">Unique States</div>
          <div class="kpi-val" id="metric-states">0</div>
        </div>
      </div>
      <div class="col-md-3 col-sm-6">
        <div class="kpi-card" style="border-left-color: #00897b;">
          <div class="kpi-title">Unique Cities</div>
          <div class="kpi-val" id="metric-cities">0</div>
        </div>
      </div>
      <div class="col-md-3 col-sm-6">
        <div class="kpi-card" style="border-left-color: #7b1fa2;">
          <div class="kpi-title">Unique ZIP Codes</div>
          <div class="kpi-val" id="metric-zips">0</div>
        </div>
      </div>
      <div class="col-md-4 col-sm-6">
        <div class="kpi-card" style="border-left-color: #388e3c;">
          <div class="kpi-title">Firms with Email</div>
          <div class="kpi-val" id="metric-emails">0</div>
        </div>
      </div>
      <div class="col-md-4 col-sm-6">
        <div class="kpi-card" style="border-left-color: #f57c00;">
          <div class="kpi-title">Firms with Website</div>
          <div class="kpi-val" id="metric-websites">0</div>
        </div>
      </div>
      <div class="col-md-4 col-sm-6">
        <div class="kpi-card" style="border-left-color: #5c6bc0;">
          <div class="kpi-title">Total Advisor Pool</div>
          <div class="kpi-val">{total_count:,}</div>
        </div>
      </div>
    </div>

    <!-- Step 2: Interactive Filter Controls -->
    <div class="filter-panel">
      <h6 class="fw-bold mb-3" style="color: #1f4e79;"><i class="bi bi-funnel-fill me-1"></i>Filter Controls</h6>
      <div class="row g-2">
        <div class="col-md-3">
          <label class="form-label small fw-semibold">State</label>
          <select id="filter-state" class="form-select form-select-sm" onchange="applyFilters()">
            <option value="">All States</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label small fw-semibold">City</label>
          <select id="filter-city" class="form-select form-select-sm" onchange="applyFilters()">
            <option value="">All Cities</option>
          </select>
        </div>
        <div class="col-md-2">
          <label class="form-label small fw-semibold">ZIP Code</label>
          <select id="filter-zip" class="form-select form-select-sm" onchange="applyFilters()">
            <option value="">All ZIPs</option>
          </select>
        </div>
        <div class="col-md-2">
          <label class="form-label small fw-semibold">Has Email</label>
          <select id="filter-email" class="form-select form-select-sm" onchange="applyFilters()">
            <option value="">All</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>
        <div class="col-md-2">
          <label class="form-label small fw-semibold">Has Website</label>
          <select id="filter-web" class="form-select form-select-sm" onchange="applyFilters()">
            <option value="">All</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Step 4: Detailed Advisor Listing Table -->
    <div class="table-container">
      <table id="advisorTable" class="table table-hover table-striped w-100 align-middle">
        <thead class="table-light">
          <tr>
            <th>Advisor Name</th>
            <th>Firm / Company</th>
            <th>City</th>
            <th>State</th>
            <th>ZIP</th>
            <th>Phone</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
  <script>
    const rawData = {json_data};
    let dataTable;

    $(document).ready(function() {{
      populateDropdowns();

      dataTable = $('#advisorTable').DataTable({{
        data: rawData,
        columns: [
          {{ data: 'name', defaultContent: '-' }},
          {{ data: 'firm', defaultContent: '-' }},
          {{ data: 'city', defaultContent: '-' }},
          {{ data: 'state', defaultContent: '-' }},
          {{ data: 'zip', defaultContent: '-' }},
          {{ data: 'phone', render: function(d) {{ return d ? `<a href="tel:${{d}}">${{d}}</a>` : '<span class="badge-no">No Phone</span>'; }} }},
          {{ data: 'email', render: function(d) {{ return d ? `<a href="mailto:${{d}}">${{d}}</a>` : '<span class="badge-no">No Email</span>'; }} }}
        ],
        pageLength: 20,
        lengthMenu: [10, 20, 50, 100],
        order: [[0, 'asc']],
        drawCallback: function() {{
          updateDynamicKPIs(this.api());
        }}
      }});

      $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {{
        const row = rawData[dataIndex];
        const stateF = $('#filter-state').val();
        const cityF = $('#filter-city').val();
        const zipF = $('#filter-zip').val();
        const emailF = $('#filter-email').val();
        const webF = $('#filter-web').val();

        if (stateF && row.state !== stateF) return false;
        if (cityF && row.city !== cityF) return false;
        if (zipF && row.zip !== zipF) return false;
        if (emailF === 'yes' && !row.has_email) return false;
        if (emailF === 'no' && row.has_email) return false;
        if (webF === 'yes' && !row.has_website) return false;
        if (webF === 'no' && row.has_website) return false;

        return true;
      }});
    }});

    function populateDropdowns() {{
      const states = [...new Set(rawData.map(r => r.state).filter(Boolean))].sort();
      const cities = [...new Set(rawData.map(r => r.city).filter(Boolean))].sort();
      const zips = [...new Set(rawData.map(r => r.zip).filter(Boolean))].sort();

      states.forEach(s => $('#filter-state').append(new Option(s, s)));
      cities.forEach(c => $('#filter-city').append(new Option(c, c)));
      zips.forEach(z => $('#filter-zip').append(new Option(z, z)));
    }}

    function applyFilters() {{
      dataTable.draw();
    }}

    function resetAllFilters() {{
      $('#filter-state, #filter-city, #filter-zip, #filter-email, #filter-web').val('');
      dataTable.search('').draw();
    }}

    function updateDynamicKPIs(api) {{
      const filteredIndexes = api.rows({{ search: 'applied' }}).indexes().toArray();
      const rows = filteredIndexes.map(idx => rawData[idx]);

      $('#metric-filtered').text(rows.length.toLocaleString());

      const states = new Set(rows.map(r => r.state).filter(Boolean));
      const cities = new Set(rows.map(r => r.city).filter(Boolean));
      const zips = new Set(rows.map(r => r.zip).filter(Boolean));
      const emails = rows.filter(r => r.has_email).length;
      const websites = rows.filter(r => r.has_website).length;

      $('#metric-states').text(states.size);
      $('#metric-cities').text(cities.size.toLocaleString());
      $('#metric-zips').text(zips.size.toLocaleString());
      $('#metric-emails').text(emails.toLocaleString());
      $('#metric-websites').text(websites.toLocaleString());
    }}

    function exportFilteredCSV() {{
      const filteredIndexes = dataTable.rows({{ search: 'applied' }}).indexes().toArray();
      const rows = filteredIndexes.map(idx => rawData[idx]);
      if (!rows.length) return alert('No data to export!');

      let csv = 'Name,Firm,City,State,ZIP,Phone,Email\\n';
      rows.forEach(r => {{
        csv += `"${{r.name}}","${{r.firm}}","${{r.city}}","${{r.state}}","${{r.zip}}","${{r.phone}}","${{r.email}}"\\n`;
      }});

      const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'Filtered_Advisor_Shortlist.csv';
      link.click();
    }}
  </script>
</body>
</html>
"""

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"\nSUCCESS: Generated 'dashboard.html' from {total_count:,} records in '{FILE_PATH}'!")