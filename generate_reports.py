"""
Standalone report generation from the processed CSV — no MySQL required.

This script is a thin wrapper around the shared query registry in
src/query.py. All analytical logic lives there (via pandas_fn lambdas),
making this a single call that stays in sync with the SQL path automatically.

Usage:
    python generate_reports.py
"""

import os
import sys
import logging

# ── Ensure src/ is importable ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

import pandas as pd
from query import run_all_queries_pandas, export_reports, print_report_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Paths ─────────────────────────────────────────────────────────────────
INPUT_PATH = os.path.join(BASE_DIR, "data", "processed", "processed_data.csv")
OUT_DIR    = os.path.join(BASE_DIR, "data", "processed")

if not os.path.exists(INPUT_PATH):
    print(f"❌ Processed data not found at: {INPUT_PATH}")
    print("   Please run the pipeline first:  python src/run_pipeline.py")
    sys.exit(1)

# ── Load & run ────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_PATH)
results = run_all_queries_pandas(df)
export_reports(results, OUT_DIR)
print_report_summary(results)
