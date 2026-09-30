from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

load_dotenv(project_root / ".env")

data_path = (
    project_root
    / "data"
    / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

db_host = os.getenv("MYSQL_HOST", "127.0.0.1")
db_port = int(os.getenv("MYSQL_PORT", "3306"))
db_user = os.getenv("MYSQL_USER", "root")
db_password = os.getenv("MYSQL_PASSWORD", "password")
db_name = os.getenv(
    "MYSQL_DATABASE",
    "logistics_ai_fde_project_db"
)

print(f"Loading CSV from {data_path}...")
df = pd.read_csv(data_path)

legacy_mapping = {
    "timestamp": "TS_UTC",
    "vehicle_gps_latitude": "V_LAT",
    "vehicle_gps_longitude": "V_LON",
    "iot_temperature": "IOT_TEMP_VAL_C",
    "cargo_condition_status": "CGO_COND_CD",
    "risk_classification": "RISK_CLS_TXT",
    "delay_probability": "DELAY_PROB_DEC",
    "port_congestion_level": "PRT_CNG_LVL",
    "route_risk_level": "RT_RSK_IDX",
}

df_legacy = df[list(legacy_mapping.keys())].rename(
    columns=legacy_mapping
)

df_legacy["SYS_INGEST_FLAG"] = "Y"

print(f"Connecting to MySQL at {db_host}:{db_port}/{db_name}...")

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    database=db_name,
)

engine = create_engine(
    connection_url,
    pool_pre_ping=True,
)

with engine.connect():
    print("✅ MySQL connection successful!")

table_name = "TBL_SC_FLEET_HIST_RAW"

print(
    f"Ingesting {len(df_legacy):,} rows into {table_name}. "
    "This may take a minute..."
)

df_legacy.to_sql(
    table_name,
    engine,
    if_exists="replace",
    index=False,
    chunksize=1000,
    method="multi",
)

print("✅ Legacy data ingestion complete!")