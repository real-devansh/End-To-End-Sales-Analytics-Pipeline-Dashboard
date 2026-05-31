"""
=============================================================================
  PREMIUM DATA ANALYTICS DASHBOARD
  ------------------------------------
  Interactive Streamlit dashboard for:
    - Exploratory Data Analysis (EDA)
    - Pipeline Monitor & Data Lineage
=============================================================================
"""

import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# ═══════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Superstore Analytics Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bright Monochrome Sharp Theme CSS ───────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global Styles ─────────────────────────────────────────────── */
    .stApp {
        background: #f5f5f5;
        font-family: 'Inter', sans-serif;
    }

    /* Force all general text elements to black */
    p, span, label, li, .stMarkdown, [data-testid="stMarkdownContainer"] {
        color: #ffffff !important;
    }

    /* ── Sidebar ───────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 2px solid #000000;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #000000 !important;
    }

    /* Filter buttons / dropdowns in sidebar */
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] .stButton > button {
        background: #ffffff !important;
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #000000 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
    }
    
    [data-testid="stSidebar"] [data-baseweb="select"] span {
        color: #000000 !important;
    }

    /* ── Dropdown Menus ────────────────────────────────────────────── */
    [data-baseweb="popover"] {
        background-color: #000000 !important;
        border: 1px solid #ffffff !important;
        border-radius: 0 !important;
    }
    [data-baseweb="menu"] {
        background-color: #000000 !important;
    }
    [data-baseweb="menu"] [role="option"] {
        background-color: #000000 !important;
        color: #ffffff !important;
        border-radius: 0 !important;
    }
    [data-baseweb="menu"] [role="option"]:hover, 
    [data-baseweb="menu"] [role="option"][aria-selected="true"] {
        background-color: #ffffff !important;
        color: #ffffff !important;
    }

    /* ── Chart Tooltips (Plotly CSS overrides) ─────────────────────── */
    .hoverlayer path {
        rx: 0 !important;
        ry: 0 !important;
    }

    /* ── KPI Cards ─────────────────────────────────────────────────── */
    .kpi-card {
        background: #ffffff;
        border: 2px solid #000000;
        border-radius: 0;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 4px 4px 0px #000000;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 6px 6px 0px #000000;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #000000;
        margin: 8px 0;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #555555;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    .kpi-subtitle {
        font-size: 0.75rem;
        color: #888888;
        margin-top: 4px;
    }

    /* ── Chart Containers ──────────────────────────────────────────── */
    .chart-container {
        background: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 0;
        padding: 20px;
        margin: 10px 0;
    }

    /* ── Section Headers ───────────────────────────────────────────── */
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #000000;
        margin: 30px 0 15px 0;
        padding-bottom: 10px;
        border-bottom: 3px solid #000000;
    }

    /* ── Tabs ──────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background: #000000;
        padding: 0px;
        border-radius: 0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        color: #000000;
        font-weight: 600;
        padding: 10px 20px;
        border: 1px solid #cccccc;
    }
    .stTabs [aria-selected="true"] {
        background: #000000 !important;
        color: #000000 !important;
    }

    /* ── DataFrames ────────────────────────────────────────────────── */
    .stDataFrame {
        border-radius: 0;
        overflow: hidden;
    }

    /* ── Headers ───────────────────────────────────────────────────── */
    h1, h2, h3 {
        color: #000000 !important;
    }

    /* ── Metric styling ─────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 2px solid #000000;
        border-radius: 0;
        padding: 16px;
    }

    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* ── Text area and code ────────────────────────────────────── */
    .stTextArea textarea {
        background: #ffffff !important;
        border: 2px solid #000000 !important;
        border-radius: 0 !important;
        color: #000000 !important;
        font-family: 'Fira Code', 'Consolas', monospace !important;
    }

    /* ── Buttons ────────────────────────────────────────────────── */
    .stButton > button {
        background: #000000 !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        border-radius: 0 !important;
        font-weight: 600 !important;
        padding: 8px 24px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: #656464  !important;
        transform: translateY(-2px) !important;
        box-shadow: 3px 3px 0px #000000 !important;
    }

    /* ── Hero Banner ───────────────────────────────────────────── */
    .hero-banner {
        background: #ffffff;
        border: 3px solid #000000;
        border-radius: 0;
        padding: 32px;
        margin-bottom: 30px;
        text-align: center;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #000000;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        color: #555555;
        font-size: 1rem;
        font-weight: 400;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_data():
    """Load processed data from CSV."""
    processed_path = os.path.join(os.path.dirname(__file__), "data", "processed", "processed_data.csv")
    raw_path = os.path.join(os.path.dirname(__file__), "data", "raw", "train.csv")

    if os.path.exists(processed_path):
        df = pd.read_csv(processed_path)
        source = "Processed"
    elif os.path.exists(raw_path):
        df = pd.read_csv(raw_path)
        source = "Raw"
    else:
        return None, "No data"

    # Ensure datetime columns
    for col in ["order_date", "ship_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df, source





# ═══════════════════════════════════════════════════════════════════════════
#  CHART THEME
# ═══════════════════════════════════════════════════════════════════════════

CHART_TEMPLATE = "plotly_white"
COLOR_PALETTE = ["#e94560", "#ff6b6b", "#ffa07a", "#48dbfb", "#0abde3",
                 "#10ac84", "#1dd1a1", "#feca57", "#ff9ff3", "#54a0ff"]

CHART_LAYOUT = dict(
    template=CHART_TEMPLATE,
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f5f5f5",
    font=dict(family="Inter", color="#000000"),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor="#000000", font=dict(color="#000000")),
    margin=dict(l=40, r=40, t=50, b=40),
    legend=dict(
        bgcolor="#ffffff",
        bordercolor="#000000",
        font=dict(size=11, color="#000000")
    )
)


def apply_layout(fig, title=""):
    """Apply consistent layout to plotly figures."""
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=title, font=dict(size=16, color="#000000"), x=0.02),
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.1)", zeroline=False, color="#000000", tickfont=dict(color="#000000"), title_font=dict(color="#000000"))
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.1)", zeroline=False, color="#000000", tickfont=dict(color="#000000"), title_font=dict(color="#000000"))
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  KPI CARD COMPONENT
# ═══════════════════════════════════════════════════════════════════════════

