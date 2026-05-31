"""
=============================================================================
  DATA INGESTION MODULE
  ---------------------
  Handles loading raw datasets from various formats (CSV, Excel, JSON).
  Validates file integrity, logs metadata, and returns a clean DataFrame.
=============================================================================
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

# ── Configure Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ── Supported File Formats ─────────────────────────────────────────────────
SUPPORTED_FORMATS = {
    ".csv":   "CSV",
    ".xlsx":  "Excel (xlsx)",
    ".xls":   "Excel (xls)",
    ".json":  "JSON",
    ".parquet": "Parquet",
}


def detect_file_format(filepath: str) -> str:
    """Detect and validate the file format based on extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format: '{ext}'. "
            f"Supported formats: {list(SUPPORTED_FORMATS.keys())}"
        )
    return ext


def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Load a dataset from the given filepath.

    Automatically detects file format (CSV, Excel, JSON, Parquet) and
    reads the data into a pandas DataFrame with appropriate settings.

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the raw data file.

    Returns
    -------
    pd.DataFrame
        The loaded dataset.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file format is not supported.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    file_ext = detect_file_format(filepath)
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

    logger.info("=" * 60)
    logger.info("  DATA INGESTION STARTED")
    logger.info("=" * 60)
    logger.info(f"  File       : {os.path.basename(filepath)}")
    logger.info(f"  Format     : {SUPPORTED_FORMATS[file_ext]}")
    logger.info(f"  Size       : {file_size_mb:.2f} MB")
    logger.info(f"  Timestamp  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("-" * 60)

    # ── Read based on format ───────────────────────────────────────────────
    start_time = datetime.now()

    if file_ext == ".csv":
        df = pd.read_csv(filepath, encoding="utf-8")
    elif file_ext in (".xlsx", ".xls"):
        df = pd.read_excel(filepath)
    elif file_ext == ".json":
        df = pd.read_json(filepath)
    elif file_ext == ".parquet":
        df = pd.read_parquet(filepath)

    elapsed = (datetime.now() - start_time).total_seconds()

    # ── Log Dataset Metadata ──────────────────────────────────────────────
    logger.info(f"  ✓ Dataset loaded successfully in {elapsed:.2f}s")
    logger.info(f"  Rows       : {df.shape[0]:,}")
    logger.info(f"  Columns    : {df.shape[1]}")
    logger.info(f"  Memory     : {df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")
    logger.info("-" * 60)
    logger.info("  Column Details:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        null_pct = (df[col].isna().sum() / len(df)) * 100
        logger.info(
            f"    ├── {col:25s} │ {str(df[col].dtype):10s} │ "
            f"Non-null: {non_null:,} │ Null: {null_pct:.1f}%"
        )
    logger.info("=" * 60)

    return df


def discover_and_load(data_dir: str) -> pd.DataFrame:
    """
    Auto-discover the first valid dataset in a directory and load it.

    Parameters
    ----------
    data_dir : str
        Path to the directory containing raw data files.

    Returns
    -------
    pd.DataFrame
        The loaded dataset.
    """
    if not os.path.isdir(data_dir):
        raise NotADirectoryError(f"Directory not found: {data_dir}")

    for filename in sorted(os.listdir(data_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in SUPPORTED_FORMATS:
            filepath = os.path.join(data_dir, filename)
            logger.info(f"  Auto-discovered dataset: {filename}")
            return load_dataset(filepath)

    raise FileNotFoundError(
        f"No supported dataset found in {data_dir}. "
        f"Supported formats: {list(SUPPORTED_FORMATS.keys())}"
    )


# ── Standalone Execution ──────────────────────────────────────────────────
if __name__ == "__main__":
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    df = discover_and_load(raw_dir)
    print(f"\n✓ Successfully ingested {df.shape[0]:,} rows × {df.shape[1]} columns")
