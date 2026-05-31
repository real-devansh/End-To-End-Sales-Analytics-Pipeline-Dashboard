# 📊 End-to-End Data Analytics Pipeline

A complete, automated data analytics pipeline built with **Python** and **MySQL**, featuring a premium **Streamlit** dashboard for interactive analysis.

---

## 🏗️ Architecture

```
/
├── data/
│   ├── raw/                    # Original datasets (CSV, Excel, JSON)
│   │   └── train.csv           # Superstore Sales dataset (9,800 records)
│   └── processed/              # Cleaned & transformed output
│       ├── processed_data.csv
│       ├── analytics_report.xlsx
│       └── csv_reports/        # Individual query results
├── src/
│   ├── __init__.py
│   ├── ingestion.py            # Data ingestion layer
│   ├── cleaning.py             # Cleaning & transformation layer
│   ├── database.py             # MySQL database layer (SQLAlchemy)
│   ├── query.py                # 15+ SQL analytical queries
│   └── run_pipeline.py         # Master pipeline orchestrator
├── dashboard.py                # Premium Streamlit dashboard
├── requirements.txt            # Python dependencies
├── pipeline.log                # Execution log
└── README.md
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Pipeline
```bash
python src/run_pipeline.py
```

This executes the full ETL pipeline:
1. **Ingest** → Auto-detect and load raw data
2. **Clean** → Standardize, deduplicate, handle missing values
3. **Transform** → Date parsing, feature engineering
4. **Store** → Save processed CSV + load into MySQL
5. **Analyze** → Execute 15+ SQL analytical queries
6. **Export** → Generate Excel and CSV reports

### 3. Launch Dashboard
```bash
streamlit run dashboard.py
```

---


## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| **📊 Overview** | KPI cards, revenue trends, category/region/segment analysis |
| **🔍 Exploratory** | Distributions, correlations, outlier detection, data quality ||
| **⚙️ Pipeline** | Architecture, data lineage, MySQL status, execution log |

---

## 🛠️ Tech Stack

- **Python 3.10** — Core processing
- **Pandas / NumPy** — Data manipulation
- **Plotly / Seaborn / Matplotlib** — Visualization
- **Streamlit** — Interactive web dashboard

---

## 📈 Key Analytics

- Revenue trends (monthly, quarterly, yearly)
- Category & sub-category performance
- Customer segmentation & top customers
- Geographic analysis (region, state, city)
- Shipping mode efficiency
- Sales tier classification
- Day-of-week patterns
- Year-over-year growth analysis
