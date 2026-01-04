# Deployment Guide

This document provides deployment instructions for both Docker Compose and Kubernetes (Helm) environments.

## Table of Contents
- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes (Helm) Deployment](#kubernetes-helm-deployment)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Docker Compose Deployment

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+

### Quick Deployment

```bash
# Clone repository
git clone <repository-url>
cd trigo-homework

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Access Services

| Service | URL | Description |
|---------|-----|-------------|
| Prometheus | http://localhost:9090 | Monitoring dashboard |
| Inventory | http://localhost:1337/inventory | Sensor inventory API |

### Verify Deployment

```bash
# Test inventory service
curl http://localhost:1337/inventory

# Check service discovery output
docker exec service_discovery cat /shared/targets.json

# View Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.scrapePool=="sensors") | .discoveredLabels'
```

### Stop Services

```bash
# Stop without removing volumes
docker-compose stop

# Stop and remove everything
docker-compose down

# Stop and remove with volumes
docker-compose down -v
```

---

## Kubernetes (Helm) Deployment

### Prerequisites
- Kubernetes 1.19+
- Helm 3.0+
- kubectl configured

### Build Docker Images

First, build and push Docker images to your registry:

```bash
# Build inventory server
cd inventory_server
docker build -t your-registry/inventory-server:latest .
docker push your-registry/inventory-server:latest

# Build service discovery
cd ../service_discovery
docker build -t your-registry/service-discovery:latest .
docker push your-registry/service-discovery:latest
```

### Deploy with Helm

#### Option 1: Default Configuration

```bash
# Create namespace
kubectl create namespace sensor-monitoring

# Install chart
helm install sensor-monitoring ./helm/sensor-monitoring \
  --namespace sensor-monitoring \
  --set inventoryServer.image.repository=your-registry/inventory-server \
  --set serviceDiscovery.image.repository=your-registry/service-discovery
```

#### Option 2: Custom Configuration

Create a `custom-values.yaml` file:

```yaml
# Image configuration
inventoryServer:
  image:
    repository: your-registry/inventory-server
    tag: "v1.0.0"

serviceDiscovery:
  image:
    repository: your-registry/service-discovery
    tag: "v1.0.0"
  config:
    updateInterval: 60  # Update every 60 seconds

# Prometheus configuration
prometheus:
  service:
    type: LoadBalancer  # Use LoadBalancer in cloud
  storage:
    enabled: true
    size: 50Gi
    storageClass: fast-ssd
  resources:
    limits:
      memory: 4Gi
      cpu: 2000m

# Persistence configuration
persistence:
  storageClass: standard-rwx
```

Deploy with custom values:

```bash
helm install sensor-monitoring ./helm/sensor-monitoring \
  --namespace sensor-monitoring \
  --values custom-values.yaml
```

### Local Kubernetes (Minikube/Kind)

For local development without storage classes:

```bash
helm install sensor-monitoring ./helm/sensor-monitoring \
  --namespace sensor-monitoring \
  --set inventoryServer.image.pullPolicy=Never \
  --set serviceDiscovery.image.pullPolicy=Never \
  --set prometheus.storage.enabled=false \
  --set persistence.accessMode=ReadWriteOnce
```

### Cloud Provider Specific Deployments

#### AWS EKS

```bash
helm install sensor-monitoring ./helm/sensor-monitoring \
  --namespace sensor-monitoring \
  --set inventoryServer.image.repository=your-ecr-url/inventory-server \
  --set serviceDiscovery.image.repository=your-ecr-url/service-discovery \
  --set prometheus.service.type=LoadBalancer \
  --set prometheus.storage.storageClass=gp3 \
  --set persistence.storageClass=efs
```

#### Google GKE

```bash
helm install sensor-monitoring ./helm/sensor-monitoring \
  --namespace sensor-monitoring \
  --set inventoryServer.image.repository=gcr.io/your-project/inventory-server \
  --set serviceDiscovery.image.repository=gcr.io/your-project/service-discovery \
  --set prometheus.service.type=LoadBalancer \
  --set prometheus.storage.storageClass=pd-ssd \
  --set persistence.storageClass=standard-rwx
```

#### Azure AKS

```bash
helm install sensor-monitoring ./helm/sensor-monitoring \
  --namespace sensor-monitoring \
  --set inventoryServer.image.repository=your-acr-url.azurecr.io/inventory-server \
  --set serviceDiscovery.image.repository=your-acr-url.azurecr.io/service-discovery \
  --set prometheus.service.type=LoadBalancer \
  --set prometheus.storage.storageClass=managed-premium \
  --set persistence.storageClass=azurefile
```

### Access Services

#### Port Forward (Development)

```bash
# Prometheus
kubectl port-forward -n sensor-monitoring svc/sensor-monitoring-prometheus 9090:9090

# Inventory service
kubectl port-forward -n sensor-monitoring svc/sensor-monitoring-inventory 1337:1337

# Access at http://localhost:9090 and http://localhost:1337
```

#### LoadBalancer (Production)

```bash
# Get external IP
kubectl get svc -n sensor-monitoring sensor-monitoring-prometheus

# Wait for EXTERNAL-IP to be assigned
export PROM_IP=$(kubectl get svc -n sensor-monitoring sensor-monitoring-prometheus -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Prometheus: http://${PROM_IP}:9090"
```

#### NodePort (On-Premise)

```bash
# Get node IP and port
export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
export NODE_PORT=$(kubectl get svc -n sensor-monitoring sensor-monitoring-prometheus -o jsonpath='{.spec.ports[0].nodePort}')

echo "Prometheus: http://${NODE_IP}:${NODE_PORT}"
```

### Verify Kubernetes Deployment

```bash
# Check pods
kubectl get pods -n sensor-monitoring

# Expected output:
# NAME                                              READY   STATUS    RESTARTS   AGE
# sensor-monitoring-inventory-xxxx                  1/1     Running   0          2m
# sensor-monitoring-prometheus-xxxx                 1/1     Running   0          2m
# sensor-monitoring-sd-xxxx                         1/1     Running   0          2m

# Check services
kubectl get svc -n sensor-monitoring

# Check PVCs
kubectl get pvc -n sensor-monitoring

# View logs
kubectl logs -n sensor-monitoring -l app.kubernetes.io/component=service-discovery -f
```

### Update Deployment

```bash
# Update with new values
helm upgrade sensor-monitoring ./helm/sensor-monitoring \
  --namespace sensor-monitoring \
  --values custom-values.yaml

# Rollback if needed
helm rollback sensor-monitoring --namespace sensor-monitoring
```

### Uninstall

```bash
# Uninstall release
helm uninstall sensor-monitoring --namespace sensor-monitoring

# Delete namespace and all resources
kubectl delete namespace sensor-monitoring
```

---

## Verification

### Test 1: Inventory Service

```bash
# Docker Compose
curl http://localhost:1337/inventory

# Kubernetes
kubectl run -n sensor-monitoring curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://sensor-monitoring-inventory:1337/inventory
```

Expected: JSON array with 100 sensors

### Test 2: Service Discovery

```bash
# Docker Compose
docker exec service_discovery cat /shared/targets.json

# Kubernetes
kubectl exec -n sensor-monitoring deployment/sensor-monitoring-sd -- cat /shared/targets.json
```

Expected: Prometheus target format with sensors

### Test 3: Prometheus Targets

```bash
# Docker Compose
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.scrapePool=="sensors") | .labels'

# Kubernetes (with port-forward)
kubectl port-forward -n sensor-monitoring svc/sensor-monitoring-prometheus 9090:9090
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.scrapePool=="sensors") | .labels'
```

Expected: List of sensor targets

### Test 4: Health Checks

```bash
# Docker Compose
docker-compose ps

