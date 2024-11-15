import unittest
from unittest.mock import patch, MagicMock
import consumer.consumer as consumer_module

class TestKafkaConsumer(unittest.TestCase):
    @patch('consumer.consumer.Consumer')
    @patch('consumer.consumer.InfluxDBClient')
    def test_consumer_processes_message(self, MockInfluxDBClient, MockConsumer):
        # Mock Kafka consumer
        mock_consumer_instance = MockConsumer.return_value
        mock_message = MagicMock()
        mock_message.value.return_value = b'{"ts": 1594512101.761235, "device": "b8:27:eb:bf:9d:51", "co": 0.005, "humidity": 51.0, "light": true, "lpg": 0.008, "motion": false, "smoke": 0.02, "temp": 22.6}'
        mock_message.error.return_value = None
        mock_consumer_instance.poll.return_value = mock_message

        # Mock InfluxDB client
        mock_write_api = MockInfluxDBClient.return_value.write_api.return_value
        mock_write_api.write = MagicMock()

        # Run the consumer loop once
        with patch('consumer.consumer.time.sleep', return_value=None):  # Prevent infinite sleep during testing
            consumer_module.consume_and_process_messages(mock_consumer_instance, mock_write_api, max_iterations=1)

        # Verify InfluxDB write call
        mock_write_api.write.assert_called_once()

        # Check if the consumer handled a message correctly
        mock_consumer_instance.poll.assert_called_once()

if __name__ == '__main__':
    unittest.main()