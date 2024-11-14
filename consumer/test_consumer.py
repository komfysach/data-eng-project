import unittest
from unittest.mock import patch, MagicMock
import consumer.consumer as consumer_module

class TestKafkaConsumer(unittest.TestCase):
    @patch('consumer.consumer.Consumer')
    @patch('consumer.consumer.InfluxDBClient')
    def test_consumer_processes_message(self, MockInfluxDBClient, MockConsumer):
        # Mock Kafka consumer
        mock_consumer_instance = MockConsumer.return_value
        mock_consumer_instance.poll = MagicMock(return_value=MagicMock(value=lambda: b'{"ts": 1594512101.761235, "device": "b8:27:eb:bf:9d:51", "co": 0.005, "humidity": 51.0, "light": true, "lpg": 0.008, "motion": false, "smoke": 0.02, "temp": 22.6}'))
        mock_consumer_instance.error = MagicMock(return_value=None)

        # Mock InfluxDB client
        mock_write_api = MockInfluxDBClient.return_value.write_api.return_value
        mock_write_api.write = MagicMock()

        # Run the consumer loop once
        with patch('consumer.consumer.time.sleep', return_value=None):  # Prevent infinite sleep during testing
            consumer_module.consume_and_process_messages(mock_consumer_instance, mock_write_api)

        # Verify InfluxDB write call
        mock_write_api.write.assert_called_once()

        # Check if the consumer handled a message correctly
        mock_consumer_instance.poll.assert_called_once()

    @patch('consumer.consumer.print')
    def test_consumer_handles_no_message(self, mock_print):
        with patch('consumer.consumer.Consumer.poll', return_value=None):
            consumer_module.consume_and_process_messages(MagicMock(), MagicMock())
            mock_print.assert_not_called()  # Should not print if there's no message

if __name__ == '__main__':
    unittest.main()