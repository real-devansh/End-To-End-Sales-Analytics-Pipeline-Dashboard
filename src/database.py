"""
=============================================================================
  DATABASE MODULE (MySQL)
  -----------------------
  Handles MySQL database connectivity, schema creation, data loading,
  and structured storage using SQLAlchemy + PyMySQL.

  Credentials are loaded exclusively from environment variables (via a
  .env file). No credentials are ever hardcoded. See .env.example.
=============================================================================
"""

import os
import re
import logging
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

# ── Load .env file if present (does nothing if already set in environment) ─
load_dotenv()

logger = logging.getLogger(__name__)


# ── Configuration — strictly from environment variables ────────────────────
def _get_db_config() -> dict:
    """
    Build the DB config dict from environment variables at call time.
    This avoids module-level caching so tests can inject env vars freely.
    """
    return {
        "host":     os.getenv("MYSQL_HOST", "localhost"),
        "port":     int(os.getenv("MYSQL_PORT", "3306")),
        "user":     os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "analytics_db"),
    }


def _mask_url(url_or_error: str) -> str:
    """
    Scrub any embedded password from a connection URL string so it is
    safe to log. Replaces the password segment with ***.

    e.g.  mysql+pymysql://root:s3cr3t@localhost/db
       →  mysql+pymysql://root:***@localhost/db
    """
    return re.sub(r":[^@:/]+@", ":***@", str(url_or_error))


def get_connection_url(include_db: bool = True) -> str:
    """Build the SQLAlchemy connection URL from current env config."""
    cfg = _get_db_config()
    encoded_password = quote_plus(cfg["password"])
    base = (
        f"mysql+pymysql://{cfg['user']}:{encoded_password}"
        f"@{cfg['host']}:{cfg['port']}"
    )
    if include_db:
        return f"{base}/{cfg['database']}"
    return base


def create_database() -> bool:
    """Create the analytics database if it does not exist."""
    cfg = _get_db_config()
    try:
        engine = create_engine(get_connection_url(include_db=False))
        with engine.connect() as conn:
            conn.execute(text(
                f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            ))
            conn.commit()
        engine.dispose()
        logger.info(f"  ✓ Database '{cfg['database']}' is ready")
        return True
    except OperationalError as e:
        # Mask password before logging to prevent credential leakage
        logger.error(f"  ✗ Failed to connect to MySQL: {_mask_url(str(e))}")
        logger.error(
            "    Ensure MySQL is running and credentials are set correctly.\n"
            "    Required env vars: MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, "
            "MYSQL_DATABASE (see .env.example)"
        )
        return False


def get_engine():
    """Get a SQLAlchemy engine connected to the analytics database."""
    return create_engine(get_connection_url(), echo=False)


def load_to_mysql(df: pd.DataFrame, table_name: str = "sales_data") -> bool:
    """
    Load a processed DataFrame into a MySQL table.

    Creates the table if it doesn't exist and replaces any existing data.
    Automatically maps pandas dtypes to appropriate MySQL column types.

    Parameters
    ----------
    df : pd.DataFrame
        The processed dataframe to store.
    table_name : str
        Target table name in MySQL.

    Returns
    -------
    bool
        True if data was loaded successfully, False otherwise.
    """
    cfg = _get_db_config()
    start_time = datetime.now()

    logger.info("=" * 60)
    logger.info("  DATABASE LOADING STARTED")
    logger.info("=" * 60)
    logger.info(f"  Target     : {cfg['database']}.{table_name}")
    logger.info(f"  Records    : {len(df):,}")
    logger.info(f"  Columns    : {df.shape[1]}")
    logger.info("-" * 60)

    # Step 1: Ensure database exists
    if not create_database():
        return False

    # Step 2: Prepare DataFrame for MySQL compatibility
    df_mysql = df.copy()

    # Convert datetime columns to string for MySQL compatibility
    for col in df_mysql.select_dtypes(include=["datetime64"]).columns:
        df_mysql[col] = df_mysql[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    engine = get_engine()
    try:
        # Step 3: Load data using pandas to_sql (handles schema auto-creation)
        df_mysql.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi",
        )

        # Step 4: Verify the load
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM `{table_name}`"))
            row_count = result.fetchone()[0]

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"  ✓ Loaded {row_count:,} records into '{table_name}'")
        logger.info(f"  ✓ Database load completed in {elapsed:.2f}s")

        # Log table structure
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        logger.info("-" * 60)
        logger.info("  Table Schema:")
        for col_info in columns:
            logger.info(
                f"    ├── {col_info['name']:25s} │ {str(col_info['type']):20s}"
            )

        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"  ✗ Database loading failed: {_mask_url(str(e))}")
        return False

    finally:
        # Guarantee the connection pool is released even if an exception occurs
        engine.dispose()


def add_indexes(table_name: str = "sales_data"):
    """Add performance indexes to the MySQL table for faster querying."""
    # Columns that benefit from an index; date/id use prefix lengths only
    # for VARCHAR-typed columns — detected at runtime via inspector.
    index_columns = [
        "order_date", "category", "sub_category", "segment",
        "region", "state", "city", "ship_mode", "customer_id",
    ]

    engine = get_engine()
    try:
        inspector = inspect(engine)
        existing_cols = {c["name"]: c for c in inspector.get_columns(table_name)}

        with engine.connect() as conn:
            for col in index_columns:
                if col not in existing_cols:
                    continue

                col_type = str(existing_cols[col]["type"]).upper()
                idx_name = f"idx_{table_name}_{col}"

                # Only apply prefix length for string types (TEXT / VARCHAR)
                needs_prefix = any(t in col_type for t in ("TEXT", "VARCHAR", "CHAR"))
                ddl = (
                    f"CREATE INDEX `{idx_name}` ON `{table_name}` (`{col}`(191))"
                    if needs_prefix
                    else f"CREATE INDEX `{idx_name}` ON `{table_name}` (`{col}`)"
                )

                try:
                    conn.execute(text(ddl))
                    logger.info(f"    ├── Created index: {idx_name}")
                except Exception:
                    pass  # Index may already exist

            conn.commit()
        logger.info("  ✓ Performance indexes added")
    except Exception as e:
        logger.warning(f"  ⚠ Could not add indexes: {e}")
    finally:
        engine.dispose()


def get_table_info(table_name: str = "sales_data") -> dict:
    """Get metadata about the MySQL table."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            row_count = conn.execute(
                text(f"SELECT COUNT(*) FROM `{table_name}`")
            ).fetchone()[0]

        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)

        return {
            "table_name":   table_name,
            "database":     _get_db_config()["database"],
            "row_count":    row_count,
            "column_count": len(columns),
            "columns": [
                {"name": c["name"], "type": str(c["type"])} for c in columns
            ],
        }
    except Exception as e:
        logger.error(f"  ✗ Could not retrieve table info: {_mask_url(str(e))}")
        return {}
    finally:
        engine.dispose()


# ── Standalone Execution ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from ingestion import discover_and_load
    from cleaning import clean_and_transform

    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

    df = discover_and_load(raw_dir)
    df = clean_and_transform(df)
    success = load_to_mysql(df)

    if success:
        add_indexes()
        info = get_table_info()
        print(f"\n✓ MySQL table '{info['table_name']}' ready with {info['row_count']:,} rows")
