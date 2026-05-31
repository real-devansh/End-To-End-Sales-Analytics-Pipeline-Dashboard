"""
=============================================================================
  SQL ANALYTICS & REPORTING MODULE
  --------------------------------
  Defines and executes key analytical SQL queries against the MySQL database
  to generate actionable business insights and reports.
=============================================================================
"""

import os
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  ANALYTICAL QUERIES — Business Intelligence Suite
# ═══════════════════════════════════════════════════════════════════════════

ANALYTICAL_QUERIES = {
    # ── Revenue & Sales Analysis ───────────────────────────────────────────
    "total_revenue_summary": {
        "title": "Total Revenue Summary",
        "description": "Overall revenue metrics including total, average, min, and max sales.",
        "sql": """
            SELECT
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value,
                ROUND(MIN(sales), 2)          AS min_sale,
                ROUND(MAX(sales), 2)          AS max_sale,
                ROUND(STDDEV(sales), 2)       AS std_dev_sales
            FROM sales_data
        """,
    },
    "monthly_revenue_trend": {
        "title": "Monthly Revenue Trend",
        "description": "Revenue trends aggregated by year and month.",
        "sql": """
            SELECT
                order_year                    AS year,
                order_month                   AS month,
                order_month_name              AS month_name,
                COUNT(*)                      AS order_count,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY order_year, order_month, order_month_name
            ORDER BY order_year, order_month
        """,
    },
    "quarterly_revenue": {
        "title": "Quarterly Revenue Performance",
        "description": "Revenue aggregated by year and quarter.",
        "sql": """
            SELECT
                order_year                    AS year,
                order_quarter                 AS quarter,
                COUNT(*)                      AS order_count,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY order_year, order_quarter
            ORDER BY order_year, order_quarter
        """,
    },
    "yearly_revenue": {
        "title": "Year-over-Year Revenue",
        "description": "Annual revenue with year-over-year growth.",
        "sql": """
            SELECT
                order_year                    AS year,
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY order_year
            ORDER BY order_year
        """,
    },

    # ── Category & Product Analysis ────────────────────────────────────────
    "category_performance": {
        "title": "Category Performance",
        "description": "Revenue and order metrics broken down by product category.",
        "sql": """
            SELECT
                category,
                COUNT(*)                      AS order_count,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value,
                ROUND(SUM(sales) * 100.0 /
                    (SELECT SUM(sales) FROM sales_data), 2)
                                              AS revenue_share_pct
            FROM sales_data
            GROUP BY category
            ORDER BY total_revenue DESC
        """,
    },
    "subcategory_performance": {
        "title": "Sub-Category Performance (Top 15)",
        "description": "Top 15 sub-categories by revenue.",
        "sql": """
            SELECT
                category,
                sub_category,
                COUNT(*)                      AS order_count,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY category, sub_category
            ORDER BY total_revenue DESC
            LIMIT 15
        """,
    },
    "top_10_products": {
        "title": "Top 10 Products by Revenue",
        "description": "Highest revenue-generating individual products.",
        "sql": """
            SELECT
                product_name,
                category,
                sub_category,
                COUNT(*)                      AS times_ordered,
                ROUND(SUM(sales), 2)          AS total_revenue
            FROM sales_data
            GROUP BY product_name, category, sub_category
            ORDER BY total_revenue DESC
            LIMIT 10
        """,
    },

    # ── Customer & Segment Analysis ────────────────────────────────────────
    "segment_analysis": {
        "title": "Customer Segment Analysis",
        "description": "Revenue and behavior metrics by customer segment.",
        "sql": """
            SELECT
                segment,
                COUNT(DISTINCT customer_id)   AS unique_customers,
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value,
                ROUND(SUM(sales) / COUNT(DISTINCT customer_id), 2)
                                              AS revenue_per_customer
            FROM sales_data
            GROUP BY segment
            ORDER BY total_revenue DESC
        """,
    },
    "top_10_customers": {
        "title": "Top 10 Customers by Revenue",
        "description": "Highest-spending customers.",
        "sql": """
            SELECT
                customer_id,
                customer_name,
                segment,
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY customer_id, customer_name, segment
            ORDER BY total_revenue DESC
            LIMIT 10
        """,
    },

    # ── Geographic Analysis ────────────────────────────────────────────────
    "region_performance": {
        "title": "Regional Performance",
        "description": "Revenue metrics across geographic regions.",
        "sql": """
            SELECT
                region,
                COUNT(DISTINCT state)         AS states_covered,
                COUNT(DISTINCT city)          AS cities_covered,
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY region
            ORDER BY total_revenue DESC
        """,
    },
    "top_10_states": {
        "title": "Top 10 States by Revenue",
        "description": "Highest-revenue states.",
        "sql": """
            SELECT
                state,
                region,
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY state, region
            ORDER BY total_revenue DESC
            LIMIT 10
        """,
    },
    "top_10_cities": {
        "title": "Top 10 Cities by Revenue",
        "description": "Highest-revenue cities.",
        "sql": """
            SELECT
                city,
                state,
                region,
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY city, state, region
            ORDER BY total_revenue DESC
            LIMIT 10
        """,
    },

    # ── Shipping & Operations Analysis ─────────────────────────────────────
    "shipping_mode_analysis": {
        "title": "Shipping Mode Analysis",
        "description": "Performance metrics by shipping mode.",
        "sql": """
            SELECT
                ship_mode,
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value,
                ROUND(AVG(shipping_days), 1)  AS avg_shipping_days
            FROM sales_data
            GROUP BY ship_mode
            ORDER BY total_revenue DESC
        """,
    },
    "day_of_week_analysis": {
        "title": "Day of Week Sales Pattern",
        "description": "Sales distribution across days of the week.",
        "sql": """
            SELECT
                order_day_of_week             AS day_of_week,
                COUNT(*)                      AS total_orders,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value
            FROM sales_data
            GROUP BY order_day_of_week
            ORDER BY total_revenue DESC
        """,
    },

    # ── Sales Tier Analysis ────────────────────────────────────────────────
    "sales_tier_distribution": {
        "title": "Sales Tier Distribution",
        "description": "Order distribution across sales tiers (Low/Medium/High/Premium).",
        "sql": """
            SELECT
                sales_tier,
                COUNT(*)                      AS order_count,
                ROUND(SUM(sales), 2)          AS total_revenue,
                ROUND(AVG(sales), 2)          AS avg_order_value,
                ROUND(MIN(sales), 2)          AS min_sale,
                ROUND(MAX(sales), 2)          AS max_sale
            FROM sales_data
            GROUP BY sales_tier
            ORDER BY avg_order_value
        """,
    },
}


