#!/bin/bash

# Step 1: Spin up Docker containers
echo "Starting Docker containers..."
docker-compose up -d

# Step 2: Install dependencies
echo "Installing dependencies..."
py -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Aborting deployment."
    exit 1
else
    echo "Dependencies installed successfully."
fi

# Step 3: Run tests
echo "Running tests..."
py -m unittest producer.test_producer
py -m unittest consumer.test_consumer
if [ $? -ne 0 ]; then
    echo "Tests failed. Aborting deployment."
    exit 1
else
    echo "All tests passed. Proceeding with deployment."
fi

# Step 4: Wait for InfluxDB to be ready
echo "Waiting for InfluxDB to initialize..."
until curl -s http://localhost:8086/health | grep '"status":"pass"' > /dev/null; do
    sleep 5
    echo "Waiting for InfluxDB to be ready..."
done

# Step 5: Prompt for username and password
read -p "Enter InfluxDB username: " username
read -sp "Enter InfluxDB password: " password
echo

# Load environment variables from .env file and set up InfluxDB
envFilePath=".env"
if [ -f "$envFilePath" ]; thendo
    source $envFilePath
fi

if [ -z "$INFLUXDB_TOKEN" ]; then
    echo "Token not found in .env file. Setting up InfluxDB using HTTP API..."
    response=$(curl -s -X POST http://localhost:8086/api/v2/setup \
        --header "Content-Type: application/json" \
        --data '{
          "username": "'"$username"'",
          "password": "'"$password"'",
          "org": "iu",
          "bucket": "sensor_data"
        }')

    token=$(echo $response | jq -r '.auth.token')
    if [ -z "$token" ]; then
        echo "Failed to create token. Exiting."
        exit 1
    fi

    # Save the token to .env
    echo "INFLUXDB_TOKEN=$token" >> $envFilePath
    export INFLUXDB_TOKEN=$token
    echo "InfluxDB setup completed. Token saved in .env"
else
    echo "Token found in .env file."
fi

# InfluxDB setup
influxdbUrl="http://localhost:8086"
org="iu"
bucket="sensor_data"
token=$INFLUXDB_TOKEN

# Check if the bucket already exists
bucketCheck=$(curl -s -H "Authorization: Token $token" "$influxdbUrl/api/v2/buckets?name=$bucket")
if echo $bucketCheck | grep -q '"name":"sensor_data"'; then
    echo "Bucket already exists."
else
    echo "Bucket does not exist. Creating bucket..."
    orgID=$(curl -s -H "Authorization: Token $token" "$influxdbUrl/api/v2/orgs?org=$org" | jq -r '.orgs[0].id')
    bucketData=$(jq -n --arg orgID "$orgID" --arg name "$bucket" '{orgID: $orgID, name: $name, retentionRules: [{type: "expire", everySeconds: 0}]}')
    bucketResponse=$(curl -s -X POST "$influxdbUrl/api/v2/buckets" -H "Authorization: Token $token" -H "Content-Type: application/json" --data "$bucketData")
    echo "Bucket created: $(echo $bucketResponse | jq -r '.name')"
fi

# Step 6: Start the Kafka producer
echo "Starting the Kafka producer..."
nohup py producer/producer.py &

# Step 7: Start the Kafka consumer
echo "Starting the Kafka consumer..."
nohup py consumer/consumer.py &

# Step 8: Start the Streamlit app
echo "Starting the Streamlit monitoring web app..."
nohup streamlit run app/app.py &

# Monitor the processes (simplified for shell script)
echo "Monitoring producer, consumer, and web app..."
echo "Web app is being served at http://localhost:8501"