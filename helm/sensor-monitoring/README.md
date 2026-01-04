# Sensor Monitoring Helm Chart

Production-ready Helm chart for deploying Trigo's sensor monitoring stack on Kubernetes.

## Overview

This chart deploys:
- **Inventory Server**: Provides dynamic sensor inventory
- **Service Discovery**: Updates Prometheus targets automatically
- **Prometheus**: Monitors all sensors and services

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PersistentVolume provisioner support (for production)

## Installation

### Quick Start

```bash
# Install with default values
helm install sensor-monitoring ./sensor-monitoring

# Install with custom values
helm install sensor-monitoring ./sensor-monitoring \
  --set prometheus.service.type=LoadBalancer \
  --set serviceDiscovery.config.updateInterval=60
```

### Custom Values

```bash
# Create custom values file
cat > custom-values.yaml <<EOF
prometheus:
  service:
    type: LoadBalancer
  storage:
    enabled: true
    size: 50Gi
    storageClass: fast-ssd
  resources:
    limits:
      memory: 4Gi
      cpu: 2000m

serviceDiscovery:
  config:
    updateInterval: 60
EOF

# Install with custom values
helm install sensor-monitoring ./sensor-monitoring -f custom-values.yaml
```

## Configuration

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.storageClass` | Global storage class | `""` |

### Inventory Server Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `inventoryServer.enabled` | Enable inventory server | `true` |
| `inventoryServer.replicaCount` | Number of replicas | `1` |
| `inventoryServer.image.repository` | Image repository | `inventory-server` |
| `inventoryServer.image.tag` | Image tag | `latest` |
| `inventoryServer.resources.limits.cpu` | CPU limit | `200m` |
| `inventoryServer.resources.limits.memory` | Memory limit | `128Mi` |

### Service Discovery Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `serviceDiscovery.enabled` | Enable service discovery | `true` |
| `serviceDiscovery.replicaCount` | Number of replicas | `1` |
| `serviceDiscovery.config.updateInterval` | Update interval (seconds) | `30` |
| `serviceDiscovery.config.metricsPort` | Sensor metrics port | `9100` |
| `serviceDiscovery.resources.limits.cpu` | CPU limit | `200m` |
| `serviceDiscovery.resources.limits.memory` | Memory limit | `128Mi` |

### Prometheus Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prometheus.enabled` | Enable Prometheus | `true` |
| `prometheus.replicaCount` | Number of replicas | `1` |
| `prometheus.service.type` | Service type | `NodePort` |
| `prometheus.service.nodePort` | NodePort | `30090` |
| `prometheus.retention.time` | Data retention time | `30d` |
| `prometheus.retention.size` | Data retention size | `10GB` |
| `prometheus.storage.enabled` | Enable persistent storage | `true` |
| `prometheus.storage.size` | Storage size | `20Gi` |
| `prometheus.resources.limits.cpu` | CPU limit | `1000m` |
| `prometheus.resources.limits.memory` | Memory limit | `2Gi` |

### Persistence Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable shared persistence | `true` |
| `persistence.storageClass` | Storage class | `""` |
| `persistence.size` | Storage size | `1Gi` |
| `persistence.accessMode` | Access mode | `ReadWriteMany` |

## Accessing Services

### Local Development (Minikube/Kind)

```bash
# Get service URLs
kubectl get svc -l app.kubernetes.io/name=sensor-monitoring

# Port forward Prometheus
kubectl port-forward svc/sensor-monitoring-prometheus 9090:9090

# Access at: http://localhost:9090
```

### Production (NodePort)

```bash
# Get NodePort
export NODE_PORT=$(kubectl get svc sensor-monitoring-prometheus -o jsonpath='{.spec.ports[0].nodePort}')
export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}')

echo "Prometheus: http://${NODE_IP}:${NODE_PORT}"
```

### Production (LoadBalancer)

```bash
# Wait for external IP
kubectl get svc sensor-monitoring-prometheus -w

# Get external IP
export EXTERNAL_IP=$(kubectl get svc sensor-monitoring-prometheus -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Prometheus: http://${EXTERNAL_IP}:9090"
```

## Upgrade

```bash
# Upgrade to new version
helm upgrade sensor-monitoring ./sensor-monitoring

# Upgrade with new values
helm upgrade sensor-monitoring ./sensor-monitoring -f new-values.yaml
```

## Uninstall

```bash
# Uninstall release
helm uninstall sensor-monitoring

# Delete PVCs (if needed)
kubectl delete pvc -l app.kubernetes.io/name=sensor-monitoring
```

