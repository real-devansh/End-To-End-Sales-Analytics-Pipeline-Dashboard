"""
=============================================================================
  MASTER PIPELINE ORCHESTRATOR
  ----------------------------
  Runs the complete ETL pipeline end-to-end:
    1. Ingest raw data
    2. Clean & transform
    3. Save processed data
    4. Load into MySQL
    5. Run analytical queries
    6. Export reports
=============================================================================
"""

import os
import sys
import logging
import time
import io
from datetime import datetime

# ── Fix Windows console encoding ──────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Configure Logging ──────────────────────────────────────────────────────
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        stream_handler,
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "..", "pipeline.log"),
            mode="w", encoding="utf-8"
        )
    ]
)
logger = logging.getLogger(__name__)

# ── Add src to path ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from ingestion import discover_and_load
from cleaning import clean_and_transform, save_processed_data
from database import load_to_mysql, add_indexes, get_engine
from query import run_all_queries, export_reports, print_report_summary


def run_pipeline():
    """
    Execute the complete data analytics pipeline.

    Stages:
        1. DATA INGESTION    — Load raw data from data/raw/
        2. DATA CLEANING     — Clean, standardize, and transform
        3. DATA STORAGE      — Save processed CSV to data/processed/
        4. DATABASE LOADING  — Load into MySQL (analytics_db.sales_data)
        5. SQL ANALYTICS     — Run 15+ analytical queries
        6. REPORT EXPORT     — Export to Excel + CSV reports
    """
    pipeline_start = datetime.now()

    # ── Paths ──────────────────────────────────────────────────────────────
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    raw_dir = os.path.join(base_dir, "data", "raw")
    processed_dir = os.path.join(base_dir, "data", "processed")

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  END-TO-END DATA ANALYTICS PIPELINE".center(68) + "║")
    print("║" + f"  Started: {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    stages = {}

    # ══════════════════════════════════════════════════════════════════════
    #  STAGE 1: DATA INGESTION
    # ══════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    logger.info("▶ STAGE 1/6: DATA INGESTION")
    try:
        df_raw = discover_and_load(raw_dir)
        stages["ingestion"] = {
            "status": "✓ SUCCESS",
            "rows": df_raw.shape[0],
            "cols": df_raw.shape[1],
            "time": round(time.time() - stage_start, 2),
        }
    except Exception as e:
        logger.error(f"  Pipeline failed at INGESTION: {e}")
        return False
    print()

    # ══════════════════════════════════════════════════════════════════════
    #  STAGE 2: DATA CLEANING & TRANSFORMATION
    # ══════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    logger.info("▶ STAGE 2/6: DATA CLEANING & TRANSFORMATION")
    try:
        df_clean = clean_and_transform(df_raw)
        stages["cleaning"] = {
            "status": "✓ SUCCESS",
            "rows": df_clean.shape[0],
            "cols": df_clean.shape[1],
            "time": round(time.time() - stage_start, 2),
        }
    except Exception as e:
        logger.error(f"  Pipeline failed at CLEANING: {e}")
        return False
    print()

    # ══════════════════════════════════════════════════════════════════════
    #  STAGE 3: SAVE PROCESSED DATA
    # ══════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    logger.info("▶ STAGE 3/6: SAVING PROCESSED DATA")
    try:
        save_processed_data(df_clean, processed_dir)
        stages["save"] = {
            "status": "✓ SUCCESS",
            "time": round(time.time() - stage_start, 2),
        }
    except Exception as e:
        logger.error(f"  Pipeline failed at SAVE: {e}")
        return False
    print()

    # ══════════════════════════════════════════════════════════════════════
    #  STAGE 4: LOAD INTO MYSQL
    # ══════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    logger.info("▶ STAGE 4/6: LOADING INTO MYSQL")
    try:
        success = load_to_mysql(df_clean)
        if success:
            add_indexes()
            stages["database"] = {
                "status": "✓ SUCCESS",
                "time": round(time.time() - stage_start, 2),
            }
        else:
            stages["database"] = {
                "status": "⚠ SKIPPED (MySQL unavailable)",
                "time": round(time.time() - stage_start, 2),
            }
            logger.warning(
                "  MySQL loading skipped — pipeline will continue without it.\n"
                "  Set MYSQL_PASSWORD env var or check MySQL service."
            )
    except Exception as e:
        logger.warning(f"  MySQL loading failed (non-fatal): {e}")
        stages["database"] = {
            "status": "⚠ SKIPPED",
            "time": round(time.time() - stage_start, 2),
        }
    print()

    # ══════════════════════════════════════════════════════════════════════
    #  STAGE 5: SQL ANALYTICS
    # ══════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    logger.info("▶ STAGE 5/6: RUNNING SQL ANALYTICS")
    results = {}
    if stages.get("database", {}).get("status", "").startswith("✓"):
        try:
            engine = get_engine()
            results = run_all_queries(engine)
            engine.dispose()
            stages["analytics"] = {
                "status": "✓ SUCCESS",
                "queries": len(results),
                "time": round(time.time() - stage_start, 2),
            }
        except Exception as e:
            logger.warning(f"  Analytics failed (non-fatal): {e}")
            stages["analytics"] = {"status": "⚠ SKIPPED", "time": 0}
    else:
        logger.info("  Skipping SQL analytics (MySQL not available)")
        stages["analytics"] = {"status": "⚠ SKIPPED (no DB)", "time": 0}
    print()

    # ══════════════════════════════════════════════════════════════════════
    #  STAGE 6: EXPORT REPORTS
    # ══════════════════════════════════════════════════════════════════════
    stage_start = time.time()
    logger.info("▶ STAGE 6/6: EXPORTING REPORTS")
    if results:
        try:
            export_reports(results, processed_dir)
            stages["export"] = {
                "status": "✓ SUCCESS",
                "time": round(time.time() - stage_start, 2),
            }
        except Exception as e:
            logger.warning(f"  Report export failed (non-fatal): {e}")
            stages["export"] = {"status": "⚠ SKIPPED", "time": 0}
    else:
        logger.info("  Skipping report export (no analytics results)")
        stages["export"] = {"status": "⚠ SKIPPED", "time": 0}

    # ══════════════════════════════════════════════════════════════════════
    #  PIPELINE SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    total_time = (datetime.now() - pipeline_start).total_seconds()

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  PIPELINE EXECUTION SUMMARY".center(68) + "║")
    print("╠" + "═" * 68 + "╣")

    stage_names = {
        "ingestion": "Data Ingestion",
        "cleaning": "Cleaning & Transformation",
        "save": "Save Processed Data",
        "database": "MySQL Database Loading",
        "analytics": "SQL Analytics",
        "export": "Report Export",
    }
    for key, name in stage_names.items():
        info = stages.get(key, {"status": "—", "time": 0})
        status = info.get("status", "—")
        elapsed = info.get("time", 0)
        line = f"  {name:35s} │ {status:25s} │ {elapsed:.2f}s"
        print("║" + line.ljust(68) + "║")

    print("╠" + "═" * 68 + "╣")
    print("║" + f"  Total Pipeline Time: {total_time:.2f}s".ljust(68) + "║")
    print("╚" + "═" * 68 + "╝")

    # ── Print report highlights if available ───────────────────────────────
    if results:
        print_report_summary(results)

    return True


# ── Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
