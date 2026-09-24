"""
=============================================================================
  DATA CLEANING & TRANSFORMATION MODULE
  --------------------------------------
  Handles data quality issues: missing values, type conversions, column
  standardization, outlier detection, and feature engineering.
=============================================================================
"""

import os
import re
import logging
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to snake_case format.

    Removes special characters, replaces spaces/hyphens with underscores,
    and converts everything to lowercase for consistency.
    """
    new_cols = {}
    for col in df.columns:
        clean = col.strip()
        clean = clean.replace(" ", "_").replace("-", "_").replace("/", "_")
        clean = "".join(c for c in clean if c.isalnum() or c == "_")
        clean = clean.lower()
        # Collapse multiple underscores
        while "__" in clean:
            clean = clean.replace("__", "_")
        clean = clean.strip("_")
        new_cols[col] = clean

    df = df.rename(columns=new_cols)
    logger.info(f"  ✓ Standardized {len(new_cols)} column names to snake_case")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Intelligently handle missing values based on column data type and
    distribution characteristics.

    Strategy:
    - Numeric columns with <5% nulls: fill with median
    - Numeric columns with >=5% nulls: fill with median + add indicator flag
    - Categorical columns: fill with mode or 'Unknown'
    - Date columns: leave as NaT (logged)
    """
    total_nulls_before = df.isnull().sum().sum()

    if total_nulls_before == 0:
        logger.info("  ✓ No missing values detected — dataset is complete")
        return df

    logger.info(f"  ⚠ Found {total_nulls_before:,} total missing values")

    for col in df.columns:
        null_count = df[col].isnull().sum()
        if null_count == 0:
            continue

        null_pct = (null_count / len(df)) * 100

        if pd.api.types.is_numeric_dtype(df[col]):
            median_val = df[col].median()

            # ── FIX: Capture the missing mask BEFORE fillna so the
            # indicator column correctly reflects the original nulls.
            if null_pct >= 5:
                flag_col = f"{col}_was_missing"
                df[flag_col] = df[col].isnull().astype(int)  # NaNs still present here
                strategy = f"median ({median_val:.2f}) + indicator flag"
            else:
                strategy = f"median ({median_val:.2f})"

            df[col] = df[col].fillna(median_val)  # NaNs removed AFTER flag is set

        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            strategy = "left as NaT"
        else:
            mode_val = df[col].mode(dropna=True)
            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val[0])
                strategy = f"mode ('{mode_val[0]}')"
            else:
                df[col] = df[col].fillna("Unknown")
                strategy = "filled with 'Unknown'"

        logger.info(
            f"    ├── {col:25s} │ Nulls: {null_count:,} ({null_pct:.1f}%) │ "
            f"Strategy: {strategy}"
        )

    total_nulls_after = df.isnull().sum().sum()
    logger.info(
        f"  ✓ Missing values reduced: {total_nulls_before:,} → {total_nulls_after:,}"
    )
    return df


def _infer_dayfirst(series: pd.Series) -> bool | None:
    """
    Heuristic: sample up to 50 non-null string values and inspect the
    leading numeric component of each date-like token.

    Returns
    -------
    True  — leading digit > 12 in at least one sample → must be DD/MM/YYYY
    False — second digit > 12 in at least one sample → must be MM/DD/YYYY or ISO
    None  — ambiguous; caller should default to False and log a warning
    """
    samples = series.dropna().astype(str).head(50)
    day_first_evidence = 0
    month_first_evidence = 0

    for val in samples:
        match = re.match(r"(\d{1,2})[\-\/\.](\d{1,2})", val)
        if match:
            first_num = int(match.group(1))
            second_num = int(match.group(2))
            if first_num > 12:
                # First component can't be a month → must be a day
                day_first_evidence += 1
            elif second_num > 12:
                # Second component can't be a month → first must be a month (US)
                month_first_evidence += 1

    if day_first_evidence > 0 and month_first_evidence == 0:
        return True   # Unambiguously DD/MM/YYYY
    elif month_first_evidence > 0 and day_first_evidence == 0:
        return False  # Unambiguously MM/DD/YYYY
    else:
        return None   # Ambiguous — caller decides


