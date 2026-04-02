"""
Load the Bike Store dataset from a local ZIP file into SQLite.
Place the Kaggle ZIP (archive_2.zip) into data/ then run this script.
Source: https://www.kaggle.com/datasets/dillonmyrick/bike-store-sample-database
"""
import os
import sys
import sqlite3
import csv
import io
from pathlib import Path
from zipfile import ZipFile

DATA_DIR = Path(__file__).resolve().parent.parent
BIKESTORE_DB = DATA_DIR / "bikestore.db"

ZIP_CANDIDATES = [
    "archive_2.zip",
    "archive (2).zip",
    "bike-store.zip",
    "bikestore.zip",
]

SCHEMA_SQL = """
-- Production schema
CREATE TABLE IF NOT EXISTS brands (
    brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    brand_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    model_year INTEGER NOT NULL,
    list_price REAL NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(brand_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Sales schema
CREATE TABLE IF NOT EXISTS stores (
    store_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    street TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT
);

CREATE TABLE IF NOT EXISTS staffs (
    staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    store_id INTEGER NOT NULL,
    manager_id INTEGER,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (manager_id) REFERENCES staffs(staff_id)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    email TEXT NOT NULL,
    street TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_status INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    required_date TEXT NOT NULL,
    shipped_date TEXT,
    store_id INTEGER NOT NULL,
    staff_id INTEGER NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (staff_id) REFERENCES staffs(staff_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    list_price REAL NOT NULL,
    discount REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (order_id, item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS stocks (
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (store_id, product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
"""

def find_zip():
    """Find the Bike Store ZIP file in the data directory."""
    for name in ZIP_CANDIDATES:
        p = DATA_DIR / name
        if p.exists():
            return p
    for p in DATA_DIR.glob("*.zip"):
        if "bike" in p.name.lower() or "store" in p.name.lower():
            return p
    return None


def create_database(zip_path: Path):
    """Create SQLite database from CSVs inside the ZIP."""
    if BIKESTORE_DB.exists():
        os.remove(BIKESTORE_DB)

    conn = sqlite3.connect(str(BIKESTORE_DB))
    cursor = conn.cursor()
    # Disable FK enforcement during bulk load (staffs has self-referential FK)
    cursor.execute("PRAGMA foreign_keys = OFF")
    cursor.executescript(SCHEMA_SQL)

    # Load order: respect FK constraints
    load_order = [
        ("brands.csv", "brands"),
        ("categories.csv", "categories"),
        ("stores.csv", "stores"),
        ("products.csv", "products"),
        ("staffs.csv", "staffs"),
        ("customers.csv", "customers"),
        ("orders.csv", "orders"),
        ("order_items.csv", "order_items"),
        ("stocks.csv", "stocks"),
    ]

    with ZipFile(zip_path, "r") as zf:
        csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
        print(f"  Found {len(csv_names)} CSV files in ZIP")

        def find_csv(target_name):
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

    print("\n  Final table counts:")
    for _, table_name in load_order:
        cnt = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"    {table_name}: {cnt:,} rows")

    conn.close()
    print(f"\n✅ Bike Store database created: {BIKESTORE_DB}")


def main():
    print("=== Bike Store Database Setup ===\n")

    zip_path = find_zip()
    if not zip_path:
        print("❌ No Bike Store ZIP file found in data/")
        print(f"   Please download from Kaggle and save to: {DATA_DIR}")
        print(f"   Expected filenames: {', '.join(ZIP_CANDIDATES)}")
        sys.exit(1)

    print(f"  Found ZIP: {zip_path.name}")
    print(f"\n[1/1] Creating SQLite database from ZIP...")
    create_database(zip_path)


if __name__ == "__main__":
    main()
