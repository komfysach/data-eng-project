import pytest
from influxdb_client import InfluxDBClient, QueryApi
import pandas as pd
from app import get_data
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# InfluxDB client setup
token = os.getenv("INFLUXDB_TOKEN")
org = "iu"
url = "http://localhost:8086"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)
query_api = influxdb_client.query_api()

def test_influxdb_connection():
    try:
        influxdb_client.ping()
        assert True
    except Exception as e:
        pytest.fail(f"InfluxDB connection failed: {e}")

def test_get_data():
    df = get_data()
    assert not df.empty, "Data retrieval failed, DataFrame is empty"

def test_threshold_logic():
    data = {
        "time": ["2023-01-01T00:00:00Z"],
        "humidity": [30.0],
        "motion": [2]
    }
    df = pd.DataFrame(data)
    HUMIDITY_THRESHOLD = 40.0
    MOTION_THRESHOLD = 1

    assert df['humidity'].max() < HUMIDITY_THRESHOLD, "Humidity threshold check failed"
    assert df['motion'].max() > MOTION_THRESHOLD, "Motion threshold check failed"