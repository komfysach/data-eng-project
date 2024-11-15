#!/bin/bash

# Step 1: Run tests
echo "Running tests..."
py -m unittest producer.test_producer
py -m unittest consumer.test_consumer
if [ $? -ne 0 ]; then
    echo "Tests failed. Aborting deployment."
    exit 1
else
    echo "All tests passed. Proceeding with deployment."
fi

# Step 2: Spin up Docker containers
echo "Starting Docker containers..."
docker-compose up -d

# Step 3: Wait for InfluxDB to be ready
echo "Waiting for InfluxDB to initialize..."
until curl -s http://localhost:8086/health | grep '"status":"pass"' > /dev/null; do
    sleep 5
    echo "Waiting for InfluxDB to be ready..."
done

# Step 4: Set up InfluxDB using HTTP API if not already configured
if curl -s -H "Authorization: Token admin:admin123" http://localhost:8086/api/v2/buckets | grep -q "sensor_data"; then
    echo "InfluxDB is already set up."
else
    echo "Setting up InfluxDB using HTTP API..."

    # Create an initial user, organization, and bucket using the API
    response=$(curl -s -X POST http://localhost:8086/api/v2/setup \
        --header "Content-Type: application/json" \
        --data '{
          "username": "admin",
          "password": "admin123",
          "org": "iu",
          "bucket": "sensor_data"
        }')

    # Extract the token using jq or a Python script
    token=$(echo $response | jq -r '.auth.token')
    if [ -z "$token" ]; then
        echo "Failed to create token. Exiting."
        exit 1
    fi

    # Save the token to .env
    echo "INFLUXDB_TOKEN=$token" > .env
    echo "InfluxDB setup completed. Token saved in .env"
fi

# Step 5: Start the Kafka producer
echo "Starting the Kafka producer..."
python producer/producer.py &
producer_pid=$!
echo "Producer started with PID $producer_pid"

# Step 6: Start the Kafka consumer
echo "Starting the Kafka consumer..."
python consumer/consumer.py &
consumer_pid=$!
echo "Consumer started with PID $consumer_pid"

# Step 7: Run the Streamlit app tests
echo "Running Streamlit app tests..."
py -m unittest app.test_app
if [ $? -ne 0 ]; then
    echo "Test failed. Aborting deployment."
    exit 1
else
    echo "Test passed. Proceeding with running streamlit app."
fi

# Step 8: Start the Streamlit app
echo "Starting the Streamlit web app..."
streamlit run app.py &
web_app_pid=$!
echo "Web app started with PID $web_app_pid"

# Monitor the processes
echo "Monitoring producer, consumer, and web app..."
echo "Web app is being served at http://localhost:8501"

# Keep the script running to show status
while sleep 10; do
    if ps -p $producer_pid > /dev/null; then
        echo "Producer is running..."
    else
        echo "Producer has stopped."
    fi

    if ps -p $consumer_pid > /dev/null; then
        echo "Consumer is running..."
    else
        echo "Consumer has stopped."
    fi

    if ps -p $web_app_pid > /dev/null; then
        echo "Web app is running at http://localhost:8501"
    else
        echo "Web app has stopped."
    fi
done
