"""Namma Mart Smart Sales Dashboard. Run: python namma_mart_app.py"""
import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import analytics as an

SHOP_NAME = "Namma Mart"
CSV_FILE = "sales_data.csv"
ALL = "All"
COLORS = {
    "navy": "#14213D", "blue": "#2563EB", "teal": "#0F766E",
    "bg": "#F3F6FB", "card": "#FFFFFF", "text": "#172033",
    "muted": "#64748B", "line": "#E2E8F0", "green": "#15803D",
    "red": "#B91C1C", "amber": "#B45309",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{SHOP_NAME} | Smart Sales Intelligence")
        self.geometry("1450x940")
        self.minsize(1120, 760)
        self.configure(bg=COLORS["bg"])
        self._style_widgets()

        self.csv_path = CSV_FILE
        if not os.path.exists(self.csv_path):
            an.generate_sample_csv(self.csv_path)
        self.df = an.load_data(self.csv_path)
        self.view = self.df.copy()
        self._build_header()
        self._build_filter_bar()
        self._build_kpis()
        self._build_target()
        self._build_highlights()
        self._build_tabs()
        self._refresh_choices()
        self.apply_filters()

    # ------------------------------------------------------------ styling
    def _style_widgets(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["card"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"],
                         font=("Segoe UI", 9))
        style.configure("Muted.TLabel", foreground=COLORS["muted"])
        style.configure("Title.TLabel", background=COLORS["navy"], foreground="white",
                         font=("Segoe UI", 21, "bold"))
        style.configure("Subtitle.TLabel", background=COLORS["navy"], foreground="#CBD5E1",
                         font=("Segoe UI", 9))
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(10, 6))
        style.configure("Accent.TButton", background=COLORS["blue"], foreground="white")
        style.map("Accent.TButton", background=[("active", "#1D4ED8")])
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=5)
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(15, 9), font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#FFFFFF")],
                  foreground=[("selected", COLORS["blue"])])
        style.configure("Treeview", rowheight=29, font=("Segoe UI", 9),
                         background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=7)
        style.configure("Horizontal.TProgressbar", troughcolor="#E2E8F0",
                         background=COLORS["teal"], thickness=12)

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS["navy"], padx=24, pady=17)
        header.pack(fill="x")
        left = tk.Frame(header, bg=COLORS["navy"])
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="NAMMA MART", bg=COLORS["navy"], fg="white",
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(left, text="RETAIL SALES INTELLIGENCE  •  PERFORMANCE  •  FORECASTS",
                 bg=COLORS["navy"], fg="#CBD5E1", font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))
        self.header_status = tk.Label(header, text="●  DATA READY", bg=COLORS["navy"],
                                      fg="#86EFAC", font=("Segoe UI", 9, "bold"))
        self.header_status.pack(side="right", padx=8)

    def _build_filter_bar(self):
        wrap = tk.Frame(self, bg=COLORS["card"], padx=15, pady=11,
                        highlightbackground=COLORS["line"], highlightthickness=1)
        wrap.pack(fill="x", padx=18, pady=(14, 8))
        tk.Label(wrap, text="FILTER DATA", bg="white", fg=COLORS["muted"],
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 12))
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        self.region_var = tk.StringVar(value=ALL)
        self.cat_var = tk.StringVar(value=ALL)
        self._filter_field(wrap, "From", self.start_var, width=12)
        self._filter_field(wrap, "To", self.end_var, width=12)
        tk.Label(wrap, text="Region", bg="white", fg=COLORS["muted"]).pack(side="left", padx=(8, 4))
        self.region_cb = ttk.Combobox(wrap, textvariable=self.region_var, width=11,
                                       state="readonly")
        self.region_cb.pack(side="left", padx=(0, 8))
        tk.Label(wrap, text="Category", bg="white", fg=COLORS["muted"]).pack(side="left", padx=(4, 4))
        self.cat_cb = ttk.Combobox(wrap, textvariable=self.cat_var, width=13,
                                   state="readonly")
        self.cat_cb.pack(side="left", padx=(0, 8))
        ttk.Button(wrap, text="Apply filters", style="Accent.TButton",
                   command=self.apply_filters).pack(side="left", padx=3)
        ttk.Button(wrap, text="Reset", command=self.reset_filters).pack(side="left", padx=3)
        ttk.Button(wrap, text="Load CSV", command=self.load_csv).pack(side="right", padx=3)

    def _filter_field(self, parent, label, variable, width=12):
        tk.Label(parent, text=label, bg="white", fg=COLORS["muted"]).pack(side="left", padx=(5, 4))
        ttk.Entry(parent, textvariable=variable, width=width).pack(side="left", padx=(0, 7))

    def _build_kpis(self):
        heading = tk.Frame(self, bg=COLORS["bg"])
        heading.pack(fill="x", padx=20, pady=(4, 5))
        tk.Label(heading, text="Business overview", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        self.period_label = tk.Label(heading, text="All available dates", bg=COLORS["bg"],
                                     fg=COLORS["muted"], font=("Segoe UI", 9))
        self.period_label.pack(side="right")
        row = tk.Frame(self, bg=COLORS["bg"])
        row.pack(fill="x", padx=16)
        specs = [("revenue", "TOTAL REVENUE", "₹0", COLORS["blue"]),
                 ("orders", "SALES RECORDS", "0", COLORS["teal"]),
                 ("aov", "AVG. ORDER VALUE", "₹0", "#7C3AED"),
                 ("units", "UNITS SOLD", "0", "#D97706"),
                 ("growth", "30-DAY GROWTH", "n/a", COLORS["green"]),
                 ("best", "BEST SELLER", "-", "#DB2777"),
                 ("region", "TOP REGION", "-", "#475569")]
        self.kpi_vars = {}
        for key, title, initial, accent in specs:
            card = tk.Frame(row, bg="white", padx=13, pady=11,
                            highlightbackground=COLORS["line"], highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=4, pady=3)
            tk.Frame(card, bg=accent, height=3).pack(fill="x", pady=(0, 8))
            tk.Label(card, text=title, bg="white", fg=COLORS["muted"],
                     font=("Segoe UI", 7, "bold")).pack(anchor="w")
            value = tk.StringVar(value=initial)
            label = tk.Label(card, textvariable=value, bg="white", fg=COLORS["text"],
                             font=("Segoe UI", 14, "bold"), anchor="w")
            label.pack(anchor="w", pady=(4, 0))
            self.kpi_vars[key] = (value, label)

    def _build_target(self):
        wrap = tk.Frame(self, bg="white", padx=14, pady=9,
                        highlightbackground=COLORS["line"], highlightthickness=1)
        wrap.pack(fill="x", padx=20, pady=(8, 9))
        tk.Label(wrap, text="MONTHLY SALES TARGET", bg="white", fg=COLORS["muted"],
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 9))
        self.target_var = tk.StringVar(value="1000000")
        ttk.Entry(wrap, textvariable=self.target_var, width=13).pack(side="left")
        ttk.Button(wrap, text="Update", command=self.update_target).pack(side="left", padx=6)
        self.target_bar = ttk.Progressbar(wrap, length=260, maximum=100)
        self.target_bar.pack(side="left", padx=(15, 9))
        self.target_label = tk.Label(wrap, text="", bg="white", fg=COLORS["text"],
                                     font=("Segoe UI", 9, "bold"))
        self.target_label.pack(side="left")
        ttk.Button(wrap, text="Export PDF", command=self.export_pdf).pack(side="right", padx=3)
        ttk.Button(wrap, text="Export chart", command=self.export_chart).pack(side="right", padx=3)
        ttk.Button(wrap, text="Export summary", command=self.export_summary).pack(side="right", padx=3)
        ttk.Button(wrap, text="Export filtered CSV", command=self.export_data).pack(side="right", padx=3)

    def _build_highlights(self):
        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x", padx=17, pady=(0, 8))
        tk.Label(bar, text="QUICK INSIGHTS", bg=COLORS["bg"], fg=COLORS["muted"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=3, pady=(0, 5))
        self.highlight_vars = {}
        for key, title in [("trend", "SALES TREND"), ("top", "TOP PRODUCT"),
                           ("decline", "DECLINE ALERTS"), ("unusual", "UNUSUAL DAYS")]:
            card = tk.Frame(bar, bg="white", padx=11, pady=8,
                            highlightbackground=COLORS["line"], highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=3)
            tk.Label(card, text=title, bg="white", fg=COLORS["muted"],
                     font=("Segoe UI", 7, "bold")).pack(anchor="w")
            var = tk.StringVar(value="Loading...")
            tk.Label(card, textvariable=var, bg="white", fg=COLORS["text"],
                     font=("Segoe UI", 9, "bold"), justify="left", wraplength=260,
                     height=2, anchor="w").pack(anchor="w", pady=(4, 0))
            self.highlight_vars[key] = var

    def _build_tabs(self):
        outer = tk.Frame(self, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True, padx=17, pady=(0, 14))
        self.nb = ttk.Notebook(outer)
        self.nb.pack(fill="both", expand=True)
        self.charts = {}
        chart_specs = [
            ("Overview", an.draw_overview, (10, 6)),
            ("Trend & Forecast", an.draw_trend, (10, 5)),
            ("Performance", an.draw_performance, (12, 5)),
            ("Unusual Sales", an.draw_unusual, (10, 5)),
            ("Pareto 80/20", an.draw_pareto, (10, 5)),
            ("Weekday Heatmap", an.draw_heatmap, (10, 5)),
        ]
        for name, draw_fn, size in chart_specs:
            frame = ttk.Frame(self.nb, padding=8)
            self.nb.add(frame, text=name)
            fig = Figure(figsize=size, dpi=100, facecolor="white")
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)
            self.charts[name] = (fig, canvas, draw_fn)

        self._build_insights_tab()
        self._build_business_analysis_tab()
        self._build_records_tab()
        self._build_add_sale_tab()

    def _build_insights_tab(self):
        frame = ttk.Frame(self.nb, padding=15)
        self.nb.add(frame, text="Smart Insights & Actions")
        top = tk.Frame(frame, bg="white", padx=15, pady=12,
                       highlightbackground=COLORS["line"], highlightthickness=1)
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="WHAT THE DATA SAYS", bg="white", fg=COLORS["blue"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.insight_text = tk.Text(top, wrap="word", font=("Segoe UI", 10), height=9,
                                    relief="flat", bg="white", fg=COLORS["text"],
                                    padx=4, pady=7, spacing3=5)
        self.insight_text.pack(fill="x")
        bottom = tk.Frame(frame, bg="white", padx=15, pady=12,
                          highlightbackground=COLORS["line"], highlightthickness=1)
        bottom.pack(fill="both", expand=True)
        tk.Label(bottom, text="RECOMMENDED ACTIONS", bg="white", fg=COLORS["teal"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.recommendation_text = tk.Text(bottom, wrap="word", font=("Segoe UI", 10),
                                           relief="flat", bg="white", fg=COLORS["text"],
                                           padx=4, pady=7, spacing3=7)
        self.recommendation_text.pack(fill="both", expand=True)

    def _build_business_analysis_tab(self):
        frame = ttk.Frame(self.nb, padding=16)
        self.nb.add(frame, text="Business Analysis")
        tk.Label(frame, text="PROFIT, CUSTOMER & PERIOD ANALYSIS", bg=COLORS["bg"],
                 fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))
        self.business_text = tk.Text(frame, wrap="word", font=("Segoe UI", 10), height=22,
                                     relief="flat", bg="white", fg=COLORS["text"],
                                     padx=16, pady=14)
        self.business_text.pack(fill="both", expand=True)
        self._set_text(self.business_text, "Add unit cost and customer ID values when recording sales to unlock these analyses.")

    def _build_records_tab(self):
        frame = ttk.Frame(self.nb, padding=12)
        self.nb.add(frame, text="Sales Records")
        toolbar = tk.Frame(frame, bg=COLORS["bg"])
        toolbar.pack(fill="x", pady=(0, 9))
        tk.Label(toolbar, text="Search product, category or region", bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.fill_table())
        ttk.Entry(toolbar, textvariable=self.search_var, width=28).pack(side="left", padx=8)
        self.record_count = tk.Label(toolbar, text="", bg=COLORS["bg"], fg=COLORS["muted"])
        self.record_count.pack(side="right")
        columns = ("date", "product", "category", "region", "units", "unit_price", "revenue")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        headings = {"date": "Date", "product": "Product", "category": "Category",
                    "region": "Region", "units": "Units", "unit_price": "Unit Price (₹)",
                    "revenue": "Revenue (₹)"}
        widths = {"date": 120, "product": 180, "category": 140, "region": 110,
                  "units": 80, "unit_price": 130, "revenue": 140}
        for col in columns:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self.sort_table(c))
            self.tree.column(col, width=widths[col], anchor="center")
        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.pack(side="top", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.sort_col, self.sort_desc = "date", True

    def _build_add_sale_tab(self):
        frame = ttk.Frame(self.nb, padding=25)
        self.nb.add(frame, text="Add a Sale")
        card = tk.Frame(frame, bg="white", padx=25, pady=22,
                        highlightbackground=COLORS["line"], highlightthickness=1)
        card.pack(anchor="nw", padx=10, pady=10)
        tk.Label(card, text="Record a new transaction", bg="white", fg=COLORS["text"],
                 font=("Segoe UI", 15, "bold")).grid(row=0, column=0, columnspan=2,
                                                      sticky="w", pady=(0, 15))
        self.sale = {key: tk.StringVar() for key in
                     ("date", "product", "category", "region", "units", "price", "cost", "customer")}
        self.sale["date"].set(str(date.today()))
        self.sale["units"].set("1")
        fields = [("Date (YYYY-MM-DD)", "date", "entry"), ("Product", "product", "combo"),
                  ("Category", "category", "combo"), ("Region", "region", "combo"),
                  ("Units sold", "units", "entry"), ("Unit price (₹)", "price", "entry"),
                  ("Unit cost (₹, optional)", "cost", "entry"),
                  ("Customer ID (optional)", "customer", "entry")]
        self.sale_widgets = {}
        for row, (label, key, kind) in enumerate(fields, start=1):
            tk.Label(card, text=label, bg="white", fg=COLORS["muted"],
                     font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky="w", pady=7)
            widget = (ttk.Combobox(card, textvariable=self.sale[key], width=30)
                      if kind == "combo" else ttk.Entry(card, textvariable=self.sale[key], width=33))
            widget.grid(row=row, column=1, sticky="w", padx=(22, 0), pady=7)
            self.sale_widgets[key] = widget
        self.sale_widgets["product"].bind("<<ComboboxSelected>>", self._autofill_product)
        ttk.Button(card, text="Save sale", style="Accent.TButton", command=self.save_sale).grid(
            row=len(fields) + 1, column=1, sticky="w", pady=(17, 5))
        tk.Label(card, text="Unit cost enables profit analysis. Customer ID enables repeat-customer analysis. Both are optional.",
                 bg="white", fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=460).grid(
                     row=len(fields) + 2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    # ------------------------------------------------------------ helpers
    def _refresh_choices(self):
        self.region_cb["values"] = [ALL] + sorted(self.df["region"].dropna().unique().tolist())
        self.cat_cb["values"] = [ALL] + sorted(self.df["category"].dropna().unique().tolist())
        if not hasattr(self, "sale_widgets"):
            return
        self.sale_widgets["product"]["values"] = sorted(self.df["product"].dropna().unique().tolist())
        self.sale_widgets["category"]["values"] = sorted(self.df["category"].dropna().unique().tolist())
        self.sale_widgets["region"]["values"] = sorted(self.df["region"].dropna().unique().tolist())

    def _parse_date(self, value):
        value = value.strip()
        return pd.to_datetime(value, format="%Y-%m-%d") if value else None

    def _autofill_product(self, _event=None):
        product = self.sale["product"].get().strip()
        rows = self.df[self.df["product"] == product]
        if not rows.empty:
            latest = rows.sort_values("date").iloc[-1]
            self.sale["category"].set(str(latest["category"]))
            self.sale["price"].set(str(latest["unit_price"]))

    # ------------------------------------------------------------ filters
    def apply_filters(self):
        try:
            start = self._parse_date(self.start_var.get())
            end = self._parse_date(self.end_var.get())
            if start is not None and end is not None and start > end:
                raise ValueError("The start date must be before the end date.")
        except ValueError as error:
            messagebox.showerror("Invalid date range", str(error) or "Use YYYY-MM-DD.")
            return
        self.view = an.apply_filters(self.df, start, end,
                                     self.region_var.get(), self.cat_var.get()).copy()
        self.refresh_dashboard()

    def reset_filters(self):
        self.start_var.set("")
        self.end_var.set("")
        self.region_var.set(ALL)
        self.cat_var.set(ALL)
        self.apply_filters()

    def refresh_dashboard(self):
        kpi = an.kpis(self.view)
        self.kpi_vars["revenue"][0].set(f"₹{kpi['revenue']:,.0f}")
        self.kpi_vars["orders"][0].set(f"{kpi['orders']:,}")
        self.kpi_vars["aov"][0].set(f"₹{kpi['aov']:,.0f}")
        self.kpi_vars["units"][0].set(f"{kpi['units']:,}")
        growth, growth_label = self.kpi_vars["growth"]
        if kpi["growth"] is None:
            growth.set("n/a")
            growth_label.config(fg=COLORS["muted"])
        else:
            growth.set(f"{'▲' if kpi['growth'] >= 0 else '▼'} {abs(kpi['growth']):.1f}%")
            growth_label.config(fg=COLORS["green"] if kpi["growth"] >= 0 else COLORS["red"])
        self.kpi_vars["best"][0].set(an.best_seller(self.view))
        self.kpi_vars["region"][0].set(an.top_region(self.view))
        if not self.view.empty:
            self.period_label.config(text=f"{self.view['date'].min():%d %b %Y} to {self.view['date'].max():%d %b %Y}")
        else:
            self.period_label.config(text="No records match these filters")
        self.update_target()
        self.update_highlights()
        self.fill_table()
        for fig, canvas, draw_fn in self.charts.values():
            draw_fn(fig, self.view)
            canvas.draw_idle()
        self._set_text(self.insight_text, an.report_text(self.view))
        actions = an.recommendations(self.view)
        action_text = "\n\n".join(f"{i + 1}.  {item}" for i, item in enumerate(actions))
        self._set_text(self.recommendation_text, action_text)
        self.refresh_business_analysis()

    def refresh_business_analysis(self):
        lines = ["PROFIT ANALYSIS", ""]
        profit = an.profit_metrics(self.view)
        if profit:
            lines += [f"Revenue with cost data: ₹{profit['revenue']:,.2f}",
                      f"Cost of goods sold: ₹{profit['cost']:,.2f}",
                      f"Gross profit: ₹{profit['profit']:,.2f}",
                      f"Gross profit margin: {profit['margin']:.1f}%",
                      f"Records containing cost data: {profit['records']:,}"]
        else:
            lines.append("Not available yet. Enter a unit cost for sales to calculate gross profit and margin.")
        lines += ["", "CUSTOMER ANALYSIS", ""]
        customers = an.customer_metrics(self.view)
        if customers:
            lines += [f"Identified customers: {customers['customers']:,}",
                      f"Repeat customers: {customers['repeat']:,}",
                      f"Top customer ID: {customers['top_customer']}",
                      f"Top customer's revenue: ₹{customers['top_revenue']:,.2f}"]
        else:
            lines.append("Not available yet. Enter customer IDs when recording sales.")
        lines += ["", "MONTH-TO-DATE COMPARISON", ""]
        comparison = an.compare_periods(self.view)
        if comparison:
            lines += [f"Current month ({comparison['current_start']:%d %b} to {comparison['current_end']:%d %b}): ₹{comparison['current']:,.2f}",
                      f"Previous month, same days ({comparison['previous_start']:%d %b} to {comparison['previous_end']:%d %b}): ₹{comparison['previous']:,.2f}"]
            if comparison["change"] is None:
                lines.append("Percentage change unavailable because the previous period had no sales.")
            else:
                lines.append(f"Revenue change: {comparison['change']:+.1f}%")
        else:
            lines.append("No data available for comparison.")
        lines += ["", "Note: Profit and customer results use only rows with the relevant information. The sample data does not contain real costs or customer IDs."]
        self._set_text(self.business_text, "\n".join(lines))

    @staticmethod
    def _set_text(widget, value):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.config(state="disabled")

    def update_highlights(self):
        if self.view.empty:
            for var in self.highlight_vars.values():
                var.set("No data for selected filters")
            return
        trend = an.trend_detection(self.view)
        self.highlight_vars["trend"].set(
            f"{trend[0]} ({trend[1]:+.1f}% / 30 days)" if trend else "Not enough history")
        product = an.best_seller(self.view)
        self.highlight_vars["top"].set(product)
        declines = an.declining_products(self.view)
        self.highlight_vars["decline"].set(
            f"{len(declines)} product(s) falling" if declines else "No sharp product decline")
        unusual = an.unusual_days(self.view)
        self.highlight_vars["unusual"].set(
            f"{len(unusual)} unusual day(s) flagged" if unusual else "No unusual days detected")

    def update_target(self):
        try:
            target = float(self.target_var.get().replace(",", "").strip())
            if target <= 0:
                raise ValueError
        except ValueError:
            self.target_label.config(text="Enter a positive target")
            self.target_bar["value"] = 0
            return
        month, revenue, percent = an.month_progress(self.view, target)
        if month is None:
            self.target_label.config(text="No sales data")
            self.target_bar["value"] = 0
            return
        self.target_bar["value"] = min(percent, 100)
        self.target_label.config(text=f"{month}: ₹{revenue:,.0f} / ₹{target:,.0f}  ({percent:.1f}%)")

    # ------------------------------------------------------------ records
    def sort_table(self, column):
        self.sort_desc = not self.sort_desc if self.sort_col == column else False
        self.sort_col = column
        self.fill_table()

    def fill_table(self):
        if not hasattr(self, "tree"):
            return
        data = self.view
        query = self.search_var.get().strip().lower()
        if query:
            mask = False
            for column in ("product", "category", "region"):
                mask = mask | data[column].astype(str).str.lower().str.contains(query, regex=False)
            data = data[mask]
        data = data.sort_values(self.sort_col, ascending=not self.sort_desc)
        self.tree.delete(*self.tree.get_children())
        for _, row in data.head(2000).iterrows():
            self.tree.insert("", "end", values=(
                row["date"].strftime("%Y-%m-%d"), row["product"], row["category"],
                row["region"], int(row["units"]), f"{row['unit_price']:,.2f}",
                f"{row['revenue']:,.2f}"))
        self.record_count.config(text=f"Showing {min(len(data), 2000):,} of {len(data):,} records")

    # ------------------------------------------------------------ file actions
    def load_csv(self):
        path = filedialog.askopenfilename(title="Select sales CSV",
                                          filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        if not messagebox.askyesno("Switch sales file", "Load this CSV as the active dashboard dataset? Your current CSV file will not be overwritten."):
            return
        try:
            loaded = an.load_data(path)
            required = {"date", "product", "category", "region", "units", "unit_price"}
            missing = required - set(loaded.columns)
            if missing:
                raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
            if loaded.empty:
                raise ValueError("The selected CSV has no valid sales rows.")
        except Exception as error:
            messagebox.showerror("Could not load CSV", str(error))
            return
        self.csv_path, self.df = path, loaded
        self._refresh_choices()
        self.reset_filters()
        self.header_status.config(text=f"●  {os.path.basename(path)}", fg="#86EFAC")

    def export_data(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile="namma_mart_filtered_sales.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if path:
            self.view.drop(columns=["month"], errors="ignore").to_csv(path, index=False)
            messagebox.showinfo("Export complete", f"Saved {len(self.view):,} records to:\n{path}")

    def export_summary(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            initialfile="namma_mart_sales_summary.txt",
                                            filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as file:
                file.write(an.summary_text(self.view, SHOP_NAME))
                file.write("\n\nRECOMMENDED ACTIONS\n\n")
                file.write("\n".join(f"- {x}" for x in an.recommendations(self.view)))
            messagebox.showinfo("Export complete", f"Summary saved to:\n{path}")

    def export_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            initialfile="namma_mart_sales_report.pdf",
                                            filetypes=[("PDF report", "*.pdf")])
        if not path:
            return
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                                    topMargin=16*mm, bottomMargin=16*mm)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name="SmallBody", parent=styles["BodyText"], leading=14, spaceAfter=5))
            k = an.kpis(self.view)
            story = [Paragraph("NAMMA MART", styles["Title"]),
                     Paragraph("Smart Sales Dashboard Report", styles["Heading2"]),
                     Paragraph(f"Generated on {date.today():%d %B %Y}", styles["SmallBody"]), Spacer(1, 8)]
            rows = [["Metric", "Value"], ["Total revenue", f"Rs {k['revenue']:,.2f}"],
                    ["Sales records", f"{k['orders']:,}"], ["Average record value", f"Rs {k['aov']:,.2f}"],
                    ["Units sold", f"{k['units']:,}"], ["Best seller", an.best_seller(self.view)],
                    ["Top region", an.top_region(self.view)]]
            t = Table(rows, colWidths=[75*mm, 85*mm])
            t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#14213D")),
                                   ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                                   ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#CBD5E1")),
                                   ("PADDING", (0,0), (-1,-1), 7)]))
            story += [t, Spacer(1, 12), Paragraph("Business analysis", styles["Heading2"])]
            pr = an.profit_metrics(self.view)
            cm = an.customer_metrics(self.view)
            cp = an.compare_periods(self.view)
            extra = []
            if pr:
                extra += [f"Gross profit: Rs {pr['profit']:,.2f}", f"Gross margin: {pr['margin']:.1f}%"]
            else:
                extra.append("Profit analysis unavailable: unit cost data has not been supplied.")
            if cm:
                extra += [f"Identified customers: {cm['customers']}", f"Repeat customers: {cm['repeat']}",
                          f"Top customer ID: {cm['top_customer']}"]
            else:
                extra.append("Customer analysis unavailable: customer IDs have not been supplied.")
            if cp and cp["change"] is not None:
                extra.append(f"Month-to-date revenue change vs same days of previous month: {cp['change']:+.1f}%")
            elif cp:
                extra.append("Period comparison: previous period had no sales, so percentage change is unavailable.")
            for item in extra:
                story.append(Paragraph(item, styles["SmallBody"]))
            story += [Spacer(1, 8), Paragraph("Smart insights", styles["Heading2"])]
            for item in an.insights(self.view):
                story.append(Paragraph("• " + item, styles["SmallBody"]))
            story += [Spacer(1, 6), Paragraph("Recommended actions", styles["Heading2"])]
            for item in an.recommendations(self.view):
                story.append(Paragraph("• " + item, styles["SmallBody"]))
            story += [Spacer(1, 8), Paragraph("Forecasts and unusual-day flags are analytical estimates, not guarantees or proof of fraud.", styles["Italic"])]
            doc.build(story)
            messagebox.showinfo("PDF exported", f"Report saved to:\n{path}")
        except Exception as error:
            messagebox.showerror("PDF export failed", str(error))

    def export_chart(self):
        selected = self.nb.tab(self.nb.select(), "text")
        if selected not in self.charts:
            messagebox.showinfo("Export chart", "Select one of the chart tabs first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            initialfile="namma_mart_chart.png",
                                            filetypes=[("PNG image", "*.png")])
        if path:
            self.charts[selected][0].savefig(path, dpi=180, bbox_inches="tight",
                                              facecolor="white")
            messagebox.showinfo("Export complete", f"Chart saved to:\n{path}")

    # ------------------------------------------------------------ add sale
    def save_sale(self):
        try:
            sale_date = pd.to_datetime(self.sale["date"].get().strip(), format="%Y-%m-%d")
            units = int(self.sale["units"].get())
            price = float(self.sale["price"].get().replace(",", "").strip())
            cost_text = self.sale["cost"].get().replace(",", "").strip()
            cost = float(cost_text) if cost_text else float("nan")
            product = self.sale["product"].get().strip()
            category = self.sale["category"].get().strip()
            region = self.sale["region"].get().strip()
            customer = self.sale["customer"].get().strip()
            if not product or not category or not region:
                raise ValueError("Product, category and region are required.")
            if units <= 0 or price <= 0 or (not pd.isna(cost) and cost < 0):
                raise ValueError("Units and selling price must be positive. Unit cost cannot be negative.")
            if not pd.isna(cost) and cost > price:
                if not messagebox.askyesno("Check unit cost", "Unit cost is higher than selling price. Save anyway?"):
                    return
        except (ValueError, TypeError) as error:
            messagebox.showerror("Check sale details", str(error) or
                                 "Use YYYY-MM-DD for date and valid positive numbers.")
            return
        new_row = pd.DataFrame([{
            "date": sale_date, "product": product, "category": category,
            "region": region, "units": units, "unit_price": price,
            "unit_cost": cost, "customer_id": customer,
        }])
        duplicates = an.find_duplicate_sales(self.df, new_row)
        if not duplicates.empty:
            if not messagebox.askyesno("Possible duplicate sale",
                    f"A sale with the same date, product, category, region, units and price already exists ({len(duplicates)} match(es)). Save this record anyway?"):
                return
        try:
            source = self.df.drop(columns=["revenue", "cost", "profit", "month"], errors="ignore").copy()
            # Keep a one-time backup before updating the original CSV.
            backup = self.csv_path + ".bak"
            if os.path.exists(self.csv_path) and not os.path.exists(backup):
                import shutil
                shutil.copy2(self.csv_path, backup)
            combined = pd.concat([source, new_row], ignore_index=True)
            temp_path = self.csv_path + ".tmp"
            combined.to_csv(temp_path, index=False)
            os.replace(temp_path, self.csv_path)
            self.df = an.load_data(self.csv_path)
        except Exception as error:
            messagebox.showerror("Could not save sale", str(error))
            return
        self._refresh_choices()
        self.reset_filters()
        messagebox.showinfo("Sale saved", f"Added {units} × {product} to the sales records.\nA backup is kept at {os.path.basename(self.csv_path)}.bak")



if __name__ == "__main__":
    App().mainloop()
