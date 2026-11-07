"""
analytics.py - data logic and chart drawing for the Namma Mart dashboard.
No tkinter in here, so it can be tested on its own.
"""
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from sales_dashboard import generate_sample_csv  # reuse the sample-data maker

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ---------------------------------------------------------------- data
def validate_sales_data(df):
    """Validate required sales columns and values; return a cleaned copy."""
    required = {"date", "product", "category", "region", "units", "unit_price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for col in ("product", "category", "region"):
        out[col] = out[col].astype("string").str.strip()
    out["units"] = pd.to_numeric(out["units"], errors="coerce")
    out["unit_price"] = pd.to_numeric(out["unit_price"], errors="coerce")
    invalid = (out["date"].isna() | out["product"].isna() | (out["product"] == "") |
               out["category"].isna() | (out["category"] == "") | out["region"].isna() |
               (out["region"] == "") | out["units"].isna() | out["unit_price"].isna() |
               (out["units"] <= 0) | (out["units"] % 1 != 0) | (out["unit_price"] <= 0))
    if invalid.any():
        raise ValueError(f"The CSV contains {int(invalid.sum())} invalid row(s). Check dates, names, positive whole-number units and positive prices.")
    out["units"] = out["units"].astype(int)
    # Optional fields are blank when the source CSV does not provide them.
    if "unit_cost" not in out.columns:
        out["unit_cost"] = np.nan
    else:
        raw_cost = out["unit_cost"]
        cost_values = pd.to_numeric(raw_cost, errors="coerce")
        invalid_cost = raw_cost.notna() & raw_cost.astype(str).str.strip().ne("") & cost_values.isna()
        if invalid_cost.any():
            raise ValueError(f"The CSV contains {int(invalid_cost.sum())} invalid unit-cost value(s).")
        out["unit_cost"] = cost_values
        if (out["unit_cost"].dropna() < 0).any():
            raise ValueError("Unit cost cannot be negative.")
    if "customer_id" not in out.columns:
        out["customer_id"] = ""
    out["customer_id"] = out["customer_id"].fillna("").astype(str).str.strip()
    out["revenue"] = out["units"] * out["unit_price"]
    out["cost"] = out["units"] * out["unit_cost"]
    out["profit"] = out["revenue"] - out["cost"]
    out["month"] = out["date"].dt.to_period("M")
    return out


def load_data(path):
    raw = pd.read_csv(path)
    if raw.empty:
        raise ValueError("The selected CSV contains no sales records.")
    return validate_sales_data(raw)


def find_duplicate_sales(df, row):
    """Find exact duplicate transactions using the available sale fields."""
    keys = ["date", "product", "category", "region", "units", "unit_price"]
    candidate = row.iloc[0] if isinstance(row, pd.DataFrame) else row
    mask = pd.Series(True, index=df.index)
    for key in keys:
        value = candidate[key]
        if key == "date":
            mask &= pd.to_datetime(df[key]).dt.normalize() == pd.Timestamp(value).normalize()
        elif key in ("units",):
            mask &= pd.to_numeric(df[key], errors="coerce") == int(value)
        elif key == "unit_price":
            mask &= np.isclose(pd.to_numeric(df[key], errors="coerce"), float(value), equal_nan=False)
        else:
            mask &= df[key].astype(str).str.casefold() == str(value).casefold()
    return df[mask]


def profit_metrics(df):
    """Return profit metrics only when unit cost data is actually available."""
    if df.empty or "unit_cost" not in df or df["unit_cost"].notna().sum() == 0:
        return None
    valid = df[df["unit_cost"].notna()]
    revenue = valid["revenue"].sum()
    profit = valid["profit"].sum()
    return {"revenue": revenue, "cost": valid["cost"].sum(), "profit": profit,
            "margin": profit / revenue * 100 if revenue else 0,
            "records": len(valid)}


def customer_metrics(df):
    """Customer summary when customer IDs are present."""
    if df.empty or "customer_id" not in df:
        return None
    known = df[df["customer_id"].astype(str).str.strip() != ""]
    if known.empty:
        return None
    counts = known.groupby("customer_id").size()
    revenue = known.groupby("customer_id")["revenue"].sum()
    return {"customers": int(counts.size), "repeat": int((counts > 1).sum()),
            "top_customer": str(revenue.idxmax()), "top_revenue": float(revenue.max())}


def compare_periods(df):
    """Compare latest month-to-date revenue with the same days of the prior month."""
    if df.empty:
        return None
    latest = pd.Timestamp(df["date"].max()).normalize()
    current_start = latest.replace(day=1)
    elapsed_days = latest.day
    previous_end = current_start - pd.Timedelta(days=1)
    previous_start = previous_end.replace(day=1)
    previous_end = min(previous_end, previous_start + pd.Timedelta(days=elapsed_days - 1))
    current = df[(df["date"] >= current_start) & (df["date"] <= latest)]["revenue"].sum()
    previous = df[(df["date"] >= previous_start) & (df["date"] <= previous_end)]["revenue"].sum()
    change = None if previous == 0 else (current - previous) / previous * 100
    return {"current": float(current), "previous": float(previous), "change": change,
            "days": elapsed_days, "current_start": current_start, "current_end": latest,
            "previous_start": previous_start, "previous_end": previous_end}


def apply_filters(df, start=None, end=None, region="All", category="All"):
    out = df
    if start is not None:
        out = out[out["date"] >= start]
    if end is not None:
        out = out[out["date"] <= end]
    if region != "All":
        out = out[out["region"] == region]
    if category != "All":
        out = out[out["category"] == category]
    return out


def rupees(x, _pos=None):
    if abs(x) >= 1e7:
        return f"₹{x / 1e7:.1f}Cr"
    if abs(x) >= 1e5:
        return f"₹{x / 1e5:.1f}L"
    return f"₹{x / 1e3:.0f}K"


def _growth(df):
    """% change: last 30 days vs the 30 days before (relative to latest date)."""
    if df.empty:
        return None
    last = df["date"].max()
    cur = df[df["date"] > last - pd.Timedelta(days=30)]["revenue"].sum()
    prev = df[(df["date"] <= last - pd.Timedelta(days=30)) &
              (df["date"] > last - pd.Timedelta(days=60))]["revenue"].sum()
    if prev == 0:
        return None
    return (cur - prev) / prev * 100


def kpis(df):
    if df.empty:
        return {"revenue": 0, "orders": 0, "aov": 0, "units": 0, "growth": None}
    return {
        "revenue": df["revenue"].sum(),
        "orders": len(df),
        "aov": df["revenue"].mean(),
        "units": int(df["units"].sum()),
        "growth": _growth(df),
    }


# ---------------------------------------------------- smart features
def daily_series(df):
    return df.groupby("date")["revenue"].sum().asfreq("D", fill_value=0)


def forecast(df, days=30):
    """Linear trend x weekday pattern. Returns (history, future) or None."""
    s = daily_series(df)
    if len(s) < 21:
        return None
    hist = s.tail(120)
    x = np.arange(len(hist))
    slope, intercept = np.polyfit(x, hist.values, 1)
    trend = slope * x + intercept
    ratio = pd.Series(hist.values / np.where(trend == 0, 1, trend), index=hist.index)
    weekday_factor = ratio.groupby(ratio.index.dayofweek).mean()

    fx = np.arange(len(hist), len(hist) + days)
    fdates = pd.date_range(hist.index[-1] + pd.Timedelta(days=1), periods=days)
    vals = (slope * fx + intercept) * np.array(
        [weekday_factor.get(d.dayofweek, 1.0) for d in fdates])
    return hist, pd.Series(np.clip(vals, 0, None), index=fdates)


def pareto(df):
    """Product revenue sorted desc with cumulative %."""
    p = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
    cum = p.cumsum() / p.sum() * 100
    return p, cum


def declining_products(df, drop_pct=20):
    """Products whose units fell >= drop_pct in last 30 days vs the 30 before."""
    if df.empty:
        return []
    last = df["date"].max()
    cur = df[df["date"] > last - pd.Timedelta(days=30)].groupby("product")["units"].sum()
    prev = df[(df["date"] <= last - pd.Timedelta(days=30)) &
              (df["date"] > last - pd.Timedelta(days=60))].groupby("product")["units"].sum()
    res = []
    for prod, p in prev.items():
        c = cur.get(prod, 0)
        if p >= 10 and (p - c) / p * 100 >= drop_pct:
            res.append((prod, (p - c) / p * 100))
    return sorted(res, key=lambda t: -t[1])


def insights(df):
    """Plain-English findings generated from the filtered data."""
    if df.empty:
        return ["No data for the selected filters."]
    out = []
    m = df.groupby("month")["revenue"].sum()
    # ignore the last month if it is only partly complete
    if len(m) > 2 and df["date"].max() < m.index[-1].end_time.normalize():
        m = m.iloc[:-1]
    out.append(f"Best month: {m.idxmax()} ({rupees(m.max())}). "
               f"Slowest month: {m.idxmin()} ({rupees(m.min())}).")

    p, cum = pareto(df)
    top = p.index[0]
    out.append(f"Top product: {top}, bringing {p.iloc[0] / p.sum() * 100:.0f}% of revenue.")
    n80 = int((cum < 80).sum()) + 1
    out.append(f"80/20 rule: {n80} of {len(p)} products generate 80% of revenue.")

    r = df.groupby("region")["revenue"].sum()
    if len(r) > 1:
        out.append(f"Strongest region: {r.idxmax()}. Weakest: {r.idxmin()} "
                   f"({(1 - r.min() / r.max()) * 100:.0f}% below the best).")

    w = df.groupby(df["date"].dt.dayofweek)["revenue"].sum()
    out.append(f"Busiest day of the week: {WEEKDAYS[w.idxmax()]}. "
               f"Quietest: {WEEKDAYS[w.idxmin()]}.")

    g = _growth(df)
    if g is not None:
        arrow = "up" if g >= 0 else "down"
        out.append(f"Last 30 days revenue is {arrow} {abs(g):.1f}% vs the previous 30 days.")

    f = forecast(df)
    if f:
        out.append(f"Forecast: about {rupees(f[1].sum())} expected in the next 30 days.")
    return out


def trend_detection(df):
    """Overall direction of sales. Returns (label, % change per 30 days) or None."""
    if df.empty:
        return None
    s = daily_series(df)
    if len(s) < 21 or s.mean() == 0:
        return None
    slope, _ = np.polyfit(np.arange(len(s)), s.values, 1)
    pct = slope * 30 / s.mean() * 100
    label = "Upward" if pct > 5 else "Downward" if pct < -5 else "Stable"
    return label, pct


def low_demand_products(df, factor=0.6):
    """Products selling far below the average product. Returns [(product, units, % of avg)]."""
    if df.empty:
        return []
    units = df.groupby("product")["units"].sum()
    avg = units.mean()
    low = units[units < factor * avg].sort_values()
    return [(p, int(u), u / avg * 100) for p, u in low.items()]


def unusual_days(df, z=2.5):
    """Days whose revenue is far from normal (z-score). Strongest first."""
    if df.empty:
        return []
    s = daily_series(df)
    if len(s) < 30 or s.std() == 0:
        return []
    zs = (s - s.mean()) / s.std()
    rows = []
    for d, zv in zs[zs.abs() >= z].sort_values(key=abs, ascending=False).items():
        day = df[df["date"] == d].groupby("product")["revenue"].sum()
        top = day.idxmax() if not day.empty else "no sales"
        share = day.max() / s[d] * 100 if not day.empty else 0
        rows.append({"date": d, "revenue": s[d], "z": zv, "top": top, "share": share})
    return rows


def performance_table(df, by):
    """Revenue, share and rating for each product / region / category."""
    r = df.groupby(by)["revenue"].sum().sort_values(ascending=False)
    t = pd.DataFrame({"revenue": r})
    t["share"] = r / r.sum() * 100
    t["vs_avg"] = (r / r.mean() - 1) * 100
    t["rating"] = np.where(t["vs_avg"] >= 25, "Top performer",
                           np.where(t["vs_avg"] <= -25, "Needs attention", "On par"))
    return t


def report_text(df):
    """All automatic findings as one block of text (Insights tab and summary file)."""
    if df.empty:
        return "No data for the selected filters."
    out = ["SMART INSIGHTS", ""] + [f"*  {s}" for s in insights(df)]

    out += ["", "TREND DETECTION", ""]
    t = trend_detection(df)
    if t:
        label, pct = t
        out.append(f"*  Overall sales trend: {label} (about {pct:+.1f}% per 30 days).")
    else:
        out.append("*  Not enough data to detect a trend.")

    out += ["", "LOW DEMAND PRODUCTS", ""]
    low = low_demand_products(df)
    if low:
        out += [f"*  {p}: only {u} units ({pct:.0f}% of the average product). "
                f"Consider a discount or less stock." for p, u, pct in low]
    else:
        out.append("*  No product has unusually low demand.")

    out += ["", "DECLINE ALERTS (last 30 days vs previous 30)", ""]
    dec = declining_products(df)
    out += ([f"*  {p}: units down {d:.0f}%" for p, d in dec]
            if dec else ["*  No product is dropping sharply."])

    out += ["", "UNUSUAL SALES DAYS", ""]
    odd = unusual_days(df)
    if odd:
        out.append(f"*  {len(odd)} unusual day(s) found. Strongest:")
        for r in odd[:5]:
            kind = "unusually HIGH" if r["z"] > 0 else "unusually LOW"
            out.append(f"     {r['date']:%d %b %Y}: Rs {r['revenue']:,.0f} ({kind}), "
                       f"mostly {r['top']} ({r['share']:.0f}% of the day)")
    else:
        out.append("*  No unusual days detected.")

    out += ["", "PERFORMANCE ANALYSIS", ""]
    for by, name in [("product", "Products"), ("region", "Regions"), ("category", "Categories")]:
        t = performance_table(df, by)
        top = [f"{i} ({r.vs_avg:+.0f}%)" for i, r in t.iterrows() if r.rating == "Top performer"]
        bad = [f"{i} ({r.vs_avg:+.0f}%)" for i, r in t.iterrows() if r.rating == "Needs attention"]
        out.append(f"*  {name} - top: {', '.join(top) or 'none'}; "
                   f"needs attention: {', '.join(bad) or 'none'}")
    return "\n".join(out)


def section_summaries(df):
    """Short text for each analysis card on the main dashboard."""
    empty = "No data"
    if df.empty:
        return {"performance": empty, "trend": empty, "trend_label": None,
                "low": empty, "insights": empty, "unusual": empty}
    out = {}

    # performance
    pt = performance_table(df, "product")
    top = pt.index[0]
    bad = int((pt["rating"] == "Needs attention").sum())
    out["performance"] = (f"Top product: {top} ({pt.iloc[0]['vs_avg']:+.0f}% vs avg)\n"
                          f"Top region: {top_region(df)}\n"
                          f"{bad} product(s) need attention")

    # trend
    t = trend_detection(df)
    g = _growth(df)
    if t:
        arrow = {"Upward": "▲", "Downward": "▼", "Stable": "►"}[t[0]]
        txt = f"{arrow} {t[0]} ({t[1]:+.1f}% per 30 days)"
        if g is not None:
            txt += f"\nLast 30 days: {g:+.1f}%"
        out["trend"], out["trend_label"] = txt, t[0]
    else:
        out["trend"], out["trend_label"] = "Not enough data", None

    # low demand
    low = low_demand_products(df)
    out["low"] = ("\n".join(f"{p}: {u} units ({pct:.0f}% of avg)" for p, u, pct in low[:3])
                  if low else "No low-demand products")

    # insights (first three)
    out["insights"] = "\n".join(f"• {s}" for s in insights(df)[:3])

    # unusual days
    odd = unusual_days(df)
    if odd:
        r = odd[0]
        out["unusual"] = (f"{len(odd)} unusual day(s)\nStrongest: {r['date']:%d %b %Y}\n"
                          f"Rs {r['revenue']:,.0f}, mostly {r['top']}")
    else:
        out["unusual"] = "No unusual days"
    return out


def best_seller(df):
    """Product with the most units sold."""
    if df.empty:
        return "-"
    return df.groupby("product")["units"].sum().idxmax()


def top_region(df):
    if df.empty:
        return "-"
    return df.groupby("region")["revenue"].sum().idxmax()


def month_progress(df, target):
    """Latest month's revenue against a target. Returns (month, revenue, percent)."""
    if df.empty or target <= 0:
        return None, 0, 0
    latest = df["month"].max()
    rev = df[df["month"] == latest]["revenue"].sum()
    return latest, rev, rev / target * 100


def summary_text(df, shop):
    """Text report for the Summary report button."""
    k = kpis(df)
    head = [f"{shop} - Sales Summary", "=" * 40,
            f"Total revenue : Rs {k['revenue']:,.0f}",
            f"Orders        : {k['orders']:,}",
            f"Avg order     : Rs {k['aov']:,.0f}",
            f"Units sold    : {k['units']:,}",
            f"Best seller   : {best_seller(df)}",
            f"Top region    : {top_region(df)}", "", ""]
    return "\n".join(head) + report_text(df)


# ------------------------------------------------------------- charts
def _empty(fig, msg="No data for the selected filters"):
    fig.clear()
    fig.text(0.5, 0.5, msg, ha="center", va="center", fontsize=14, color="gray")


def draw_overview(fig, df):
    if df.empty:
        return _empty(fig)
    fig.clear()
    ax1, ax2, ax3, ax4 = fig.subplots(2, 2).flatten()

    m = df.groupby("month")["revenue"].sum()
    ax1.plot(m.index.astype(str), m.values, marker="o", color="#2a6f97")
    ax1.set_title("Monthly Revenue")
    ax1.yaxis.set_major_formatter(FuncFormatter(rupees))
    ax1.tick_params(axis="x", rotation=45, labelsize=8)
    ax1.grid(alpha=0.3)

    c = df.groupby("category")["revenue"].sum()
    ax2.pie(c.values, labels=c.index, autopct="%1.0f%%", startangle=90,
            pctdistance=0.8, wedgeprops={"width": 0.45})
    ax2.set_title("Revenue by Category")

    t = df.groupby("product")["revenue"].sum().sort_values().tail(5)
    ax3.barh(t.index, t.values, color="#52b788")
    ax3.xaxis.set_major_formatter(FuncFormatter(rupees))
    ax3.set_title("Top 5 Products")

    r = df.groupby("region")["units"].sum()
    ax4.bar(r.index, r.values, color="#e76f51")
    ax4.set_title("Units by Region")
    fig.tight_layout()


def draw_trend(fig, df):
    s = daily_series(df) if not df.empty else None
    if s is None or len(s) < 2:
        return _empty(fig, "Need more days of data")
    fig.clear()
    ax = fig.subplots(1, 1)
    ax.plot(s.index, s.values, color="#bbbbbb", linewidth=0.8, label="Daily revenue")
    ax.plot(s.index, s.rolling(7, min_periods=1).mean(), color="#2a6f97",
            linewidth=2, label="7-day average")
    f = forecast(df)
    if f:
        hist, fut = f
        ax.plot(fut.index, fut.values, color="#e76f51", linestyle="--",
                linewidth=2, label="30-day forecast")
        ax.axvspan(fut.index[0], fut.index[-1], color="#e76f51", alpha=0.08)
    ax.yaxis.set_major_formatter(FuncFormatter(rupees))
    verdict = trend_detection(df)
    suffix = f"  |  Trend: {verdict[0]} ({verdict[1]:+.1f}% per 30 days)" if verdict else ""
    ax.set_title("Revenue Trend and 30-Day Forecast" + suffix)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()


def draw_pareto(fig, df):
    if df.empty:
        return _empty(fig)
    fig.clear()
    ax = fig.subplots(1, 1)
    p, cum = pareto(df)
    ax.bar(p.index, p.values, color="#2a9d8f")
    ax.yaxis.set_major_formatter(FuncFormatter(rupees))
    ax.tick_params(axis="x", rotation=30)
    ax2 = ax.twinx()
    ax2.plot(p.index, cum.values, color="#e76f51", marker="o")
    ax2.axhline(80, color="gray", linestyle=":")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative % of revenue")
    ax.set_title("Pareto (80/20) Analysis: which products carry the shop?")
    fig.tight_layout()


def draw_heatmap(fig, df):
    if df.empty:
        return _empty(fig)
    fig.clear()
    ax = fig.subplots(1, 1)
    pv = (df.assign(dow=df["date"].dt.dayofweek)
            .pivot_table(index="dow", columns="month", values="revenue",
                         aggfunc="sum", fill_value=0)
            .reindex(range(7), fill_value=0))
    im = ax.imshow(pv.values, aspect="auto", cmap="YlOrRd")
    ax.set_yticks(range(7))
    ax.set_yticklabels(WEEKDAYS)
    ax.set_xticks(range(len(pv.columns)))
    ax.set_xticklabels([str(c) for c in pv.columns], rotation=45, fontsize=8)
    ax.set_title("When do customers buy? Revenue by weekday and month")
    cb = fig.colorbar(im, ax=ax)
    cb.formatter = FuncFormatter(rupees)
    cb.update_ticks()
    fig.tight_layout()


def draw_performance(fig, df):
    if df.empty:
        return _empty(fig)
    fig.clear()
    axes = fig.subplots(1, 3)
    colors = {"Top performer": "#2d9a4b", "On par": "#8d99ae", "Needs attention": "#cc3b3b"}
    for ax, by in zip(axes, ["product", "region", "category"]):
        t = performance_table(df, by).iloc[::-1]
        ax.barh(t.index, t["revenue"], color=[colors[r] for r in t["rating"]])
        ax.axvline(t["revenue"].mean(), color="black", linestyle="--", linewidth=1)
        ax.xaxis.set_major_formatter(FuncFormatter(rupees))
        ax.tick_params(axis="x", labelsize=8)
        ax.set_title(f"By {by} (dashed = average)", fontsize=10)
    fig.suptitle("Sales Performance: green = top performer, red = needs attention")
    fig.tight_layout()


def draw_unusual(fig, df):
    s = daily_series(df) if not df.empty else None
    if s is None or len(s) < 30:
        return _empty(fig, "Need at least 30 days of data")
    fig.clear()
    ax = fig.subplots(1, 1)
    ax.plot(s.index, s.values, color="#8d99ae", linewidth=0.9, label="Daily revenue")
    limit = s.mean() + 2.5 * s.std()
    ax.axhline(limit, color="#e76f51", linestyle="--", label="Unusual above this line")
    odd = unusual_days(df)
    if odd:
        ax.scatter([r["date"] for r in odd], [r["revenue"] for r in odd],
                   color="red", zorder=3, label=f"Unusual days ({len(odd)})")
        for r in odd[:3]:
            ax.annotate(f"{r['date']:%d %b}", (r["date"], r["revenue"]),
                        textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    ax.yaxis.set_major_formatter(FuncFormatter(rupees))
    ax.set_title("Unusual Sales Detection")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

def recommendations(df):
    """Create cautious, data-based actions. Sales data alone cannot reveal stock levels."""
    if df.empty:
        return ["Load sales data to generate recommendations."]
    items = []
    decline = declining_products(df)
    for product, drop in decline[:3]:
        items.append(f"Review {product}: units sold are down {drop:.0f}% against the previous 30-day period. Check price, promotion and customer feedback.")
    low = low_demand_products(df)
    for product, units, pct in low[:2]:
        items.append(f"Review demand for {product}: {units} units sold, around {pct:.0f}% of the average product volume. Consider a small promotion before changing purchasing levels.")
    region_sales = df.groupby("region")["revenue"].sum().sort_values(ascending=False)
    if len(region_sales) > 1:
        strongest, weakest = region_sales.index[0], region_sales.index[-1]
        gap = (1 - region_sales.iloc[-1] / region_sales.iloc[0]) * 100 if region_sales.iloc[0] else 0
        if gap >= 20:
            items.append(f"Compare {weakest} with {strongest}: revenue in {weakest} is {gap:.0f}% below the strongest region. Check local demand and product mix.")
    trend = trend_detection(df)
    if trend:
        label, pct = trend
        if label == "Downward":
            items.append(f"Overall sales trend is downward ({pct:.1f}% per 30 days by a linear trend). Review recent pricing, promotions and sales activity.")
        elif label == "Upward":
            items.append(f"Overall sales trend is upward (+{pct:.1f}% per 30 days by a linear trend). Check product availability before planning promotions.")
    odd = unusual_days(df)
    if odd:
        top = odd[0]
        direction = "higher" if top["z"] > 0 else "lower"
        items.append(f"Check {top['date']:%d %b %Y}: revenue was unusually {direction} than the dataset average. The largest product contribution was {top['top']}.")
    if not items:
        items.append("No major warning was found in the selected data. Continue tracking weekly sales and product mix.")
    items.append("Stock advice is limited because this dataset has no inventory or purchase records.")
    return items
