"""
=============================================================================
  DATABASE MODULE (MySQL)
  -----------------------
  Handles MySQL database connectivity, schema creation, data loading,
  and structured storage using SQLAlchemy + PyMySQL.
=============================================================================
"""

import os
import logging
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# ── Default Configuration ──────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("MYSQL_HOST", "localhost"),
    "port":     int(os.environ.get("MYSQL_PORT", "3306")),
    "user":     os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "analytics_db"),
}


def get_connection_url(include_db: bool = True) -> str:
    """Build the SQLAlchemy connection URL."""
    # URL-encode password to safely handle special characters like @, #, !, etc.
    encoded_password = quote_plus(DB_CONFIG['password'])
    base = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{encoded_password}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
    )
    if include_db:
        return f"{base}/{DB_CONFIG['database']}"
    return base


def create_database():
    """Create the analytics database if it does not exist."""
    try:
        engine = create_engine(get_connection_url(include_db=False))
        with engine.connect() as conn:
            conn.execute(text(
                f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            ))
            conn.commit()
        engine.dispose()
        logger.info(f"  ✓ Database '{DB_CONFIG['database']}' is ready")
        return True
    except OperationalError as e:
        logger.error(f"  ✗ Failed to connect to MySQL: {e}")
        logger.error(
            "    Ensure MySQL is running and credentials are correct.\n"
            "    Set environment variables: MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST"
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
    start_time = datetime.now()

    logger.info("=" * 60)
    logger.info("  DATABASE LOADING STARTED")
    logger.info("=" * 60)
    logger.info(f"  Target     : {DB_CONFIG['database']}.{table_name}")
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

    try:
        engine = get_engine()

        # Step 3: Load data using pandas to_sql (handles schema auto-creation)
        df_mysql.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi"
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

        engine.dispose()
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"  ✗ Database loading failed: {e}")
        return False


def add_indexes(table_name: str = "sales_data"):
    """Add performance indexes to the MySQL table for faster querying."""
    index_columns = [
        "order_date", "category", "sub_category", "segment",
        "region", "state", "city", "ship_mode", "customer_id"
    ]

    try:
        engine = get_engine()
        inspector = inspect(engine)
        existing_cols = [c["name"] for c in inspector.get_columns(table_name)]

        with engine.connect() as conn:
            for col in index_columns:
                if col in existing_cols:
                    idx_name = f"idx_{table_name}_{col}"
                    try:
                        conn.execute(text(
                            f"CREATE INDEX `{idx_name}` ON `{table_name}` (`{col}`(191))"
                            if col in ["customer_id", "order_date"]
                            else f"CREATE INDEX `{idx_name}` ON `{table_name}` (`{col}`)"
                        ))
                        logger.info(f"    ├── Created index: {idx_name}")
                    except Exception:
                        pass  # Index may already exist
            conn.commit()
        engine.dispose()
        logger.info("  ✓ Performance indexes added")
    except Exception as e:
        logger.warning(f"  ⚠ Could not add indexes: {e}")


def execute_query(query: str) -> pd.DataFrame:
    """Execute a SQL query and return results as a DataFrame."""
    try:
        engine = get_engine()
        df = pd.read_sql(query, engine)
        engine.dispose()
        return df
    except Exception as e:
        logger.error(f"  ✗ Query execution failed: {e}")
        return pd.DataFrame()


def get_table_info(table_name: str = "sales_data") -> dict:
    """Get metadata about the MySQL table."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            row_count = conn.execute(
                text(f"SELECT COUNT(*) FROM `{table_name}`")
            ).fetchone()[0]

        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        engine.dispose()

        return {
            "table_name": table_name,
            "database": DB_CONFIG["database"],
            "row_count": row_count,
            "column_count": len(columns),
            "columns": [
                {"name": c["name"], "type": str(c["type"])} for c in columns
            ],
        }
    except Exception as e:
        logger.error(f"  ✗ Could not retrieve table info: {e}")
        return {}


# ── Standalone Execution ──────────────────────────────────────────────────
if __name__ == "__main__":
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