def kpi_card(label, value, subtitle=""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## Navigation")
    page = st.radio(
        "Select Page",
        ["Overview Dashboard", "Exploratory Analysis", "Pipeline Monitor"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### Filters")

# ── Load Data ──────────────────────────────────────────────────────────────
df, data_source = load_data()

if df is None:
    st.error("❌ No data found. Please run the pipeline first: `python src/run_pipeline.py`")
    st.stop()

# ── Sidebar Filters ────────────────────────────────────────────────────────
with st.sidebar:
    # Category filter
    if "category" in df.columns:
        categories = ["All"] + sorted(df["category"].unique().tolist())
        selected_category = st.selectbox("Category", categories)
    else:
        selected_category = "All"

    # Region filter
    if "region" in df.columns:
        regions = ["All"] + sorted(df["region"].unique().tolist())
        selected_region = st.selectbox("Region", regions)
    else:
        selected_region = "All"

    # Segment filter
    if "segment" in df.columns:
        segments = ["All"] + sorted(df["segment"].unique().tolist())
        selected_segment = st.selectbox("Segment", segments)
    else:
        selected_segment = "All"

    # Year filter
    if "order_year" in df.columns:
        years = ["All"] + sorted(df["order_year"].dropna().unique().astype(int).tolist())
        selected_year = st.selectbox("Year", years)
    else:
        selected_year = "All"

    st.markdown("---")
    st.markdown(f"**Data Source:** {data_source}")
    st.markdown(f"**Records:** {len(df):,}")
    st.markdown(f"**Columns:** {df.shape[1]}")

# ── Apply Filters ──────────────────────────────────────────────────────────
filtered_df = df.copy()
if selected_category != "All" and "category" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["category"] == selected_category]
if selected_region != "All" and "region" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["region"] == selected_region]
if selected_segment != "All" and "segment" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["segment"] == selected_segment]
if selected_year != "All" and "order_year" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["order_year"] == int(selected_year)]


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 1: OVERVIEW DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