def convert_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect and convert date-like columns to proper datetime format.
    Dynamically infers date order (dayfirst) from the data instead of
    hardcoding it, preventing silent misparsing of US-format dates.
    """
    date_keywords = ["date", "time", "timestamp", "created", "updated", "dt"]
    converted = 0

    for col in df.columns:
        is_date_col = any(kw in col.lower() for kw in date_keywords)

        if is_date_col and df[col].dtype == "object":
            try:
                dayfirst = _infer_dayfirst(df[col])

                if dayfirst is None:
                    logger.warning(
                        f"    ⚠ '{col}': Cannot determine date order from sampled data. "
                        f"Defaulting to dayfirst=False (ISO / US MM/DD/YYYY format). "
                        f"Set SALES_DAYFIRST=true env var to override globally."
                    )
                    dayfirst = os.environ.get("SALES_DAYFIRST", "false").lower() == "true"

                df[col] = pd.to_datetime(df[col], dayfirst=dayfirst, format="mixed")
                converted += 1
                fmt_label = "DD/MM/YYYY" if dayfirst else "MM/DD/YYYY or ISO"
                logger.info(f"    ├── Converted '{col}' to datetime (detected format: {fmt_label})")

            except (ValueError, TypeError) as exc:
                logger.warning(f"    ├── Could not parse '{col}' as datetime: {exc}")

    if converted > 0:
        logger.info(f"  ✓ Converted {converted} column(s) to datetime")
    else:
        logger.info("  ✓ No date columns detected for conversion")

    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows and log the result."""
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed > 0:
        logger.info(f"  ✓ Removed {removed:,} duplicate rows ({before:,} → {len(df):,})")
    else:
        logger.info("  ✓ No duplicate rows found")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived features specific to the Superstore sales dataset.

    New columns created:
    - order_year, order_month, order_quarter, order_day_of_week
    - shipping_days (Ship Date - Order Date)
    - sales_category (Low / Medium / High / Premium based on quartiles)
    """
    new_features = 0

    # ── Date-based features ────────────────────────────────────────────────
    if "order_date" in df.columns and pd.api.types.is_datetime64_any_dtype(df["order_date"]):
        df["order_year"] = df["order_date"].dt.year
        df["order_month"] = df["order_date"].dt.month
        df["order_month_name"] = df["order_date"].dt.strftime("%B")
        df["order_quarter"] = df["order_date"].dt.quarter
        df["order_day_of_week"] = df["order_date"].dt.day_name()
        new_features += 5
        logger.info("    ├── Created: order_year, order_month, order_month_name, order_quarter, order_day_of_week")

    # ── Shipping duration ──────────────────────────────────────────────────
    if (
        "order_date" in df.columns
        and "ship_date" in df.columns
        and pd.api.types.is_datetime64_any_dtype(df["order_date"])
        and pd.api.types.is_datetime64_any_dtype(df["ship_date"])
    ):
        df["shipping_days"] = (df["ship_date"] - df["order_date"]).dt.days
        new_features += 1
        logger.info(
            f"    ├── Created: shipping_days "
            f"(avg: {df['shipping_days'].mean():.1f} days)"
        )

    # ── Sales tier classification ──────────────────────────────────────────
    if "sales" in df.columns:
        q1 = df["sales"].quantile(0.25)
        q2 = df["sales"].quantile(0.50)
        q3 = df["sales"].quantile(0.75)
        conditions = [
            df["sales"] <= q1,
            (df["sales"] > q1) & (df["sales"] <= q2),
            (df["sales"] > q2) & (df["sales"] <= q3),
            df["sales"] > q3,
        ]
        labels = ["Low", "Medium", "High", "Premium"]
        df["sales_tier"] = np.select(conditions, labels, default="Unknown")
        new_features += 1
        logger.info(
            f"    ├── Created: sales_tier "
            f"(Low≤{q1:.0f}, Med≤{q2:.0f}, High≤{q3:.0f}, Premium>{q3:.0f})"
        )

    if new_features > 0:
        logger.info(f"  ✓ Engineered {new_features} new feature(s)")
    else:
        logger.info("  ✓ No feature engineering opportunities detected")

    return df


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Master cleaning function — executes the full cleaning pipeline in order.

    Pipeline stages:
    1. Standardize column names
    2. Remove duplicates
    3. Handle missing values
    4. Convert date columns
    5. Engineer new features

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe from ingestion.

    Returns
    -------
    pd.DataFrame
        Cleaned and transformed dataframe.
    """
    start_time = datetime.now()

    logger.info("=" * 60)
    logger.info("  DATA CLEANING & TRANSFORMATION STARTED")
    logger.info("=" * 60)
    logger.info(f"  Input shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info("-" * 60)

    # Stage 1: Standardize column names
    logger.info("  [1/5] Standardizing column names...")
    df = standardize_columns(df)

    # Stage 2: Remove duplicates
    logger.info("  [2/5] Removing duplicates...")
    df = remove_duplicates(df)

    # Stage 3: Handle missing values
    logger.info("  [3/5] Handling missing values...")
    df = handle_missing_values(df)

    # Stage 4: Convert date columns
    logger.info("  [4/5] Converting date columns...")
    df = convert_date_columns(df)

    # Stage 5: Engineer features
    logger.info("  [5/5] Engineering features...")
    df = engineer_features(df)

    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info("-" * 60)
    logger.info(f"  Output shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info(f"  ✓ Cleaning completed in {elapsed:.2f}s")
    logger.info("=" * 60)

    return df


def save_processed_data(df: pd.DataFrame, output_dir: str, filename: str = "processed_data.csv"):
    """Save the processed DataFrame to the output directory."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    df.to_csv(output_path, index=False)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"  ✓ Processed data saved to: {output_path} ({size_mb:.2f} MB)")
    return output_path


# ── Standalone Execution ──────────────────────────────────────────────────
if __name__ == "__main__":
    from ingestion import discover_and_load

    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

    df = discover_and_load(raw_dir)
    df = clean_and_transform(df)
    save_processed_data(df, processed_dir)
    print(f"\n✓ Cleaning complete: {df.shape[0]:,} rows × {df.shape[1]} columns")
