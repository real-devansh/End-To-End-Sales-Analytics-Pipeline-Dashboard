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
import zipfile
from io import BytesIO
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Pipeline imports ──────────────────────────────────────────────────────
from src.cleaning import clean_and_transform
from src.query import run_all_queries_pandas

# ═══════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Superstore Analytics Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Deep Space Dark Theme CSS ───────────────────────────────────────────────
with open(os.path.join(os.path.dirname(__file__), "style.css"), encoding="utf-8") as f:
    st.markdown(f"<style>\n{f.read()}\n</style>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

_RAW_PATH = os.path.join(os.path.dirname(__file__), "data", "raw", "train.csv")
_PROCESSED_PATH = os.path.join(os.path.dirname(__file__), "data", "processed", "processed_data.csv")

REQUIRED_COLUMNS = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
    "Customer ID", "Customer Name", "Segment", "Country", "City", "State",
    "Postal Code", "Region", "Product ID", "Category", "Sub-Category",
    "Product Name", "Sales",
]


# ═══════════════════════════════════════════════════════════════════════════
#  DATA HELPERS (in-memory, no disk writes)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600, show_spinner="⚙️ Loading default dataset…")
def _load_default_raw() -> pd.DataFrame:
    """Load and return the immutable base train.csv (cached)."""
    if os.path.exists(_PROCESSED_PATH):
        df = pd.read_csv(_PROCESSED_PATH)
    elif os.path.exists(_RAW_PATH):
        df = pd.read_csv(_RAW_PATH)
    else:
        return None
    for col in ["order_date", "ship_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner="🔄 Cleaning uploaded file…", max_entries=5)
def _clean_uploaded_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse and clean an uploaded CSV entirely in memory."""
    buf = BytesIO(file_bytes)
    raw_df = pd.read_csv(buf)
    return clean_and_transform(raw_df)


@st.cache_data(show_spinner="📊 Computing analytics…", max_entries=3)
def _run_analytics(df: pd.DataFrame) -> dict:
    """Run all analytical queries. Cached per unique DataFrame content."""
    return run_all_queries_pandas(df)


def create_zip_archive(df: pd.DataFrame, results: dict) -> bytes:
    """Bundle cleaned DataFrame and query results into an in-memory ZIP."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("cleaned_data.csv", df.to_csv(index=False))
        for key, result_df in results.items():
            if not result_df.empty:
                zf.writestr(f"reports/{key}.csv", result_df.to_csv(index=False))
    buf.seek(0)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
#  KPI CARD COMPONENT
# ═══════════════════════════════════════════════════════════════════════════

def kpi_card(label, value, subtitle=""):
    """Render a styled KPI metric card."""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  CHART THEME
# ═══════════════════════════════════════════════════════════════════════════

# Deep Space Dark palette — matches CSS design system
CHART_TEMPLATE = "plotly_dark"
COLOR_PALETTE = [
    "#1ED760",  # accent green
    "#1fef6a",  # green lighter
    "#48dbfb",  # cyan
    "#0abde3",  # blue
    "#feca57",  # amber
    "#ff9ff3",  # pink
    "#54a0ff",  # periwinkle
    "#ff6b6b",  # coral
    "#5f27cd",  # violet
    "#10ac84",  # teal
]

CHART_LAYOUT = dict(
    template=CHART_TEMPLATE,
    paper_bgcolor="#181818",
    plot_bgcolor="#181818",
    font=dict(family="Inter, system-ui, sans-serif", color="#B3B3B3", size=12),
    hoverlabel=dict(
        bgcolor="#242424",
        bordercolor="#535353",
        font=dict(color="#FFFFFF", family="Inter, sans-serif", size=12)
    ),
    margin=dict(l=40, r=40, t=52, b=40),
    legend=dict(
        bgcolor="rgba(24,24,24,0.8)",
        bordercolor="#535353",
        borderwidth=1,
        font=dict(size=11, color="#B3B3B3")
    )
)


def apply_layout(fig, title=""):
    """Apply consistent Deep Space dark layout to plotly figures."""
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text=title,
            font=dict(size=15, color="#FFFFFF", family="Inter, sans-serif"),
            x=0.02
        ),
    )
    fig.update_xaxes(
        gridcolor="rgba(83,83,83,0.3)",
        zeroline=False,
        color="#B3B3B3",
        tickfont=dict(color="#B3B3B3"),
        title_font=dict(color="#B3B3B3"),
        linecolor="#535353",
    )
    fig.update_yaxes(
        gridcolor="rgba(83,83,83,0.3)",
        zeroline=False,
        color="#B3B3B3",
        tickfont=dict(color="#B3B3B3"),
        title_font=dict(color="#B3B3B3"),
        linecolor="#535353",
    )
    return fig


