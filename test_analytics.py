"""Headless tests for Namma Mart analytics and chart functions."""
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure

import analytics as an


def main():
    df = an.load_data("sales_data.csv")
    assert not df.empty, "Sample sales data should not be empty"
    assert {"date", "product", "category", "region", "units", "unit_price", "revenue", "month"}.issubset(df.columns)
    print("KPIs:", an.kpis(df))
    print("Insights:")
    for item in an.insights(df):
        print("-", item)
    print("Recommendations:")
    for item in an.recommendations(df):
        print("-", item)
    print("Declining products:", an.declining_products(df))

    chart_functions = [an.draw_overview, an.draw_trend, an.draw_performance,
                       an.draw_unusual, an.draw_pareto, an.draw_heatmap]
    for fn in chart_functions:
        fig = Figure(figsize=(9, 5))
        fn(fig, df)
        assert len(fig.axes) > 0, f"{fn.__name__} did not create a chart"
        print("Chart OK:", fn.__name__)

    filtered = an.apply_filters(df, region="North", category="Grocery")
    assert ((filtered["region"] == "North") & (filtered["category"] == "Grocery")).all()
    print("Filtered rows:", len(filtered))

    # Optional profit/customer fields remain optional for legacy CSV files.
    assert an.profit_metrics(df) is None
    assert an.customer_metrics(df) is None
    assert an.compare_periods(df) is not None
    sample_row = df.iloc[[0]].drop(columns=["revenue", "cost", "profit", "month"])
    assert len(an.find_duplicate_sales(df, sample_row)) >= 1

    # Supplied cost and customer ID fields unlock the additional analysis.
    enriched = df.head(5).copy()
    enriched["unit_cost"] = enriched["unit_price"] * 0.6
    enriched["customer_id"] = ["C001", "C001", "C002", "C003", "C003"]
    enriched["cost"] = enriched["units"] * enriched["unit_cost"]
    enriched["profit"] = enriched["revenue"] - enriched["cost"]
    assert an.profit_metrics(enriched)["profit"] > 0
    assert an.customer_metrics(enriched)["repeat"] == 2
    print("Profit, customer, duplicate and period comparison checks OK")

    empty = an.apply_filters(df, region="RegionThatDoesNotExist")
    assert empty.empty
    assert an.kpis(empty)["revenue"] == 0
    assert an.insights(empty) == ["No data for the selected filters."]
    fig = Figure()
    an.draw_overview(fig, empty)
    print("Empty-data handling OK")
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