# Kubernetes
kubectl get pods -n sensor-monitoring
```

All services should show healthy status

---

## Troubleshooting

### Docker Compose Issues

#### Port Conflicts
```bash
# Check if ports are in use
netstat -an | grep -E '1337|9090'

# Change ports in docker-compose.yml
ports:
  - "9091:9090"  # Use different host port
```

#### Container Crashes
```bash
# View logs
docker-compose logs service_name

# Restart specific service
docker-compose restart service_name

# Full rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

#### Volume Permissions
```bash
# Fix volume permissions
docker-compose down
sudo rm -rf ./prometheus_data
docker-compose up -d
```

### Kubernetes Issues

#### Pods Not Starting
```bash
# Check pod events
kubectl describe pod -n sensor-monitoring pod-name

# Common issues:
# - Image pull errors: Check image repository and credentials
# - Resource limits: Check resource requests/limits
# - PVC binding: Check PVC status
```

#### PVC Binding Issues
```bash
# Check PVC status
kubectl get pvc -n sensor-monitoring

# Check storage classes
kubectl get storageclass

# Solution: Use available storage class or disable persistence
helm upgrade sensor-monitoring ./helm/sensor-monitoring \
  --set prometheus.storage.enabled=false \
  --set persistence.accessMode=ReadWriteOnce
```

