# Namma Mart Smart Sales Dashboard

A Python desktop application built with Tkinter, Pandas, NumPy and Matplotlib. It uses a local CSV file and works offline after the Python packages are installed.

## Features

- KPI cards: revenue, sales records, average order value, units, 30-day growth, best seller and top region
- Date, region and category filters
- Monthly revenue, category mix, top products and regional unit charts
- 7-day moving average and a 30-day trend/weekday forecast
- Product, region and category performance comparisons
- Pareto (80/20) product revenue analysis
- Weekday-by-month revenue heatmap
- Unusual high/low sales-day flags using a z-score
- Declining-product alerts and low-demand analysis
- Plain-English business insights and suggested actions
- Monthly revenue target progress and equal-length period comparison
- Gross profit and profit-margin analysis when unit costs are supplied
- Customer counts, repeat-customer analysis and top-customer revenue when customer IDs are supplied
- Input validation for dates, names, units, prices and optional costs
- Exact-match duplicate-sale warning before saving a new transaction
- One-time `.bak` backup before the app rewrites the CSV after adding a sale
- Searchable and sortable transaction records
- Add a sale, including optional unit cost and customer ID
- Load another compatible CSV after a confirmation prompt
- Export filtered CSV data, charts, text summaries and PDF reports

## Requirements

- Python 3.10 or newer
- Windows, macOS or Linux with Tk support

## Run in VS Code (Windows PowerShell)

Open this folder in VS Code. In the terminal, make sure the current directory contains `namma_mart_app.py` and `requirements.txt`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python namma_mart_app.py
```

If PowerShell blocks activation, run the app with the environment's Python directly:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe namma_mart_app.py
```

## Run tests

```powershell
python test_analytics.py
```

## CSV format

The CSV must contain these columns:

`date, product, category, region, units, unit_price`

Optional columns:

`unit_cost, customer_id`

Dates should use `YYYY-MM-DD`. `units` must be a positive whole number and `unit_price` must be positive. `unit_cost` must be zero or positive when provided. The application calculates revenue as `units × unit_price`, cost as `units × unit_cost`, and gross profit as revenue minus cost. Blank optional fields are allowed.

## Important notes

- `sales_data.csv` contains example/demo sales records. Replace it with real, authorized shop data before using the results for business decisions.
- The forecast is a simple linear trend adjusted for weekday patterns. It is a planning estimate, not a machine-learning model or a guarantee.
- Unusual-day flags indicate statistical outliers, not fraud.
- Low-demand and decline alerts are based on sales records. The app cannot calculate stock reorder quantities because the CSV does not include inventory, purchases or supplier lead times.
- Each row is treated as one sales record/order for the average order value calculation. If one customer order can contain multiple product rows, add an order ID column and group by it for a true average order value.
- Profit metrics use only rows with a supplied unit cost. Customer metrics use only rows with a supplied customer ID. The bundled demo data has neither, so those sections explain that real values are needed rather than inventing them.
- Duplicate detection compares date, product, category, region, units and unit price. It warns about exact matches but allows the user to confirm legitimate repeat purchases.
- Period comparison uses the latest month-to-date and compares it with the same calendar days of the previous month. A percentage is not shown when the earlier period has zero revenue.
- The PDF export includes KPIs, available business analysis, insights and recommended actions. Install all packages from `requirements.txt` before using it.
