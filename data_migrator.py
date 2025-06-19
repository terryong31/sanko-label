import pandas as pd
from sqlalchemy import create_engine

# === CONFIGURATION ===
EXCEL_FILE = 'new_data.xlsx'  # Change this to your Excel file name
DATABASE_TYPE = 'mysql'        # Change to 'postgresql' if using PostgreSQL
DB_USER = 'root'
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_PORT = '3306'               # '5432' for PostgreSQL
DB_NAME = 'sanko'
TABLE_NAME = 'information'

# === READ EXCEL FILE ===
df = pd.read_excel(EXCEL_FILE)

# === CREATE DATABASE CONNECTION ===
if DATABASE_TYPE == 'mysql':
    engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
elif DATABASE_TYPE == 'postgresql':
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
else:
    raise ValueError("Unsupported database type.")

# === UPLOAD TO DATABASE ===
df.to_sql(TABLE_NAME, con=engine, if_exists='replace', index=False)
print(f"Data uploaded successfully to table '{TABLE_NAME}' in database '{DB_NAME}'.")

