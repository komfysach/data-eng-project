from confluent_kafka import Consumer, KafkaException, KafkaError
import json

# Initialize Kafka consumer
consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'sensor-data-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(consumer_config)

# Print that the consumer is ready
print('Kafka consumer is ready', consumer)

consumer.subscribe(['sensor-data'])

# Print the consumer subscription
print('Subscribed to sensor-data topic')

# Example processing: filter data based on a threshold value
threshold_value = 50  

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                print('%% %s [%d] reached end at offset %d\n' %
                      (msg.topic(), msg.partition(), msg.offset()))
            elif msg.error():
                raise KafkaException(msg.error())
        else:
            try:
                data = json.loads(msg.value().decode('utf-8'))
                # Example processing: print filtered data
                print(f"Received message: {data}")
                if 'sensor_value' in data and data['sensor_value'] > threshold_value:
                    print(f"Filtered data: {data}")
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON message: {e}")
            except KeyError as e:
                print(f"Missing expected key in message: {e}")
            except Exception as e:
                print(f"Unexpected error while processing message: {e}")
except KeyboardInterrupt:
    pass
finally:
    # Close down consumer to commit final offsets.
    consumer.close()