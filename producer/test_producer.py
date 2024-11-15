import unittest
from unittest.mock import patch, MagicMock
import producer.producer as producer_module
import pandas as pd

class TestKafkaProducer(unittest.TestCase):
    @patch('producer.producer.producer')
    def test_producer_sends_message(self, MockProducer):
        # Mock Kafka producer
        mock_producer_instance = MockProducer.return_value
        mock_producer_instance.produce = MagicMock()
        mock_producer_instance.flush = MagicMock()

        # Mock dataset
        data = pd.DataFrame([{
            'ts': 1594512101.761235,
            'device': 'b8:27:eb:bf:9d:51',
            'co': 0.005,
            'humidity': 51.0,
            'light': True,
            'lpg': 0.008,
            'motion': False,
            'smoke': 0.02,
            'temp': 22.6
        }])

        # Run the producer function
        with patch('producer.producer.time.sleep', return_value=None):  # Prevent sleep during testing
            producer_module.produce_messages(mock_producer_instance, data)

        # Verify Kafka produce call
        mock_producer_instance.produce.assert_called_once()
        mock_producer_instance.flush.assert_called()

if __name__ == '__main__':
    unittest.main()