def _generate_synthetic_100k(base_df: pd.DataFrame) -> pd.DataFrame:
    """Resample base_df to 100,000 rows with variance — purely in memory."""
    TARGET = 100_000
    df_large = base_df.sample(n=TARGET, replace=True).reset_index(drop=True)
    if "Row ID" in df_large.columns:
        df_large["Row ID"] = np.arange(1, TARGET + 1)
    if "Sales" in df_large.columns:
        noise = np.random.uniform(0.85, 1.15, TARGET)
        df_large["Sales"] = (df_large["Sales"] * noise).round(2)
    for col in ["Order Date", "Ship Date"]:
        if col in df_large.columns:
            offsets = pd.to_timedelta(np.random.randint(1, 365, TARGET), unit="d")
            df_large[col] = pd.to_datetime(df_large[col], errors="coerce") + offsets
            df_large[col] = df_large[col].dt.strftime("%d/%m/%Y")
    if "Order ID" in df_large.columns:
        suffix = np.random.randint(1000, 9999, TARGET).astype(str)
        df_large["Order ID"] = df_large["Order ID"].str[:-4] + suffix
    return df_large


# ═══════════════════════════════════════════════════════════════════════════
#  SESSION STATE INITIALISATION
# ═══════════════════════════════════════════════════════════════════════════

if "active_df" not in st.session_state:
    _default = _load_default_raw()
    if _default is None:
        st.error("❌ No data found. Run the pipeline first: `python src/run_pipeline.py`")
        st.stop()
    st.session_state["active_df"]    = _default
    st.session_state["data_source"]  = "Default Superstore Data"
    st.session_state["is_generated"] = False


# ═══════════════════════════════════════════════════════════════════════════
#  DATASET MANAGEMENT MODAL
# ═══════════════════════════════════════════════════════════════════════════

@st.dialog("Dataset Management & Data Ingestion", width="large")
def _dataset_modal():
    with st.expander("📋 Required Schema — expand to view", expanded=False):
        st.markdown(
            "> **Custom datasets must include all required columns "
            "to prevent downstream pipeline errors.**"
        )
        st.code(", ".join(REQUIRED_COLUMNS), language="text")

    st.markdown("---")

    tab_upload, tab_generate, tab_reset = st.tabs([
        "⬆️ Upload Custom Dataset",
        "⚡ Generate 100k Synthetic",
        "↩️ Reset to Default",
    ])

    with tab_upload:
        st.markdown("Upload a `.csv` file. It will be validated against the required schema before loading.")
        uploaded = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            label_visibility="collapsed",
            key="modal_uploader",
        )
        if uploaded is not None:
            peek = pd.read_csv(BytesIO(uploaded.getvalue()), nrows=5)
            missing = [c for c in REQUIRED_COLUMNS if c not in peek.columns]
            if missing:
                st.error(
                    "**Schema validation failed.** "
                    "The following required columns are missing:\n\n"
                    + "\n".join(f"- `{c}`" for c in missing)
                )
                st.stop()
            else:
                st.success(
                    f"✅ Schema validated — all {len(REQUIRED_COLUMNS)} required columns present."
                )
                if st.button("Load Dataset", key="modal_load_btn", use_container_width=True):
                    with st.spinner("Cleaning & loading…"):
                        cleaned = _clean_uploaded_bytes(uploaded.getvalue(), uploaded.name)
                    st.session_state["active_df"]    = cleaned
                    st.session_state["data_source"]  = uploaded.name
                    st.session_state["is_generated"] = False
                    st.toast(f"✅ {uploaded.name} loaded — {len(cleaned):,} rows", icon="🗂️")
                    st.rerun()

    with tab_generate:
        if st.session_state.get("is_generated", False):
            st.warning(
                "⚠️ A generated 100k dataset is currently active. "
                "Generating a new one will replace the active session data "
                "(your base dataset remains safe)."
            )
        else:
            st.info(
                "This will resample the base `train.csv` to **100,000 rows** "
                "with randomised sales variance and date offsets — all in memory."
            )
        if st.button("⚡ Generate & Load 100k Rows", key="modal_gen_btn", use_container_width=True):
            raw_base = pd.read_csv(_RAW_PATH) if os.path.exists(_RAW_PATH) else None
            if raw_base is None:
                st.error("Base dataset not found. Cannot generate synthetic data.")
                st.stop()
            with st.spinner("Generating 100,000 rows…"):
                synth = _generate_synthetic_100k(raw_base)
                cleaned_synth = clean_and_transform(synth)
            st.session_state["active_df"]    = cleaned_synth
            st.session_state["data_source"]  = "Synthetic 100k Resample"
            st.session_state["is_generated"] = True
            st.toast("⚡ 100k synthetic dataset loaded into session!", icon="✅")
            st.rerun()

    with tab_reset:
        current_source = st.session_state.get("data_source", "—")
        st.markdown(f"**Currently active:** `{current_source}`")
        st.markdown(
            "Reset will restore the original Superstore dataset "
            "(≈9,800 rows) from `train.csv`."
        )
        if st.button("↩️ Reset to Default Dataset", key="modal_reset_btn", use_container_width=True):
            _default = _load_default_raw()
            st.session_state["active_df"]    = _default
            st.session_state["data_source"]  = "Default Superstore Data"
            st.session_state["is_generated"] = False
            st.toast("↩️ Restored default Superstore dataset.", icon="✅")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    if st.button("🗄️ Upload / Manage Dataset", use_container_width=True, key="open_modal_btn"):
        _dataset_modal()

    _src  = st.session_state.get("data_source", "—")
    _rows = len(st.session_state["active_df"])
    _cols = len(st.session_state["active_df"].columns)
    st.markdown(
        f'<div style="background:#1e1e1e;border:1px solid #535353;border-radius:0.6rem;'
        f'padding:12px 14px;margin-top:8px;font-size:0.78rem;line-height:1.9;">'
        f'<div><span style="color:#B3B3B3">Current Source</span><br>'
        f'<strong style="color:#FFFFFF">{_src}</strong></div>'
        f'<div style="margin-top:6px">'
        f'<span style="color:#B3B3B3">Loaded Records</span><br>'
        f'<strong style="color:#1ED760;font-family:\'JetBrains Mono\',monospace">{_rows:,}</strong>'
        f'</div>'
        f'<div style="margin-top:6px">'
        f'<span style="color:#B3B3B3">Total Attributes</span><br>'
        f'<strong style="color:#FFFFFF">{_cols} columns</strong>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("## Navigation")
    page = st.radio(
        "Select Page",
        ["Overview Dashboard", "Exploratory Analysis", "Pipeline Monitor"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### Filters")

# Resolve active DataFrame
df = st.session_state["active_df"]
data_source = st.session_state.get("data_source", "Default Superstore Data")

# Sidebar Filters
with st.sidebar:
    if "category" in df.columns:
        categories = ["All"] + sorted(df["category"].unique().tolist())
        selected_category = st.selectbox("Category", categories)
    else:
        selected_category = "All"
    if "region" in df.columns:
        regions = ["All"] + sorted(df["region"].unique().tolist())
        selected_region = st.selectbox("Region", regions)
    else:
        selected_region = "All"
    if "segment" in df.columns:
        segments = ["All"] + sorted(df["segment"].unique().tolist())
        selected_segment = st.selectbox("Segment", segments)
    else:
        selected_segment = "All"
    if "order_year" in df.columns:
        years = ["All"] + sorted(df["order_year"].dropna().unique().astype(int).tolist())
        selected_year = st.selectbox("Year", years)
    else:
        selected_year = "All"

# Apply Filters
filtered_df = df.copy()
if selected_category != "All" and "category" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["category"] == selected_category]
if selected_region != "All" and "region" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["region"] == selected_region]
if selected_segment != "All" and "segment" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["segment"] == selected_segment]
if selected_year != "All" and "order_year" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["order_year"] == int(selected_year)]

