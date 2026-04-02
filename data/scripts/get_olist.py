"""
Load the Olist Brazilian E-Commerce dataset from a local ZIP file into SQLite.
Place the Kaggle ZIP (archive.zip) into data/ then run this script.
Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
"""
import os
import sys
import sqlite3
import csv
import io
from pathlib import Path
from zipfile import ZipFile

DATA_DIR = Path(__file__).resolve().parent.parent
OLIST_DB = DATA_DIR / "olist.db"

# The script will look for any of these filenames in data/
ZIP_CANDIDATES = [
    "archive.zip",
    "brazilian-ecommerce.zip",
    "olist.zip",
    "olist-brazilian-ecommerce.zip",
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE IF NOT EXISTS sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght REAL,
    product_description_lenght REAL,
    product_photos_qty REAL,
    product_weight_g REAL,
    product_length_cm REAL,
    product_height_cm REAL,
    product_width_cm REAL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TEXT,
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT,
    order_item_id INTEGER,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TEXT,
    price REAL,
    freight_value REAL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

CREATE TABLE IF NOT EXISTS order_payments (
    order_id TEXT,
    payment_sequential INTEGER,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value REAL,
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS order_reviews (
    review_id TEXT,
    order_id TEXT,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT,
    review_answer_timestamp TEXT,
    PRIMARY KEY (review_id, order_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);
"""

def find_zip():
    """Find the Olist ZIP file in the data directory."""
    for name in ZIP_CANDIDATES:
        p = DATA_DIR / name
        if p.exists():
            return p
    # Also check for any zip file containing 'olist' in its name
    for p in DATA_DIR.glob("*.zip"):
        if "olist" in p.name.lower() or "ecommerce" in p.name.lower() or p.name == "archive.zip":
            return p
    return None


def create_database(zip_path: Path):
    """Create SQLite database from CSVs inside the ZIP."""
    if OLIST_DB.exists():
        os.remove(OLIST_DB)

    conn = sqlite3.connect(str(OLIST_DB))
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_SQL)

    # Load order: respect FK constraints
    load_order = [
        ("olist_customers_dataset.csv", "customers"),
        ("olist_sellers_dataset.csv", "sellers"),
        ("olist_products_dataset.csv", "products"),
        ("product_category_name_translation.csv", "category_translation"),
        ("olist_orders_dataset.csv", "orders"),
        ("olist_order_items_dataset.csv", "order_items"),
        ("olist_order_payments_dataset.csv", "order_payments"),
        ("olist_order_reviews_dataset.csv", "order_reviews"),
    ]

    with ZipFile(zip_path, "r") as zf:
        # List CSV files in the ZIP (may be nested in a folder)
        csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
        print(f"  Found {len(csv_names)} CSV files in ZIP")

        def find_csv(target_name):
            """Find a CSV in the ZIP, handling nested folders."""
            for n in csv_names:
                if n.endswith(target_name) or n.split("/")[-1] == target_name:
                    return n
            return None

        for csv_filename, table_name in load_order:
            zip_entry = find_csv(csv_filename)
            if not zip_entry:
                print(f"  [skip] {csv_filename} not found in ZIP")
                continue

            print(f"  Loading {csv_filename} -> {table_name}...")
            with zf.open(zip_entry) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8")
                reader = csv.DictReader(text)
                headers = reader.fieldnames
                if not headers:
                    continue

                placeholders = ", ".join(["?"] * len(headers))
                cols = ", ".join(headers)
                sql = f"INSERT OR IGNORE INTO {table_name} ({cols}) VALUES ({placeholders})"

                batch = []
                count = 0
                for row in reader:
                    vals = [row.get(h, None) for h in headers]
                    batch.append(vals)
                    count += 1
                    if len(batch) >= 5000:
                        cursor.executemany(sql, batch)
                        batch = []
                if batch:
                    cursor.executemany(sql, batch)
                print(f"    -> {count} rows")

    conn.commit()

    # Print final stats
    print("\n  Final table counts:")
    for _, table_name in load_order:
        cnt = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"    {table_name}: {cnt:,} rows")

    conn.close()
    print(f"\n✅ Olist database created: {OLIST_DB}")


def main():
    print("=== Olist Brazilian E-Commerce Dataset Setup ===\n")
    
    zip_path = find_zip()
    if not zip_path:
        print("❌ No Olist ZIP file found in data/")
        print(f"   Please download from: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
        print(f"   Save the ZIP to: {DATA_DIR}")
        print(f"   Expected filenames: {', '.join(ZIP_CANDIDATES)}")
        sys.exit(1)

    print(f"  Found ZIP: {zip_path.name}")
    print(f"\n[1/1] Creating SQLite database from ZIP...")
    create_database(zip_path)


if __name__ == "__main__":
    main()