#### Service Discovery Not Working
```bash
# Check connectivity
kubectl exec -n sensor-monitoring deployment/sensor-monitoring-sd -- \
  wget -O- http://sensor-monitoring-inventory:1337/inventory

# Check targets file
kubectl exec -n sensor-monitoring deployment/sensor-monitoring-sd -- \
  cat /shared/targets.json

# Check logs
kubectl logs -n sensor-monitoring -l app.kubernetes.io/component=service-discovery -f
```

#### Prometheus Not Scraping
```bash
# Check Prometheus config
kubectl exec -n sensor-monitoring deployment/sensor-monitoring-prometheus -- \
  cat /etc/prometheus/prometheus.yml

# Check targets directory
kubectl exec -n sensor-monitoring deployment/sensor-monitoring-prometheus -- \
  ls -la /etc/prometheus/targets/

# Reload Prometheus config
kubectl exec -n sensor-monitoring deployment/sensor-monitoring-prometheus -- \
  wget --post-data="" http://localhost:9090/-/reload
```

### General Debugging

#### Enable Debug Logging

Docker Compose:
```yaml
# Add to service_discovery in docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

Kubernetes:
```yaml
# Add to values.yaml
serviceDiscovery:
  config:
    logLevel: DEBUG
```

#### Network Connectivity

```bash
# Docker Compose
docker-compose exec service_discovery ping inventory_server

# Kubernetes
kubectl exec -n sensor-monitoring deployment/sensor-monitoring-sd -- \
  ping sensor-monitoring-inventory
```

#### Check Resource Usage

```bash
# Docker Compose
docker stats

# Kubernetes
kubectl top pods -n sensor-monitoring
kubectl top nodes
```

---

## Production Checklist

Before deploying to production:

- [ ] Docker images are tagged with specific versions (not `latest`)
- [ ] Resource limits are configured appropriately
- [ ] Persistent storage is enabled and tested
- [ ] Health checks are working
- [ ] Monitoring and alerting are configured
- [ ] Backup strategy is in place for Prometheus data
- [ ] Network policies are configured (Kubernetes)
- [ ] TLS/authentication is enabled for Prometheus
- [ ] Security scanning is performed on Docker images
- [ ] Documentation is updated with environment-specific details

---

## Next Steps

After successful deployment:

1. **Configure Alerting**: Set up Alertmanager for sensor down alerts
2. **Add Dashboards**: Create Grafana dashboards for visualization
3. **Enable Authentication**: Secure Prometheus with OAuth/LDAP
4. **Set up Backups**: Configure regular backups of Prometheus data
5. **Performance Tuning**: Adjust scrape intervals and retention based on needs
6. **High Availability**: Deploy multiple replicas in production

