import logging
from confluent_kafka import Consumer, KafkaException
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka consumer configuration
kafka_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'sensor-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(kafka_config)
consumer.subscribe(['sensor-data'])

# InfluxDB client setup
token = os.getenv("INFLUXDB_TOKEN")
org = "iu"
url = "http://localhost:8086"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)
write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
bucket = "sensor_data"

def consume_and_process_messages(consumer, write_api):
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    continue
                else:
                    logging.error(f"Consumer error: {msg.error()}")
                    break

            # Process the message
            try:
                data = json.loads(msg.value().decode('utf-8'))
                logging.info(f"Received message: {data}")

                # Ensure the timestamp is an integer
                timestamp = int(data['ts'])
                logging.info(f"Parsed timestamp: {timestamp}")

                point = (
                    Point("sensor_measurement")
                    .tag("device", data['device'])
                    .field("co", data['co'])
                    .field("humidity", data['humidity'])
                    .field("light", int(data['light']))
                    .field("lpg", data['lpg'])
                    .field("motion", int(data['motion']))
                    .field("smoke", data['smoke'])
                    .field("temp", data['temp'])
                )

                write_api.write(bucket=bucket, org=org, record=point)
                logging.info(f"Point data written to InfluxDB: {point.to_line_protocol()}")
                logging.info(f"Consumed and written data to InfluxDB: {data}")
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error processing message: {e}")

    except KeyboardInterrupt:
        logging.info("Consumer interrupted")
    finally:
        consumer.close()
        logging.info("Consumer script completed.")

if __name__ == "__main__":
    consume_and_process_messages(consumer, write_api)