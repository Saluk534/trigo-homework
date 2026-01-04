# Quick Start Guide

## 🚀 Get Started in 60 Seconds

### 1. Start the Stack
```bash
docker-compose up -d
```

### 2. Wait for Services (about 10-15 seconds)
```bash
docker-compose ps
```

### 3. Open Prometheus
Visit: **http://localhost:9090**

### 4. View Discovered Targets
Click on: **Status → Targets** or visit http://localhost:9090/targets

You should see:
- ✅ `prometheus` job - Prometheus monitoring itself
- ✅ `inventory_service` job - The inventory API
- ✅ `sensors` job - ~100 dynamically discovered sensors

## 🧪 Quick Tests

### Test Inventory Service
```bash
curl http://localhost:1337/inventory
```
Should return: `["sensor_0", "sensor_1", ..., "sensor_99"]`

### Check Service Discovery
```bash
docker exec service_discovery cat /shared/targets.json
```
Should show Prometheus target format with all sensors

### View Logs
```bash
docker-compose logs -f service_discovery
```
Should show periodic updates every 30 seconds

## 🛠 Useful Commands

### Stop Everything
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Clean Restart (remove all data)
```bash
docker-compose down -v
docker-compose up -d
```

### View All Logs
```bash
docker-compose logs -f
```

## 📊 What's Happening?

1. **Inventory Server** (port 1337) - Serves list of 100 sensors
2. **Service Discovery** - Queries inventory every 30s, writes to `/shared/targets.json`
3. **Prometheus** (port 9090) - Reads targets file, tries to scrape all sensors

## ❓ Troubleshooting

### Services Not Starting?
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Can't Access Prometheus?
Make sure port 9090 is not in use:
```bash
netstat -an | grep 9090
```

### Need to Check Health?
```bash
docker-compose ps
```
All services should show `Up (healthy)`

## 📚 More Information

See [SOLUTION.md](./SOLUTION.md) for complete documentation.

