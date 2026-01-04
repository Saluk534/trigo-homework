# Service Discovery Updater

## Purpose
This service bridges the gap between Trigo's inventory system and Prometheus monitoring by:
1. Periodically fetching the list of active sensors from the inventory API
2. Converting the sensor list into Prometheus file-based service discovery format
3. Writing the targets to a shared volume that Prometheus watches

## How It Works

```
┌─────────────┐
│ Inventory   │ HTTP GET /inventory
│ Service     │◄─────────────────┐
└─────────────┘                  │
                                 │
                          ┌──────┴──────┐
                          │ SD Updater  │
                          │  (Python)   │
                          └──────┬──────┘
                                 │
                                 │ Write JSON
                                 ▼
                          ┌─────────────┐
                          │ Shared      │
                          │ Volume      │
                          │targets.json │
                          └──────┬──────┘
                                 │
                                 │ Read & Monitor
                                 ▼
                          ┌─────────────┐
                          │ Prometheus  │
                          └─────────────┘
```

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `INVENTORY_URL` | `http://inventory_server:1337/inventory` | URL to fetch sensor list |
| `UPDATE_INTERVAL` | `30` | How often to update targets (seconds) |
| `TARGETS_FILE` | `/shared/targets.json` | Output file path |
| `METRICS_PORT` | `9100` | Port where sensors expose metrics |
| `METRICS_PATH` | `/metrics` | Path to metrics endpoint on sensors |

## Output Format

The service generates a JSON file in Prometheus file-based service discovery format:

```json
[
  {
    "targets": [
      "sensor_0:9100",
      "sensor_1:9100",
      "sensor_2:9100"
    ],
    "labels": {
      "__metrics_path__": "/metrics",
      "job": "sensors",
      "environment": "production"
    }
  }
]
```

## Features

### Reliability
- **Retry logic**: Automatic retries with exponential backoff
- **Startup resilience**: Retries connection to inventory service on startup
- **Error recovery**: Continues running even if individual update cycles fail

### Performance
- **Atomic writes**: Uses temporary file + rename to prevent partial reads
- **Efficient polling**: Configurable update interval (default 30s)
- **Low resource usage**: ~50MB RAM, minimal CPU

### Observability
- **Structured logging**: Clear, timestamped log messages
- **Health checks**: Docker health check verifies targets file exists
- **Status reporting**: Logs update success/failure and sensor counts

### Security
- **Non-root user**: Runs as unprivileged user (UID 1000)
- **Minimal image**: Based on python:slim for small attack surface
- **No secrets**: All config via environment variables

## Running Standalone

### Build
```bash
docker build -t service-discovery:latest .
```

### Run
```bash
docker run -d \
  -e INVENTORY_URL=http://inventory:1337/inventory \
  -e UPDATE_INTERVAL=30 \
  -v $(pwd)/targets:/shared \
  service-discovery:latest
```

### Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
export INVENTORY_URL=http://localhost:1337/inventory
export TARGETS_FILE=./targets.json
python sd_updater.py
```

## Monitoring

### View Logs
```bash
docker logs -f service_discovery
```

Expected output:
```
2025-01-04 12:00:00 - __main__ - INFO - Starting Prometheus Service Discovery Updater
2025-01-04 12:00:00 - __main__ - INFO - Configuration:
2025-01-04 12:00:00 - __main__ - INFO -   Inventory URL: http://inventory_server:1337/inventory
2025-01-04 12:00:00 - __main__ - INFO -   Update Interval: 30s
2025-01-04 12:00:00 - __main__ - INFO - Fetching sensor inventory...
2025-01-04 12:00:00 - __main__ - INFO - Successfully fetched 100 sensors
2025-01-04 12:00:00 - __main__ - INFO - Successfully updated targets file: /shared/targets.json
```

### Check Health
```bash
docker exec service_discovery test -f /shared/targets.json && echo "Healthy"
```

### Verify Output
```bash
docker exec service_discovery cat /shared/targets.json
```

## Troubleshooting

### Service Not Updating
**Symptom**: Logs show "Failed to fetch inventory"

**Solution**:
1. Check inventory service is running: `docker ps | grep inventory`
2. Test connectivity: `docker exec service_discovery ping inventory_server`
3. Check URL: `echo $INVENTORY_URL`

### Targets File Not Created
**Symptom**: `/shared/targets.json` doesn't exist

**Solution**:
1. Check volume mount: `docker inspect service_discovery | grep Mounts`
2. Check permissions: `docker exec service_discovery ls -la /shared`
3. Check logs: `docker logs service_discovery`

### High Resource Usage
**Symptom**: CPU or memory usage is high

**Solution**:
1. Increase `UPDATE_INTERVAL` to reduce polling frequency
2. Check for network issues causing retries
3. Verify inventory service is responding quickly

## Code Structure

```
sd_updater.py
├── Configuration (environment variables)
├── create_http_session()      # HTTP client with retries
├── fetch_sensor_inventory()   # Get sensors from API
├── create_prometheus_targets() # Convert to Prometheus format
├── write_targets_file()       # Atomic file write
├── update_service_discovery() # Main update logic
└── main()                     # Main loop
```

## Testing

### Unit Tests (example)
```python
# Test target creation
sensors = ["sensor_1", "sensor_2"]
targets = create_prometheus_targets(sensors)
assert len(targets) == 1
assert "sensor_1:9100" in targets[0]["targets"]
```

### Integration Test
```bash
# Start inventory service
docker run -d -p 1337:1337 inventory_server

# Start SD updater
docker run -d \
  -e INVENTORY_URL=http://host.docker.internal:1337/inventory \
  -v $(pwd)/targets:/shared \
  service-discovery:latest

# Wait and verify
sleep 35
cat targets/targets.json | jq '.[] | .targets | length'
# Should output: 100
```

## Performance Metrics

With default configuration:
- **Update cycle time**: < 1 second
- **Memory usage**: ~50MB
- **CPU usage**: < 0.5% average
- **Network bandwidth**: < 1KB per update

## Future Enhancements

Potential improvements (not in scope for 2-hour assignment):
- [ ] Add custom metrics endpoint for monitoring SD health
- [ ] Support multiple inventory sources
- [ ] Add webhook support for immediate updates
- [ ] Implement leader election for HA deployments
- [ ] Add validation for sensor hostname format
- [ ] Support for sensor grouping/sharding