## Monitoring

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=sensor-monitoring
```

### View Logs

```bash
# Service discovery logs
kubectl logs -f -l app.kubernetes.io/component=service-discovery

# Prometheus logs
kubectl logs -f -l app.kubernetes.io/component=prometheus

# Inventory logs
kubectl logs -f -l app.kubernetes.io/component=inventory
```

### Check Targets

```bash
# Port forward Prometheus
kubectl port-forward svc/sensor-monitoring-prometheus 9090:9090

# Open browser to http://localhost:9090/targets
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod -l app.kubernetes.io/name=sensor-monitoring

# Check PVC status
kubectl get pvc -l app.kubernetes.io/name=sensor-monitoring
```

### Service Discovery Not Working

```bash
# Check targets file
kubectl exec -it deployment/sensor-monitoring-sd -- cat /shared/targets.json

# Check connectivity to inventory
kubectl exec -it deployment/sensor-monitoring-sd -- \
  python3 -c "import requests; print(requests.get('http://sensor-monitoring-inventory:1337/inventory').json())"
```

### Storage Issues

If using `ReadWriteMany` access mode without a compatible storage class:

```yaml
# Option 1: Use ReadWriteOnce with single replica
persistence:
  accessMode: ReadWriteOnce

# Option 2: Use NFS or compatible storage class
persistence:
  storageClass: nfs-client
  accessMode: ReadWriteMany
```

## High Availability Setup

For production HA setup:

```yaml
# HA configuration
prometheus:
  replicaCount: 2
  resources:
    limits:
      memory: 4Gi
      cpu: 2000m
  storage:
    enabled: true
    size: 100Gi

serviceDiscovery:
  replicaCount: 2

inventoryServer:
  replicaCount: 3
```

## Security Considerations

1. **Network Policies**: Add network policies to restrict traffic
2. **RBAC**: Create service accounts with minimal permissions
3. **Secrets**: Store sensitive config in Kubernetes secrets
4. **TLS**: Enable TLS for Prometheus endpoint
5. **Authentication**: Add authentication to Prometheus

## Testing

```bash
# Run Helm lint
helm lint ./sensor-monitoring

# Dry run install
helm install sensor-monitoring ./sensor-monitoring --dry-run --debug

# Template validation
helm template sensor-monitoring ./sensor-monitoring | kubectl apply --dry-run=client -f -
```

## Examples

### Development Setup (Minikube)

```bash
helm install sensor-monitoring ./sensor-monitoring \
  --set prometheus.service.type=NodePort \
  --set prometheus.storage.enabled=false \
  --set persistence.accessMode=ReadWriteOnce
```

### Production Setup (AWS EKS)

```bash
helm install sensor-monitoring ./sensor-monitoring \
  --set prometheus.service.type=LoadBalancer \
  --set prometheus.storage.storageClass=gp3 \
  --set prometheus.storage.size=100Gi \
  --set persistence.storageClass=efs \
  --set persistence.accessMode=ReadWriteMany \
  --set prometheus.resources.limits.memory=8Gi \
  --set prometheus.resources.limits.cpu=4000m
```

### Production Setup (GKE)

```bash
helm install sensor-monitoring ./sensor-monitoring \
  --set prometheus.service.type=LoadBalancer \
  --set prometheus.storage.storageClass=pd-ssd \
  --set persistence.storageClass=standard-rwx \
  --set prometheus.retention.time=90d \
  --set prometheus.retention.size=100GB
```

## Architecture

```
┌─────────────────────────┐
│ Kubernetes Cluster      │
│                         │
│  ┌─────────────────┐   │
│  │ Inventory       │   │
│  │ Deployment      │   │
│  │ (Service)       │   │
│  └────────┬────────┘   │
│           │             │
│  ┌────────▼────────┐   │
│  │ Service         │   │
│  │ Discovery       │◄──┤─── Shared PVC (targets)
│  │ Deployment      │   │
│  └────────┬────────┘   │
│           │             │
│  ┌────────▼────────┐   │
│  │ Prometheus      │   │
│  │ Deployment      │   │
│  │ (NodePort/LB)   │   │
│  └─────────────────┘   │
│                         │
└─────────────────────────┘
```

## Support

For issues or questions:
1. Check logs: `kubectl logs -l app.kubernetes.io/name=sensor-monitoring`
2. Verify configuration: `helm get values sensor-monitoring`
3. Review events: `kubectl get events --sort-by='.lastTimestamp'`

