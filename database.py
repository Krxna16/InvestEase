import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_NAME = 'portfolio.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_holding(symbol, quantity, price, date):
    """Adds a new stock holding to the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO holdings (symbol, quantity, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
        (symbol.upper(), quantity, price, date)
    )
    conn.commit()
    conn.close()

def get_all_holdings():
    """Retrieves all stock holdings from the database as a DataFrame."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM holdings", conn)
    conn.close()
    return df

def update_holding(id, symbol, quantity, price, date):
    """Updates an existing stock holding."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE holdings SET symbol=?, quantity=?, purchase_price=?, purchase_date=? WHERE id=?",
        (symbol.upper(), quantity, price, date, id)
    )
    conn.commit()
    conn.close()

def delete_holding(id):
    """Deletes a stock holding by its ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM holdings WHERE id=?", (id,))
    conn.commit()
    conn.close()

def import_csv(file_path):
    """Imports holdings from a CSV file into the database."""
    try:
        df = pd.read_csv(file_path)
        df.columns = ['Symbol', 'Quantity', 'Purchase_Price', 'Purchase_Date']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("DELETE FROM holdings")
        
        for _, row in df.iterrows():
            c.execute(
                "INSERT INTO holdings (symbol, quantity, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
                (row['Symbol'].upper(), row['Quantity'], row['Purchase_Price'], str(row['Purchase_Date']))
            )
        conn.commit()
        conn.close()
        return True, f"Successfully imported {len(df)} records."
    except Exception as e:
        return False, f"Import failed: {e}"

def export_csv(file_path='exported_portfolio.csv'):
    """Exports all holdings from the database to a CSV file."""
    df = get_all_holdings()
    df_export = df.drop(columns=['id'])
    
    df_export.to_csv(file_path, index=False)
    
    if os.path.exists(file_path):
        return True, file_path
    else:
        return False, "Failed to create CSV file."

init_db()