import streamlit as st
from influxdb_client import InfluxDBClient, QueryApi
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import time
from streamlit_autorefresh import st_autorefresh

# Load environment variables from .env file
load_dotenv()

# InfluxDB client setup
token = os.getenv("INFLUXDB_TOKEN")
org = "iu"
url = "http://localhost:8086"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)
query_api = influxdb_client.query_api()

# Streamlit app setup
st.set_page_config(page_title="Sensor Data Dashboard", layout="wide")
st.title("Real-time Sensor Data Dashboard")

# Helper function to query data
def get_data():
    query = '''
    from(bucket:"sensor_data")
    |> range(start: -1h)
    |> filter(fn: (r) => r._measurement == "sensor_measurement")
    '''
    result = query_api.query(org=org, query=query)

    data = {
        "time": [],
        "temp": [],
        "humidity": [],
        "motion": [],
        "co": [],
        "lpg": [],
        "smoke": []
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
            elif record.get_field() == "co":
                value = record.get_value()
                if isinstance(value, str):
                    data["co"].append(float(value.rstrip('m')))
                else:
                    data["co"].append(value)
            elif record.get_field() == "lpg":
                value = record.get_value()
                if isinstance(value, str):
                    data["lpg"].append(float(value.rstrip('m')))
                else:
                    data["lpg"].append(value)
            elif record.get_field() == "smoke":
                value = record.get_value()
                if isinstance(value, str):
                    data["smoke"].append(float(value.rstrip('m')))
                else:
                    data["smoke"].append(value)

    # Ensure all arrays are of the same length
    min_length = min(len(data["time"]), len(data["temp"]), len(data["humidity"]), len(data["motion"]), len(data["co"]), len(data["lpg"]), len(data["smoke"]))
    for key in data:
        data[key] = data[key][:min_length]

    return pd.DataFrame(data)

# Main function to display the dashboard
def main():
    df = get_data()
    if not df.empty:
        # Plot temperature
        st.subheader("Temperature Over Time")
        fig_temp = px.line(df, x="time", y="temp", title="Temperature")
        st.plotly_chart(fig_temp, use_container_width=True)

        # Plot humidity
        st.subheader("Humidity Over Time")
        fig_humidity = px.line(df, x="time", y="humidity", title="Humidity")
        st.plotly_chart(fig_humidity, use_container_width=True)

        # Plot motion
        st.subheader("Motion Detection")
        fig_motion = px.line(df, x="time", y="motion", title="Motion Detection")
        st.plotly_chart(fig_motion, use_container_width=True)

        # Plot CO
        st.subheader("CO Levels Over Time")
        fig_co = px.line(df, x="time", y="co", title="CO Levels")
        st.plotly_chart(fig_co, use_container_width=True)

        # Plot LPG
        st.subheader("LPG Levels Over Time")
        fig_lpg = px.line(df, x="time", y="lpg", title="LPG Levels")
        st.plotly_chart(fig_lpg, use_container_width=True)

        # Plot Smoke
        st.subheader("Smoke Levels Over Time")
        fig_smoke = px.line(df, x="time", y="smoke", title="Smoke Levels")
        st.plotly_chart(fig_smoke, use_container_width=True)

        # Check thresholds and display notifications
        if df['humidity'].max() < 40.0:
            st.error("Warning: Humidity level dropped below 40%!")
        if df['motion'].max() > 1:
            st.warning("Alert: Motion detected!")
    else:
        st.write("No data available")

# Run the main function and refresh every second
if __name__ == "__main__":
    main()
    time.sleep(1)
    st_autorefresh(interval=1000)  # Refresh every second