"""Sample-data generator and standalone Matplotlib dashboard for Namma Mart."""
import os
import random
from datetime import date, timedelta

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

CSV_FILE = "sales_data.csv"
OUT_FILE = "dashboard.png"
SHOP_NAME = "Namma Mart"


def generate_sample_csv(path, days=365, seed=42):
    """Create a reproducible sample dataset when no sales CSV exists."""
    random.seed(seed)
    products = {
        "Laptop": ("Electronics", 55000), "Headphones": ("Electronics", 2500),
        "T-Shirt": ("Clothing", 600), "Jeans": ("Clothing", 1800),
        "Rice (5kg)": ("Grocery", 450), "Olive Oil": ("Grocery", 700),
        "Desk Lamp": ("Home", 1200), "Cushion": ("Home", 400),
    }
    regions = ["North", "South", "East", "West"]
    start = date.today() - timedelta(days=days - 1)
    rows = ["date,product,category,region,units,unit_price"]
    for offset in range(days):
        day = start + timedelta(days=offset)
        for _ in range(random.randint(3, 8)):
            name = random.choices(list(products), weights=[1, 6, 10, 7, 12, 8, 6, 9])[0]
            category, price = products[name]
            units = random.randint(1, 5) + (2 if day.month >= 10 else 0)
            rows.append(f"{day},{name},{category},{random.choice(regions)},{units},{price}")
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write("\n".join(rows) + "\n")
    print(f"Sample data written to {path}")


def load_data(path):
    return pd.read_csv(path, parse_dates=["date"])


def rupees(value, _position=None):
    if abs(value) >= 1e7:
        return f"₹{value / 1e7:.1f}Cr"
    if abs(value) >= 1e5:
        return f"₹{value / 1e5:.1f}L"
    if abs(value) >= 1e3:
        return f"₹{value / 1e3:.0f}K"
    return f"₹{value:.0f}"


def build_dashboard(df):
    df = df.copy()
    df["revenue"] = df["units"] * df["unit_price"]
    df["month"] = df["date"].dt.to_period("M")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"{SHOP_NAME}: Sales Dashboard", fontsize=18, fontweight="bold")
    monthly = df.groupby("month")["revenue"].sum()
    axes[0, 0].plot(monthly.index.astype(str), monthly.values, marker="o", color="#2a6f97")
    axes[0, 0].set_title("Monthly Revenue")
    axes[0, 0].yaxis.set_major_formatter(FuncFormatter(rupees))
    axes[0, 0].tick_params(axis="x", rotation=45)
    axes[0, 0].grid(alpha=0.25)
    category = df.groupby("category")["revenue"].sum()
    axes[0, 1].pie(category.values, labels=category.index, autopct="%1.1f%%", startangle=90,
                   wedgeprops={"width": 0.45})
    axes[0, 1].set_title("Revenue Share by Category")
    top = df.groupby("product")["revenue"].sum().nlargest(5).sort_values()
    axes[1, 0].barh(top.index, top.values, color="#52b788")
    axes[1, 0].set_title("Top 5 Products by Revenue")
    axes[1, 0].xaxis.set_major_formatter(FuncFormatter(rupees))
    region = df.groupby("region")["units"].sum()
    axes[1, 1].bar(region.index, region.values, color="#e76f51")
    axes[1, 1].set_title("Units Sold by Region")
    axes[1, 1].set_ylabel("Units")
    footer = (f"Total Revenue: ₹{df['revenue'].sum():,.0f}   |   Orders: {len(df):,}   |   "
              f"Avg Order Value: ₹{df['revenue'].mean():,.0f}")
    fig.text(0.5, 0.01, footer, ha="center", fontsize=11)
    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    fig.savefig(OUT_FILE, dpi=160, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    if not os.path.exists(CSV_FILE):
        generate_sample_csv(CSV_FILE)
    build_dashboard(load_data(CSV_FILE))
