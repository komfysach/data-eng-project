# Step 1: Run tests
Write-Host "Running tests..."
py -m unittest producer.test_producer
py -m unittest consumer.test_consumer
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed. Aborting deployment."
    exit 1
} else {
    Write-Host "All tests passed. Proceeding with deployment."
}

# Step 2: Spin up Docker containers
Write-Host "Starting Docker containers..."
docker-compose up -d

# Step 3: Wait for InfluxDB to be ready
Write-Host "Waiting for InfluxDB to initialize..."
do {
    Start-Sleep -Seconds 5
    $health = Invoke-RestMethod -Uri http://localhost:8086/health -UseBasicParsing
} while ($health.status -ne "pass")

# Step 4: Set up InfluxDB using HTTP API if not already configured
$bucketCheck = Invoke-RestMethod -Uri http://localhost:8086/api/v2/buckets -Headers @{ Authorization = "Token admin:admin123" } -UseBasicParsing
if ($bucketCheck.buckets | Where-Object { $_.name -eq "sensor_data" }) {
    Write-Host "InfluxDB is already set up."
} else {
    Write-Host "Setting up InfluxDB using HTTP API..."
    $response = Invoke-RestMethod -Uri http://localhost:8086/api/v2/setup -Method Post -ContentType "application/json" -Body '{
        "username": "admin",
        "password": "admin123",
        "org": "iu",
        "bucket": "sensor_data"
    }'
    $token = $response.auth.token
    if (-not $token) {
        Write-Host "Failed to create token. Exiting."
        exit 1
    }

    # Save the token to .env
    Set-Content -Path .env -Value "INFLUXDB_TOKEN=$token"
    Write-Host "InfluxDB setup completed. Token saved in .env"
}

# Step 5: Start the Kafka producer
Write-Host "Starting the Kafka producer..."
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "producer/producer.py"
Write-Host "Producer started."

# Step 6: Start the Kafka consumer
Write-Host "Starting the Kafka consumer..."
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "consumer/consumer.py"
Write-Host "Consumer started."

# Step 7: Run the Streamlit app tests
Write-Host "Running Streamlit app tests..."
py -m unittest app.test_app
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed. Aborting deployment."
    exit 1
} else {
    Write-Host "Test passed. Proceeding with starting streamlit app."
}

# Step 8: Start the Streamlit app
Write-Host "Starting the Streamlit web app..."
Start-Process -NoNewWindow -FilePath "streamlit" -ArgumentList "run app.py"
Write-Host "Web app started and running at http://localhost:8501"

# Monitor the processes (simplified for PowerShell)
Write-Host "Monitoring producer, consumer, and web app..."
Write-Host "Web app is being served at http://localhost:8501"
