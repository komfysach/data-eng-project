# Step 1: Install dependencies
Write-Host "Installing dependencies..."
py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies. Aborting deployment."
    exit 1
} else {
    Write-Host "Dependencies installed successfully."
}

# Step 2: Run tests
Write-Host "Running tests..."
py -m unittest producer.test_producer
py -m unittest consumer.test_consumer
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed. Aborting deployment."
    exit 1
} else {
    Write-Host "All tests passed. Proceeding with deployment."
}

# Step 3: Spin up Docker containers
Write-Host "Starting Docker containers..."
docker-compose up -d

# Step 4: Wait for InfluxDB to be ready
Write-Host "Waiting for InfluxDB to initialize..."
do {
    Start-Sleep -Seconds 5
    $health = Invoke-RestMethod -Uri http://localhost:8086/health -UseBasicParsing
} while ($health.status -ne "pass")

# Step 5: Load environment variables from .env file and set up InfluxDB
$envFilePath = ".env"
$envContent = Get-Content -Path $envFilePath
$tokenPattern = "INFLUXDB_TOKEN=(.*)"
$tokenMatch = $envContent | Select-String -Pattern $tokenPattern

if ($tokenMatch) {
    $env:INFLUXDB_TOKEN = $tokenMatch.Matches.Groups[1].Value
    Write-Host "Token found in .env file."
} else {
    Write-Host "Token not found in .env file. Setting up InfluxDB using HTTP API..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8086/api/v2/setup" -Method Post -ContentType "application/json" -Body '{
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
        Add-Content -Path $envFilePath -Value "`nINFLUXDB_TOKEN=$token"
        $env:INFLUXDB_TOKEN = $token
        Write-Host "InfluxDB setup completed. Token saved in .env"
    } catch {
        Write-Host "Error setting up InfluxDB: $_"
        exit 1
    }
}

# InfluxDB setup
$influxdbUrl = "http://localhost:8086"
$org = "iu"
$bucket = "sensor_data"
$token = $env:INFLUXDB_TOKEN

# Check if the bucket already exists
try {
    $bucketCheck = Invoke-RestMethod -Uri "$influxdbUrl/api/v2/buckets?name=$bucket" -Headers @{Authorization = "Token $token"}
    if ($bucketCheck.buckets.Count -eq 0) {
        Write-Host "Bucket does not exist. Creating bucket..."
        $bucketData = @{
            orgID = (Invoke-RestMethod -Uri "$influxdbUrl/api/v2/orgs?org=$org" -Headers @{Authorization = "Token $token"}).orgs[0].id
            name = $bucket
            retentionRules = @(@{type = "expire"; everySeconds = 0})
        }
        $bucketResponse = Invoke-RestMethod -Uri "$influxdbUrl/api/v2/buckets" -Method Post -Headers @{Authorization = "Token $token"} -Body ($bucketData | ConvertTo-Json)
        Write-Host "Bucket created: $($bucketResponse.name)"
    } else {
        Write-Host "Bucket already exists."
    }
} catch {
    Write-Host "Error checking or creating bucket: $_"
}

# Step 7: Start the Kafka producer
Write-Host "Starting the Kafka producer..."
Start-Process -NoNewWindow -FilePath "py" -ArgumentList "producer/producer.py"
Write-Host "Producer started."

# Step 8: Start the Kafka consumer
Write-Host "Starting the Kafka consumer..."
Start-Process -NoNewWindow -FilePath "py" -ArgumentList "consumer/consumer.py"
Write-Host "Consumer started."

# Step 9: Start the Streamlit app
Write-Host "Starting the Streamlit monitoring web app..."
Start-Process -NoNewWindow -FilePath "streamlit" -ArgumentList "run app.py"
Write-Host "Web app started and running at http://localhost:8501"

# Monitor the processes (simplified for PowerShell)
Write-Host "Monitoring producer, consumer, and web app..."
Write-Host "Web app is being served at http://localhost:8501"