# Compute Analytics Results
results = _run_analytics(df)

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

    # ── Sample Data ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Sample Data (First 20 rows):**")
    st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Download Centre ──────────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">📥 Download Centre</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Export the current dataset and all analytical reports. "
        "Downloads are based on the **full unfiltered dataset**."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    dl_col1, dl_col2 = st.columns(2)

    # ── Column 1: Cleaned CSV ───────────────────────────────────────
    with dl_col1:
        st.markdown("**🗂 Cleaned Dataset (CSV)**")
        st.caption(
            "The fully processed, feature-engineered sales data "
            "as a single CSV file."
        )
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Download Cleaned CSV",
            data=csv_bytes,
            file_name="cleaned_sales_data.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_cleaned_csv",
        )

    # ── Column 2: Full Analytics ZIP ───────────────────────────────
    with dl_col2:
        st.markdown("**📦 Full Analytics ZIP**")
        st.caption(
            "Cleaned data + all 15 analytical query results "
            "bundled into a single ZIP archive, built in memory."
        )
        zip_bytes = create_zip_archive(df, results)
        st.download_button(
            label="⬇ Download Analytics ZIP",
            data=zip_bytes,
            file_name=(
                f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
            ),
            mime="application/zip",
            use_container_width=True,
            key="dl_analytics_zip",
        )

    # ── Column 3: Corporate PDF Report ────────────────────────────
    # (Hidden as per request)
    # with dl_col3:
    #     st.markdown("**📋 Corporate PDF Report**")
    #     st.caption(
    #         "Multi-page A4 PDF with executive summary KPIs, "
    #         "category/region snapshots, and granular insight tables."
    #     )
    #     try:
    #         from pdf_generator import generate_pdf_report
    #         pdf_bytes = generate_pdf_report(results)
    #         st.download_button(
    #             label="⬇ Download PDF Report",
    #             data=pdf_bytes,
    #             file_name=(
    #                 f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    #             ),
    #             mime="application/pdf",
    #             use_container_width=True,
    #             key="dl_pdf_report",
    #         )
    #     except ImportError:
    #         st.warning(
    #             "⚠ fpdf2 not installed.  "
    #             "Run: `pip install fpdf2` to enable PDF export."
    #         )
    #     except Exception as _pdf_exc:
    #         st.error(f"PDF generation failed: {_pdf_exc}")


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
