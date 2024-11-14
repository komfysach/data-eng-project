import pytest
from influxdb_client import InfluxDBClient, QueryApi
import pandas as pd

influxdb_client = InfluxDBClient(url="http://localhost:8086", token="", org="")
query_api = influxdb_client.query_api()

def test_influxdb_connection():
    try:
        influxdb_client.ping()
        assert True
    except Exception as e:
        pytest.fail(f"InfluxDB connection failed: {e}")

def test_get_data():
    query = '''
    from(bucket:"sensor_data")
    |> range(start: -1h)
    |> filter(fn: (r) => r._measurement == "sensor_measurement")
    '''
    result = query_api.query(org="", query=query)

    data = {
        "time": [],
        "temp": [],
        "humidity": [],
        "motion": []
    }
    for table in result:
        for record in table.records:
            data["time"].append(record.get_time())
            if record.get_field() == "temp":
                data["temp"].append(record.get_value())
            elif record.get_field() == "humidity":
                data["humidity"].append(record.get_value())
            elif record.get_field() == "motion":
                data["motion"].append(record.get_value())

    df = pd.DataFrame(data)
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
