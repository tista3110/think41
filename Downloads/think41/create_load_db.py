import sqlite3
import csv
import os

DB_NAME = 'ecommerce.db'
USERS_CSV = os.path.join('archive', 'archive', 'users.csv')
ORDERS_CSV = os.path.join('archive', 'archive', 'orders.csv')

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            age INTEGER,
            gender TEXT,
            state TEXT,
            street_address TEXT,
            postal_code TEXT,
            city TEXT,
            country TEXT,
            latitude REAL,
            longitude REAL,
            traffic_source TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            status TEXT,
            gender TEXT,
            created_at TEXT,
            returned_at TEXT,
            shipped_at TEXT,
            delivered_at TEXT,
            num_of_item INTEGER
        )
    ''')
    conn.commit()

def load_csv_to_table(conn, csv_path, table_name, columns):
    cursor = conn.cursor()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append(tuple(row[col] if row[col] != '' else None for col in columns))
        placeholders = ','.join(['?'] * len(columns))
        insert_query = f'INSERT INTO {table_name} ({",".join(columns)}) VALUES ({placeholders})'
        cursor.executemany(insert_query, rows)
    conn.commit()

def verify_data(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]
    print(f'Total users loaded: {users_count}')
    cursor.execute('SELECT COUNT(*) FROM orders')
    orders_count = cursor.fetchone()[0]
    print(f'Total orders loaded: {orders_count}')
    cursor.execute('SELECT * FROM users LIMIT 3')
    print('Sample users:')
    for row in cursor.fetchall():
        print(row)
    cursor.execute('SELECT * FROM orders LIMIT 3')
    print('Sample orders:')
    for row in cursor.fetchall():
        print(row)

def main():
    conn = sqlite3.connect(DB_NAME)
    create_tables(conn)
    load_csv_to_table(conn, USERS_CSV, 'users', [
        'id', 'first_name', 'last_name', 'email', 'age', 'gender', 'state',
        'street_address', 'postal_code', 'city', 'country', 'latitude',
        'longitude', 'traffic_source', 'created_at'
    ])
    load_csv_to_table(conn, ORDERS_CSV, 'orders', [
        'order_id', 'user_id', 'status', 'gender', 'created_at', 'returned_at',
        'shipped_at', 'delivered_at', 'num_of_item'
    ])
    verify_data(conn)
    conn.close()

if __name__ == '__main__':
    main()
