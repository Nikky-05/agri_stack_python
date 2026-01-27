import pandas as pd
import psycopg2
from psycopg2 import sql
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_PARAMS = {
    "dbname": os.getenv("DEFAULT_DB", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "NKpallotti@99"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

TARGET_DB = os.getenv("DB_NAME", "exam_db")

def setup_database():
    try:
        # Connect to default database to create the new one
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Create database
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TARGET_DB}'")
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {TARGET_DB}")
            print(f"Database '{TARGET_DB}' created.")
        else:
            print(f"Database '{TARGET_DB}' already exists.")
        
        cur.close()
        conn.close()

        # Connect to the new database
        # Connect to the new database
        DB_PARAMS["dbname"] = TARGET_DB
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Define tables
        tables = {
            "aggregate_summary_data": """
                CREATE TABLE IF NOT EXISTS aggregate_summary_data (
                    rec_id SERIAL PRIMARY KEY,
                    state_lgd_code TEXT,
                    district_lgd_code TEXT,
                    sub_district_lgd_code TEXT,
                    village_lgd_code TEXT,
                    season TEXT,
                    season_id INT,
                    year TEXT,
                    total_plots INT,
                    total_assigned_plots INT,
                    total_no_of_surveyors INT,
                    total_plots_surveyed INT,
                    total_plots_unable_to_survey INT,
                    total_survey_approved INT,
                    total_today_survey INT,
                    total_survey_under_review INT,
                    timestamp TEXT,
                    createdat TIMESTAMP,
                    updatedat TIMESTAMP,
                    reference_id TEXT,
                    record_id TEXT,
                    is_view BOOLEAN
                )
            """,
            "crop_area_data": """
                CREATE TABLE IF NOT EXISTS crop_area_data (
                    rec_id SERIAL PRIMARY KEY,
                    state_lgd_code TEXT,
                    district_lgd_code TEXT,
                    sub_district_lgd_code TEXT,
                    village_lgd_code TEXT,
                    season TEXT,
                    season_id INT,
                    season_start_date TEXT,
                    season_end_date TEXT,
                    crop_code TEXT,
                    crop_name_eng TEXT,
                    irrigation_source TEXT,
                    area_unit TEXT,
                    year TEXT,
                    timestamp TEXT,
                    no_of_plots INT,
                    no_of_farmers INT,
                    crop_area_closed NUMERIC,
                    crop_area_approved NUMERIC,
                    createdat TIMESTAMP,
                    updatedat TIMESTAMP,
                    reference_id TEXT,
                    record_id TEXT,
                    is_view BOOLEAN
                )
            """,
            "cultivated_summary_data": """
                CREATE TABLE IF NOT EXISTS cultivated_summary_data (
                    rec_id SERIAL PRIMARY KEY,
                    state_lgd_code TEXT,
                    district_lgd_code TEXT,
                    sub_district_lgd_code TEXT,
                    village_lgd_code TEXT,
                    area_unit TEXT,
                    season TEXT,
                    season_id TEXT,
                    year TEXT,
                    timestamp TEXT,
                    total_surveyed_plots INT,
                    total_surveyable_area NUMERIC,
                    total_surveyed_area NUMERIC,
                    total_na_area NUMERIC,
                    total_fallow_area NUMERIC,
                    total_harvested_area NUMERIC,
                    total_irrigated_area NUMERIC,
                    total_perennial_crop_area NUMERIC,
                    total_biennial_crop_area NUMERIC,
                    total_seasonal_crop_area NUMERIC,
                    total_unirrigated_area NUMERIC,
                    createdat TIMESTAMP,
                    updatedat TIMESTAMP,
                    reference_id TEXT,
                    record_id TEXT,
                    is_view BOOLEAN
                )
            """
        }

        for table_name, create_sql in tables.items():
            cur.execute(create_sql)
            print(f"Table '{table_name}' checked/created.")

        conn.commit()
        
        # Import data
        csv_files = {
            "aggregate_summary_data": "data_for_testing/data-1768987329067mhAgreegatedData.csv",
            "crop_area_data": "data_for_testing/data-1768987385851mhCropArea.csv",
            "cultivated_summary_data": "data_for_testing/data-1768987427993mhCultivatedData.csv"
        }

        for table_name, csv_file in csv_files.items():
            df = pd.read_csv(csv_file)
            # Basic cleanup for Postgres compatibility
            df = df.where(pd.notnull(df), None)
            
            # Using pandas to_sql for simplicity in this implementation
            from sqlalchemy import create_engine
            encoded_password = quote_plus(DB_PARAMS['password'])
            engine = create_engine(f"postgresql://{DB_PARAMS['user']}:{encoded_password}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{TARGET_DB}")
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            print(f"Data imported into '{table_name}' from '{csv_file}'.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_database()
