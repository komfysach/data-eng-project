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
    # Select box for refresh rate
    refresh_rate = st.selectbox(
        "Select refresh rate",
        options=[1, 5, 10, 30],
        index=0,
        format_func=lambda x: f"{x} sec"
    )

    # Convert refresh rate to milliseconds
    refresh_interval = refresh_rate * 1000

    # Auto-refresh the page based on the selected refresh rate
    st_autorefresh(interval=refresh_interval, key="sensor_data_dashboard")

    # Dynamic threshold sliders
    st.sidebar.header("Set Thresholds")
    humidity_threshold = st.sidebar.slider("Humidity Threshold (%)", min_value=0, max_value=100, value=40)
    motion_threshold = st.sidebar.slider("Motion Threshold", min_value=0, max_value=10, value=1)
    co_threshold = st.sidebar.slider("CO Threshold (ppm)", min_value=0.0, max_value=10.0, value=0.005)
    lpg_threshold = st.sidebar.slider("LPG Threshold (ppm)", min_value=0.0, max_value=10.0, value=0.008)
    smoke_threshold = st.sidebar.slider("Smoke Threshold (ppm)", min_value=0.0, max_value=10.0, value=0.02)
    temp_threshold = st.sidebar.slider("Temperature Threshold (°C)", min_value=-10.0, max_value=50.0, value=25.0)

   # Timer for loading data
    start_time = time.time()
    timeout = 60  # 1 minute

    alerts = []

    alerts = []

    while True:
        df = get_data()
        if not df.empty:
            # Check thresholds and collect alerts
            if df['humidity'].max() < humidity_threshold:
                alerts.append(f"Warning: Humidity level dropped below {humidity_threshold}%!")
            if df['motion'].max() > motion_threshold:
                alerts.append(f"Alert: Motion detected above threshold of {motion_threshold}!")
            if df['co'].max() > co_threshold:
                alerts.append(f"Alert: CO level detected above threshold of {co_threshold} ppm!")
            if df['lpg'].max() > lpg_threshold:
                alerts.append(f"Alert: LPG level detected above threshold of {lpg_threshold} ppm!")
            if df['smoke'].max() > smoke_threshold:
                alerts.append(f"Alert: Smoke level detected above threshold of {smoke_threshold} ppm!")
            if df['temp'].max() > temp_threshold:
                alerts.append(f"Alert: Temperature level detected above threshold of {temp_threshold} °C!")
            break
        else:
            elapsed_time = time.time() - start_time
            if elapsed_time < timeout:
                st.write("Loading the data...")
            else:
                st.write("No data loaded. Check the logs...")
                break

    # Display alerts at the top of the sidebar
    st.sidebar.header("Alerts")
    for alert in alerts:
        st.sidebar.error(alert)
        
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
            if df['humidity'].max() < humidity_threshold:
                st.error(f"Warning: Humidity level dropped below {humidity_threshold}%!")
            if df['motion'].max() > motion_threshold:
                st.warning(f"Alert: Motion detected above threshold of {motion_threshold}!")
            if df['co'].max() > co_threshold:
                st.warning(f"Alert: CO level detected above threshold of {co_threshold} ppm!")
            if df['lpg'].max() > lpg_threshold:
                st.warning(f"Alert: LPG level detected above threshold of {lpg_threshold} ppm!")
            if df['smoke'].max() > smoke_threshold:
                st.warning(f"Alert: Smoke level detected above threshold of {smoke_threshold} ppm!")
            if df['temp'].max() > temp_threshold:
                st.warning(f"Alert: Temperature level detected above threshold of {temp_threshold} °C!")
            break
        else:
            elapsed_time = time.time() - start_time
            if elapsed_time < timeout:
                st.write("Loading the data...")
            else:
                st.write("No data loaded. Check the logs...")
                break

    # Display alerts at the top of the sidebar
    st.sidebar.header("Alerts")
    for alert in alerts:
        st.sidebar.error(alert)

# Run the main function
if __name__ == "__main__":
    main()