def run_all_queries(engine) -> dict:
    """
    Execute all analytical queries and return results as a dictionary
    of DataFrames.

    Parameters
    ----------
    engine : sqlalchemy.Engine
        Database engine connected to the analytics database.

    Returns
    -------
    dict
        Dictionary mapping query_key -> pd.DataFrame of results.
    """
    logger.info("=" * 60)
    logger.info("  SQL ANALYTICS EXECUTION STARTED")
    logger.info("=" * 60)

    results = {}
    start_time = datetime.now()

    for key, query_def in ANALYTICAL_QUERIES.items():
        try:
            df = pd.read_sql(query_def["sql"], engine)
            results[key] = df
            logger.info(
                f"  ✓ {query_def['title']:40s} │ {len(df):,} rows"
            )
        except Exception as e:
            logger.error(f"  ✗ {query_def['title']:40s} │ Error: {e}")
            results[key] = pd.DataFrame()

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("-" * 60)
    logger.info(f"  ✓ Executed {len(results)} queries in {elapsed:.2f}s")
    logger.info("=" * 60)

    return results


def export_reports(results: dict, output_dir: str):
    """
    Export all query results to an Excel workbook with multiple sheets
    and also individual CSV files.

    Parameters
    ----------
    results : dict
        Dictionary of query results from run_all_queries().
    output_dir : str
        Directory to save the reports.
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── Export to single Excel workbook ────────────────────────────────────
    excel_path = os.path.join(output_dir, "analytics_report.xlsx")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for key, df in results.items():
            if not df.empty:
                sheet_name = key[:31]  # Excel sheet name limit
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    logger.info(f"  ✓ Excel report saved: {excel_path}")

    # ── Export individual CSVs ─────────────────────────────────────────────
    csv_dir = os.path.join(output_dir, "csv_reports")
    os.makedirs(csv_dir, exist_ok=True)
    for key, df in results.items():
        if not df.empty:
            csv_path = os.path.join(csv_dir, f"{key}.csv")
            df.to_csv(csv_path, index=False)

    logger.info(f"  ✓ Individual CSV reports saved to: {csv_dir}")

    return excel_path


def print_report_summary(results: dict):
    """Print a formatted summary of key metrics to the console."""
    print("\n" + "═" * 70)
    print("  📊  ANALYTICS REPORT SUMMARY")
    print("═" * 70)

    # ── Total Revenue ──────────────────────────────────────────────────────
    if "total_revenue_summary" in results and not results["total_revenue_summary"].empty:
        r = results["total_revenue_summary"].iloc[0]
        print(f"\n  💰 TOTAL REVENUE")
        print(f"     Total Orders   : {int(r['total_orders']):,}")
        print(f"     Total Revenue  : ${r['total_revenue']:,.2f}")
        print(f"     Avg Order Value: ${r['avg_order_value']:,.2f}")
        print(f"     Max Sale       : ${r['max_sale']:,.2f}")

    # ── Top Category ───────────────────────────────────────────────────────
    if "category_performance" in results and not results["category_performance"].empty:
        top_cat = results["category_performance"].iloc[0]
        print(f"\n  🏆 TOP CATEGORY: {top_cat['category']}")
        print(f"     Revenue        : ${top_cat['total_revenue']:,.2f}")
        print(f"     Revenue Share  : {top_cat['revenue_share_pct']:.1f}%")

    # ── Top Region ─────────────────────────────────────────────────────────
    if "region_performance" in results and not results["region_performance"].empty:
        top_reg = results["region_performance"].iloc[0]
        print(f"\n  🌍 TOP REGION: {top_reg['region']}")
        print(f"     Revenue        : ${top_reg['total_revenue']:,.2f}")
        print(f"     Cities Covered : {int(top_reg['cities_covered']):,}")

    # ── Top Customer ───────────────────────────────────────────────────────
    if "top_10_customers" in results and not results["top_10_customers"].empty:
        top_cust = results["top_10_customers"].iloc[0]
        print(f"\n  👤 TOP CUSTOMER: {top_cust['customer_name']}")
        print(f"     Total Revenue  : ${top_cust['total_revenue']:,.2f}")
        print(f"     Total Orders   : {int(top_cust['total_orders'])}")

    print("\n" + "═" * 70)


# ── Standalone Execution ──────────────────────────────────────────────────
if __name__ == "__main__":
    from database import get_engine

    engine = get_engine()
    results = run_all_queries(engine)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    export_reports(results, output_dir)
    print_report_summary(results)
    engine.dispose()
