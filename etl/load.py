"""Loads transformed data into PostgreSQL database."""

import os
import psycopg
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg.connect(
        dbname="airpollution_db",
        user="postgres",
        password=os.getenv("POSTGRES_PASSWORD"),
        host="localhost",
        port="5432",
    )


def load_data(table_name: str, df: pd.DataFrame):
    """Inserts data into PostgreSQL database."""
    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ", ".join(["%s"] * len(df.columns))
    columns = ", ".join(df.columns)
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    data_tuples = [tuple(row) for row in df.to_numpy()]

    cursor.executemany(sql, data_tuples)
    conn.commit()

    cursor.close()
    conn.close()
