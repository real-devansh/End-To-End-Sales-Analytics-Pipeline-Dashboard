"""
=============================================================================
  PDF CORPORATE REPORT GENERATOR
  --------------------------------
  Produces a structured, multi-page A4 PDF from the analytical results
  dictionary returned by run_all_queries_pandas() or run_all_queries().

  Usage:
      from pdf_generator import generate_pdf_report
      pdf_bytes = generate_pdf_report(results)   # returns bytes

  Dependencies:
      fpdf2 >= 2.7.0   →  pip install fpdf2
=============================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
from fpdf import FPDF, XPos, YPos


# ═══════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  (matches the Streamlit dashboard's visual language)
# ═══════════════════════════════════════════════════════════════════════════

_BLACK   = (0,   0,   0)
_WHITE   = (255, 255, 255)
_GREY_BG = (245, 245, 245)   # alternating row fill
_GREY_LT = (200, 200, 200)   # light rule lines
_ACCENT  = (233, 69,  96)    # red accent — matches dashboard #e94560


# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOM FPDF SUBCLASS — consistent header & footer on every page
# ═══════════════════════════════════════════════════════════════════════════

class _SalesReport(FPDF):
    """
    FPDF2 subclass providing:
      - A full-width black banner header on every page
      - A metadata footer with page number and timestamp
      - Helper methods: section_title(), kpi_row(), df_table()
    """

    COMPANY   = "Superstore Analytics Pipeline"
    GENERATED = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Per-page header ────────────────────────────────────────────────────
    def header(self) -> None:
        self.set_fill_color(*_BLACK)
        self.rect(0, 0, self.w, 16, style="F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_WHITE)
        self.set_y(3)
        self.cell(
            0, 10,
            f"{self.COMPANY.upper()}   —   CORPORATE ANALYTICS REPORT",
            align="C",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.set_text_color(*_BLACK)
        self.ln(6)

    # ── Per-page footer ────────────────────────────────────────────────────
    def footer(self) -> None:
        self.set_y(-13)
        self.set_draw_color(*_GREY_LT)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140, 140, 140)
        self.cell(
            0, 6,
            f"Confidential — Internal Use Only   |   "
            f"Page {self.page_no()}   |   Generated {self.GENERATED}",
            align="C",
        )

    # ── Section title with accent underline ───────────────────────────────
    def section_title(self, title: str) -> None:
        """Bold heading followed by a red accent rule."""
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*_BLACK)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*_ACCENT)
        self.set_line_width(0.7)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_line_width(0.2)
        self.set_draw_color(*_BLACK)
        self.ln(5)

    # ── KPI label / value pair ────────────────────────────────────────────
    def kpi_row(self, label: str, value: str) -> None:
        """Greyed label with a bold black value on the same line."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(85, 85, 85)
        self.cell(85, 7, label)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*_BLACK)
        self.cell(0, 7, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── DataFrame → styled PDF table ─────────────────────────────────────
    def df_table(
        self,
        df: pd.DataFrame,
        col_widths: Optional[list] = None,
    ) -> None:
        """
        Render a pandas DataFrame as an alternating-row PDF table.

        Parameters
        ----------
        df         : DataFrame to render (call .head(n) before passing).
        col_widths : Column widths in mm. Distributed evenly if None.
        """
        if df.empty:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(150, 150, 150)
            self.cell(0, 6, "(No data available)",
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(3)
            return

        cols   = df.columns.tolist()
        usable = self.w - self.l_margin - self.r_margin
        widths = col_widths or [usable / len(cols)] * len(cols)
        row_h  = 6

        # Header row
        self.set_font("Helvetica", "B", 7.5)
        self.set_fill_color(*_BLACK)
        self.set_text_color(*_WHITE)
        self.set_draw_color(*_GREY_LT)
        for col, w in zip(cols, widths):
            self.cell(
                w, row_h + 2,
                str(col).replace("_", " ").title(),
                border=1, align="C", fill=True,
            )
        self.ln(row_h + 2)

        # Data rows
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*_BLACK)
        for row_idx, (_, row) in enumerate(df.iterrows()):
            self.set_fill_color(*(_GREY_BG if row_idx % 2 == 0 else _WHITE))
            for val, w in zip(row.values, widths):
                if isinstance(val, float):
                    cell_text = f"{val:,.2f}"
                elif isinstance(val, int):
                    cell_text = f"{val:,}"
                else:
                    cell_text = str(val)
                self.cell(w, row_h, cell_text, border="B", align="C", fill=True)
            self.ln(row_h)

        self.ln(6)


# ═══════════════════════════════════════════════════════════════════════════
#  INTERNAL HELPER
# ═══════════════════════════════════════════════════════════════════════════

def _equal_widths(n: int, pdf: FPDF) -> list:
    """n equal column widths that fill the usable page width."""
    usable = pdf.w - pdf.l_margin - pdf.r_margin
    return [usable / n] * n


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def generate_pdf_report(results: dict) -> bytes:
    """
    Generate a two-page A4 PDF corporate report from analytical query results.

    Page 1 — Executive Summary
        Revenue KPIs, category performance snapshot, regional snapshot.

    Page 2 — Granular Insights
        Segment analysis, top customers, shipping modes, top products.

    Parameters
    ----------
    results : dict
        Mapping of query_key -> pd.DataFrame, as returned by
        run_all_queries_pandas() or run_all_queries().

    Returns
    -------
    bytes
        Raw PDF bytes — pass directly to st.download_button(data=...).
    """
    pdf = _SalesReport(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(left=15, top=20, right=15)

    # ════════════════════════════════════════════════════════════════════
    #  PAGE 1 : EXECUTIVE SUMMARY
    # ════════════════════════════════════════════════════════════════════
    pdf.add_page()

    # Hero block
    hero_y = pdf.get_y()
    pdf.set_fill_color(*_BLACK)
    pdf.rect(pdf.l_margin, hero_y, pdf.w - pdf.l_margin - pdf.r_margin, 28, style="F")
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*_WHITE)
    pdf.set_y(hero_y + 5)
    pdf.cell(0, 10, "EXECUTIVE SUMMARY",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(190, 190, 190)
    pdf.cell(
        0, 6,
        f"Superstore Analytics Pipeline   •   "
        f"{datetime.now().strftime('%B %d, %Y at %H:%M')}",
        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_text_color(*_BLACK)
    pdf.ln(12)

    # Revenue KPIs
    pdf.section_title("Revenue Overview")
    rev = results.get("total_revenue_summary", pd.DataFrame())
    if not rev.empty:
        r = rev.iloc[0]
        pdf.kpi_row("Total Orders Processed",
                    f"{int(r.get('total_orders', 0)):,}")
        pdf.kpi_row("Total Revenue",
                    f"${float(r.get('total_revenue', 0)):,.2f}")
        pdf.kpi_row("Average Order Value",
                    f"${float(r.get('avg_order_value', 0)):,.2f}")
        pdf.kpi_row("Minimum Sale",
                    f"${float(r.get('min_sale', 0)):,.2f}")
        pdf.kpi_row("Maximum Sale",
                    f"${float(r.get('max_sale', 0)):,.2f}")
        pdf.kpi_row("Sales Std Deviation",
                    f"${float(r.get('std_dev_sales', 0)):,.2f}")
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "Revenue data unavailable.",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Category performance snapshot
    cat = results.get("category_performance", pd.DataFrame())
    if not cat.empty:
        pdf.section_title("Category Performance Snapshot")
        show_cols = [c for c in
                     ["category", "order_count", "total_revenue", "revenue_share_pct"]
                     if c in cat.columns]
        pdf.df_table(cat[show_cols].head(5),
                     col_widths=_equal_widths(len(show_cols), pdf))

    # Regional performance snapshot
    reg = results.get("region_performance", pd.DataFrame())
    if not reg.empty:
        pdf.section_title("Regional Performance Snapshot")
        show_cols = [c for c in
                     ["region", "states_covered", "cities_covered",
                      "total_orders", "total_revenue"]
                     if c in reg.columns]
        pdf.df_table(reg[show_cols].head(5),
                     col_widths=_equal_widths(len(show_cols), pdf))

    # ════════════════════════════════════════════════════════════════════
    #  PAGE 2 : GRANULAR INSIGHTS
    # ════════════════════════════════════════════════════════════════════
    pdf.add_page()

    # Page hero
    hero_y = pdf.get_y()
    pdf.set_fill_color(*_BLACK)
    pdf.rect(pdf.l_margin, hero_y, pdf.w - pdf.l_margin - pdf.r_margin, 20, style="F")
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*_WHITE)
    pdf.set_y(hero_y + 4)
    pdf.cell(0, 12, "GRANULAR INSIGHTS",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_BLACK)
    pdf.ln(10)

    # Segment analysis
    seg = results.get("segment_analysis", pd.DataFrame())
    if not seg.empty:
        pdf.section_title("Customer Segment Analysis")
        show_cols = [c for c in
                     ["segment", "unique_customers", "total_orders",
                      "total_revenue", "avg_order_value", "revenue_per_customer"]
                     if c in seg.columns]
        pdf.df_table(seg[show_cols].head(5),
                     col_widths=_equal_widths(len(show_cols), pdf))

    # Top 10 customers
    cust = results.get("top_10_customers", pd.DataFrame())
    if not cust.empty:
        pdf.section_title("Top 10 Customers by Revenue")
        show_cols = [c for c in
                     ["customer_name", "segment", "total_orders",
                      "total_revenue", "avg_order_value"]
                     if c in cust.columns]
        usable = pdf.w - pdf.l_margin - pdf.r_margin
        widths = (
            [usable * 0.38, usable * 0.18, usable * 0.14,
             usable * 0.16, usable * 0.14]
            if len(show_cols) == 5
            else _equal_widths(len(show_cols), pdf)
        )
        pdf.df_table(cust[show_cols].head(10), col_widths=widths)

    # Shipping mode analysis
    ship = results.get("shipping_mode_analysis", pd.DataFrame())
    if not ship.empty:
        pdf.section_title("Shipping Mode Analysis")
        show_cols = [c for c in
                     ["ship_mode", "total_orders", "total_revenue",
                      "avg_order_value", "avg_shipping_days"]
                     if c in ship.columns]
        pdf.df_table(ship[show_cols],
                     col_widths=_equal_widths(len(show_cols), pdf))

    # Top 10 products
    prod = results.get("top_10_products", pd.DataFrame())
    if not prod.empty:
        pdf.section_title("Top 10 Products by Revenue")
        show_cols = [c for c in
                     ["product_name", "category", "times_ordered", "total_revenue"]
                     if c in prod.columns]
        usable = pdf.w - pdf.l_margin - pdf.r_margin
        widths = (
            [usable * 0.46, usable * 0.20, usable * 0.14, usable * 0.20]
            if len(show_cols) == 4
            else _equal_widths(len(show_cols), pdf)
        )
        pdf.df_table(prod[show_cols].head(10), col_widths=widths)

    return bytes(pdf.output())
