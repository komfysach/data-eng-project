from confluent_kafka import Producer
import pandas as pd
import json
import time

# Initialize Kafka producer
producer = Producer({'bootstrap.servers': 'localhost:9092'})

# Print thaT the producer is ready
print('Kafka producer is ready', producer)

# Delivery report callback
def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

# Load the dataset
data = pd.read_csv('data/iot_telemetry_data.csv')

# Print the first 5 rows of the dataset
print(data.head())

# Simulate real-time data ingestion
for _, row in data.iterrows():
    message = row.to_dict()
    print(f"Producing message: {message}")  # Log the message being produced
    try:
        producer.produce('sensor-data', value=json.dumps(message).encode('utf-8'), callback=delivery_report)
        producer.poll(0)
    except Exception as e:
        print(f"Failed to produce message: {e}")
    time.sleep(1)  # Simulate real-time data stream

# Flush producer
try:
    producer.flush()
except Exception as e:
    print(f"Failed to flush producer: {e}")