if page == "Overview Dashboard":
    # ── Hero Banner ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">Superstore Analytics Dashboard</div>
        <div class="hero-subtitle">End-to-End Data Analytics Pipeline • Real-time Insights • Powered by Python + MySQL</div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ────────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)

    total_revenue = filtered_df["sales"].sum() if "sales" in filtered_df.columns else 0
    total_orders = len(filtered_df)
    avg_order = filtered_df["sales"].mean() if "sales" in filtered_df.columns else 0
    unique_customers = filtered_df["customer_id"].nunique() if "customer_id" in filtered_df.columns else 0
    unique_products = filtered_df["product_name"].nunique() if "product_name" in filtered_df.columns else 0

    with col1:
        kpi_card("Total Revenue", f"${total_revenue:,.0f}", f"From {total_orders:,} orders")
    with col2:
        kpi_card("Average Order", f"${avg_order:,.2f}", "Per transaction")
    with col3:
        kpi_card("Total Orders", f"{total_orders:,}", "Transactions")
    with col4:
        kpi_card("Customers", f"{unique_customers:,}", "Unique buyers")
    with col5:
        kpi_card("Products", f"{unique_products:,}", "Unique items")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Revenue Trend ──────────────────────────────────────────────────────
    if "order_year" in filtered_df.columns and "order_month" in filtered_df.columns:
        monthly = (
            filtered_df.groupby(["order_year", "order_month"])["sales"]
            .agg(["sum", "count"])
            .reset_index()
        )
        monthly.columns = ["Year", "Month", "Revenue", "Orders"]
        monthly["Period"] = monthly["Year"].astype(str) + "-" + monthly["Month"].astype(str).str.zfill(2)
        monthly = monthly.sort_values("Period")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["Period"], y=monthly["Revenue"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#e94560", width=3),
            marker=dict(size=6, color="#ff6b6b"),
            fillcolor="rgba(233,69,96,0.1)",
            name="Revenue"
        ))
        apply_layout(fig, "Monthly Revenue Trend")
        fig.update_layout(height=400, xaxis_title="Month", yaxis_title="Revenue ($)")
        st.plotly_chart(fig, use_container_width=True)

    # ── Two Column Charts ──────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        # Category Revenue
        if "category" in filtered_df.columns:
            cat_data = (
                filtered_df.groupby("category")["sales"]
                .sum().reset_index()
                .sort_values("sales", ascending=True)
            )
            fig = px.bar(
                cat_data, x="sales", y="category", orientation="h",
                color="sales", color_continuous_scale=["#ff6b6b", "#e94560", "#a82855"],
            )
            apply_layout(fig, "Revenue by Category")
            fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # Region Revenue
        if "region" in filtered_df.columns:
            reg_data = (
                filtered_df.groupby("region")["sales"]
                .sum().reset_index()
                .sort_values("sales", ascending=False)
            )
            fig = px.pie(
                reg_data, values="sales", names="region",
                color_discrete_sequence=COLOR_PALETTE, hole=0.45,
            )
            apply_layout(fig, "Revenue Distribution by Region")
            fig.update_layout(height=350)
            fig.update_traces(
                textposition="inside", textinfo="percent+label",
                marker=dict(line=dict(color="#0f0c29", width=2))
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Second Row Charts ──────────────────────────────────────────────────
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        # Top 10 Sub-Categories
        if "sub_category" in filtered_df.columns:
            sub_data = (
                filtered_df.groupby("sub_category")["sales"]
                .sum().reset_index()
                .sort_values("sales", ascending=False).head(10)
            )
            fig = px.bar(
                sub_data, x="sub_category", y="sales",
                color="sales", color_continuous_scale=["#ff6b6b", "#e94560", "#a82855"],
            )
            apply_layout(fig, "Top 10 Sub-Categories by Revenue")
            fig.update_layout(height=380, showlegend=False, coloraxis_showscale=False,
                              xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col_right2:
        # Segment Analysis
        if "segment" in filtered_df.columns:
            seg_data = filtered_df.groupby("segment").agg(
                Revenue=("sales", "sum"),
                Orders=("sales", "count"),
                AvgOrder=("sales", "mean")
            ).reset_index()
            fig = px.bar(
                seg_data, x="segment", y="Revenue",
                color="segment", color_discrete_sequence=["#e94560", "#48dbfb", "#10ac84"],
                text=seg_data["Revenue"].apply(lambda x: f"${x:,.0f}")
            )
            apply_layout(fig, "Revenue by Customer Segment")
            fig.update_layout(height=380, showlegend=False)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # ── Shipping Analysis ──────────────────────────────────────────────────
    if "ship_mode" in filtered_df.columns and "shipping_days" in filtered_df.columns:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            ship_data = filtered_df.groupby("ship_mode").agg(
                Revenue=("sales", "sum"),
                AvgDays=("shipping_days", "mean")
            ).reset_index().sort_values("Revenue", ascending=False)
            fig = px.bar(
                ship_data, x="ship_mode", y="Revenue",
                color="AvgDays", color_continuous_scale="RdYlGn_r",
                text=ship_data["Revenue"].apply(lambda x: f"${x:,.0f}")
            )
            apply_layout(fig, "Shipping Mode Performance")
            fig.update_layout(height=350)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        with col_s2:
            fig = px.box(
                filtered_df, x="ship_mode", y="shipping_days",
                color="ship_mode", color_discrete_sequence=COLOR_PALETTE,
            )
            apply_layout(fig, "Shipping Days Distribution")
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 2: EXPLORATORY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Exploratory Analysis":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">Exploratory Data Analysis</div>
        <div class="hero-subtitle">Deep dive into data distributions, correlations, patterns, and outliers</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Distributions", "Correlations", "Outliers", "Data Quality", "Trends"
    ])

    # ── TAB 1: Distributions ───────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="section-header">Sales Distribution Analysis</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if "sales" in filtered_df.columns:
                fig = px.histogram(
                    filtered_df, x="sales", nbins=80,
                    color_discrete_sequence=["#e94560"],
                    marginal="box",
                )
                apply_layout(fig, "Sales Value Distribution")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "sales" in filtered_df.columns:
                fig = px.histogram(
                    filtered_df[filtered_df["sales"] < filtered_df["sales"].quantile(0.95)],
                    x="sales", nbins=60,
                    color_discrete_sequence=["#48dbfb"],
                    marginal="violin",
                )
                apply_layout(fig, "Sales Distribution (Excluding Top 5% Outliers)")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        # Category-wise distribution
        if "category" in filtered_df.columns and "sales" in filtered_df.columns:
            fig = px.violin(
                filtered_df, x="category", y="sales",
                color="category", color_discrete_sequence=COLOR_PALETTE,
                box=True, points="outliers",
            )
            apply_layout(fig, "Sales Distribution by Category")
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Sales tier pie
        if "sales_tier" in filtered_df.columns:
            tier_data = filtered_df["sales_tier"].value_counts().reset_index()
            tier_data.columns = ["Tier", "Count"]
            fig = px.pie(
                tier_data, values="Count", names="Tier",
                color_discrete_sequence=["#10ac84", "#48dbfb", "#feca57", "#e94560"],
                hole=0.4,
            )
            apply_layout(fig, "Order Distribution by Sales Tier")
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)

    # ── TAB 2: Correlations ────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-header">Correlation Analysis</div>', unsafe_allow_html=True)

        numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) >= 2:
            corr_matrix = filtered_df[numeric_cols].corr()

            fig = px.imshow(
                corr_matrix,
                text_auto=".2f",
                color_continuous_scale=["#0abde3", "#1a1a2e", "#e94560"],
                aspect="auto",
            )
            apply_layout(fig, "Correlation Heatmap (Numeric Features)")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

        # Scatter: Sales vs Shipping Days
        if "sales" in filtered_df.columns and "shipping_days" in filtered_df.columns:
            fig = px.scatter(
                filtered_df.sample(min(2000, len(filtered_df))),
                x="shipping_days", y="sales",
                color="category" if "category" in filtered_df.columns else None,
                color_discrete_sequence=COLOR_PALETTE,
                opacity=0.6, size_max=10,
            )
            apply_layout(fig, "Sales vs Shipping Days")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    # ── TAB 3: Outlier Detection ───────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-header">Outlier Detection</div>', unsafe_allow_html=True)

        if "sales" in filtered_df.columns:
            Q1 = filtered_df["sales"].quantile(0.25)
            Q3 = filtered_df["sales"].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outliers = filtered_df[(filtered_df["sales"] < lower) | (filtered_df["sales"] > upper)]

            col1, col2, col3 = st.columns(3)
            with col1:
                kpi_card("Outliers Detected", f"{len(outliers):,}",
                         f"{(len(outliers)/len(filtered_df)*100):.1f}% of total")
            with col2:
                kpi_card("IQR Range", f"${lower:.0f} — ${upper:.0f}", "1.5x IQR bounds")
            with col3:
                kpi_card("Max Outlier", f"${outliers['sales'].max():,.0f}" if len(outliers) > 0 else "N/A",
                         "Highest outlier value")

            st.markdown("<br>", unsafe_allow_html=True)

            fig = go.Figure()
            fig.add_trace(go.Box(
                y=filtered_df["sales"], name="Sales",
                marker_color="#e94560", boxpoints="outliers",
                jitter=0.3, pointpos=-1.8,
            ))
            apply_layout(fig, "Sales Outlier Detection (IQR Method)")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            if len(outliers) > 0:
                st.markdown("**Top 10 Outlier Transactions:**")
                display_cols = [c for c in ["order_id", "customer_name", "product_name", "category", "sales"] if c in outliers.columns]
                st.dataframe(
                    outliers.nlargest(10, "sales")[display_cols],
                    use_container_width=True, hide_index=True
                )

    # ── TAB 4: Data Quality ────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="section-header">Data Quality Report</div>', unsafe_allow_html=True)

        quality_data = []
        for col in filtered_df.columns:
            null_count = filtered_df[col].isnull().sum()
            null_pct = (null_count / len(filtered_df)) * 100
            unique_count = filtered_df[col].nunique()
            quality_data.append({
                "Column": col,
                "Dtype": str(filtered_df[col].dtype),
                "Non-Null": f"{len(filtered_df) - null_count:,}",
                "Null Count": null_count,
                "Null %": f"{null_pct:.2f}%",
                "Unique": unique_count,
                "Unique %": f"{(unique_count/len(filtered_df)*100):.1f}%",
            })

        quality_df = pd.DataFrame(quality_data)
        st.dataframe(quality_df, use_container_width=True, hide_index=True, height=600)

        # Missing value heatmap
        null_counts = filtered_df.isnull().sum()
        if null_counts.sum() > 0:
            null_cols = null_counts[null_counts > 0]
            fig = px.bar(
                x=null_cols.index, y=null_cols.values,
                color=null_cols.values,
                color_continuous_scale=["#feca57", "#e94560"],
                labels={"x": "Column", "y": "Missing Values"},
            )
            apply_layout(fig, "Missing Values by Column")
            fig.update_layout(height=350, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No missing values — dataset is 100% complete after processing!")

        # Dataset summary stats — numeric only to avoid pyarrow serialization crash
        st.markdown("**Numeric Summary Statistics:**")
        numeric_df = filtered_df.select_dtypes(include="number")
        st.dataframe(numeric_df.describe().T.round(2), use_container_width=True)

    # ── TAB 5: Advanced Trends ─────────────────────────────────────────────
    with tab5:
        st.markdown('<div class="section-header">Advanced Trend Analysis</div>', unsafe_allow_html=True)

        # YoY Growth
        if "order_year" in filtered_df.columns:
            yearly = filtered_df.groupby("order_year")["sales"].sum().reset_index()
            yearly.columns = ["Year", "Revenue"]
            yearly["Growth %"] = yearly["Revenue"].pct_change() * 100

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    yearly, x="Year", y="Revenue",
                    color="Revenue", color_continuous_scale=["#feca57", "#e94560"],
                    text=yearly["Revenue"].apply(lambda x: f"${x:,.0f}")
                )
                apply_layout(fig, "Year-over-Year Revenue")
                fig.update_layout(height=380, coloraxis_showscale=False)
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(
                    yearly.dropna(subset=["Growth %"]),
                    x="Year", y="Growth %",
                    color="Growth %", color_continuous_scale=["#feca57", "#e94560"],
                    text=yearly.dropna(subset=["Growth %"])["Growth %"].apply(lambda x: f"{x:+.1f}%")
                )
                apply_layout(fig, "Year-over-Year Growth Rate (%)")
                fig.update_layout(height=380, coloraxis_showscale=False)
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

        # Category trend over time
        if "order_year" in filtered_df.columns and "category" in filtered_df.columns:
            cat_trend = (
                filtered_df.groupby(["order_year", "category"])["sales"]
                .sum().reset_index()
            )
            fig = px.line(
                cat_trend, x="order_year", y="sales", color="category",
                color_discrete_sequence=COLOR_PALETTE,
                markers=True, line_shape="spline",
            )
            apply_layout(fig, "Category Revenue Trend Over Years")
            fig.update_layout(height=400)
            fig.update_traces(line=dict(width=3))
            st.plotly_chart(fig, use_container_width=True)

        # Day of week heatmap
        if "order_day_of_week" in filtered_df.columns and "order_month" in filtered_df.columns:
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            heatmap_data = filtered_df.groupby(["order_day_of_week", "order_month"])["sales"].sum().reset_index()
            heatmap_pivot = heatmap_data.pivot_table(
                index="order_day_of_week", columns="order_month", values="sales", fill_value=0
            )
            # Reindex to proper day order
            valid_days = [d for d in day_order if d in heatmap_pivot.index]
            heatmap_pivot = heatmap_pivot.reindex(valid_days)

            fig = px.imshow(
                heatmap_pivot,
                color_continuous_scale=["#0abde3", "#1a1a2e", "#e94560"],
                labels={"x": "Month", "y": "Day of Week", "color": "Revenue"},
                aspect="auto",
            )
            apply_layout(fig, "Sales Heatmap: Day of Week × Month")
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)



# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 4: PIPELINE MONITOR
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Pipeline Monitor":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">Pipeline Monitor</div>
        <div class="hero-subtitle">Data lineage, storage details, and pipeline execution metadata</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Pipeline Architecture ──────────────────────────────────────────────
    st.markdown('<div class="section-header">Pipeline Architecture</div>', unsafe_allow_html=True)

    stages = {
        "1. Ingestion": "Auto-detects CSV/Excel/JSON → loads to DataFrame",
        "2. Cleaning": "Standardize columns → remove duplicates → handle nulls",
        "3. Transformation": "Date parsing → feature engineering → sales tiers",
        "4. Storage (CSV)": "Save processed data to data/processed/",
        "5. Data Serving": "Load processed CSV into memory for real-time dashboard",
        "6. Analytics": "Generate interactive visualizations and insights",
    }

    cols = st.columns(3)
    for i, (stage, desc) in enumerate(stages.items()):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="kpi-card" style="text-align:left; margin-bottom:12px;">
                <div style="font-size:1.1rem; font-weight:700; color:#000000; margin-bottom:6px;">{stage}</div>
                <div style="color:#555555; font-size:0.85rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Data Lineage ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Data Files</div>', unsafe_allow_html=True)

    base_dir = os.path.dirname(__file__)
    files_info = []

    for root, dirs, files in os.walk(os.path.join(base_dir, "data")):
        for f in files:
            fpath = os.path.join(root, f)
            rel_path = os.path.relpath(fpath, base_dir)
            size_kb = os.path.getsize(fpath) / 1024
            files_info.append({
                "File": rel_path,
                "Size": f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB",
                "Modified": datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M"),
            })

    if files_info:
        st.dataframe(pd.DataFrame(files_info), use_container_width=True, hide_index=True)
    else:
        st.info("No data files found. Run the pipeline first.")



    # ── Dataset Shape ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Current Dataset Overview</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Rows", f"{len(df):,}", "Total records")
    with col2:
        kpi_card("Columns", f"{df.shape[1]}", "Features")
    with col3:
        mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
        kpi_card("Memory", f"{mem:.1f} MB", "In-memory size")
    with col4:
        nulls = df.isnull().sum().sum()
        kpi_card("Null Values", f"{nulls:,}", f"{(nulls/(df.shape[0]*df.shape[1])*100):.2f}% of cells")

    # ── Sample Data ────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Sample Data (First 20 rows):**")
    st.dataframe(df.head(20), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:rgba(0,0,0,1); padding:20px;'>"
    "End-to-End Data Analytics Pipeline — Python • MySQL • Streamlit"
    "</div>",
    unsafe_allow_html=True
)
