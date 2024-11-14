from confluent_kafka import Producer
import pandas as pd
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Kafka producer
producer = Producer({'bootstrap.servers': 'localhost:9092'})

# Print that the producer is ready
print('Kafka producer is ready', producer)

# Delivery report callback
def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

def produce_messages(producer, data):
    try:
        # Simulate real-time data ingestion
        for _, row in data.iterrows():
            message = row.to_dict()
            try:
                producer.produce(
                    topic='sensor-data',
                    key=str(row['ts']),
                    value=json.dumps(message),
                    callback=delivery_report
                )
                producer.flush()
                time.sleep(1)
                logging.info(f"Produced message: {message}")
            except Exception as e:
                logging.error(f"Error producing message: {e}")
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
    finally:
        producer.flush()
        logging.info("Producer script completed.")

if __name__ == "__main__":
    # Load the dataset
    try:
        data = pd.read_csv('data/iot_telemetry_data.csv')
        logging.info("Dataset loaded successfully.")
    except FileNotFoundError as e:
        logging.error(f"Dataset not found: {e}")
        raise

    # Print the first 5 rows of the dataset
    print(data.head())

    produce_messages(producer, data)