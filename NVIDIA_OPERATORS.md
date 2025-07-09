# NVIDIA Operators Management with OpenShift MCP Server

This guide covers how to manage NVIDIA operators and GPU workloads using the OpenShift MCP server.

## Overview

The OpenShift MCP server provides full support for NVIDIA operators through:
- **OLM Integration**: Automatic detection of NVIDIA GPU Operator
- **Comprehensive Logging**: Access to all NVIDIA operator pods and logs
- **Resource Monitoring**: Monitor GPU nodes, device plugins, and drivers
- **Troubleshooting**: Search across all NVIDIA-related logs and events

## Supported NVIDIA Operators

### NVIDIA GPU Operator
- **Purpose**: Manages GPU drivers, CUDA runtime, device plugin, and monitoring
- **Installation**: Via Red Hat Operator Hub or NVIDIA Operator Catalog
- **Components**:
  - GPU Driver DaemonSet
  - CUDA Runtime
  - Device Plugin
  - GPU Feature Discovery
  - DCGM Exporter
  - MIG Manager (for A100/H100)

### NVIDIA Network Operator
- **Purpose**: Manages NVIDIA networking components (Mellanox/ConnectX)
- **Components**:
  - OFED Driver
  - SR-IOV Device Plugin
  - RDMA Shared Device Plugin

### NVIDIA BlueField DPU Support
- **Purpose**: Comprehensive BlueField Data Processing Unit management
- **Components**:
  - BlueField DPU Operator (via Network Operator)
  - BlueField BSN (BlueField Software for Networking)
  - DPU Driver Management
  - Network Offloading Configuration
  - SR-IOV and RDMA for BlueField
  - BlueField DOCA (Data Center on-a-Chip Architecture)

## Prerequisites

### OpenShift Cluster Setup
```bash
# Ensure your OpenShift cluster has GPU nodes
oc get nodes -l node.openshift.io/instance-type

# Label GPU nodes (if not auto-detected)
oc label node <gpu-node-name> nvidia.com/gpu=true
```

### MCP Server Configuration
```json
{
  "mcpServers": {
    "openshift-nvidia": {
      "command": "podman",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/home/user/.kube:/root/.kube:ro",
        "-e", "KUBECONFIG_PATH=/root/.kube/config",
        "-e", "MCP_TRANSPORT=stdio",
        "quay.io/redhat-ai-tools/openshift-operator-log-server"
      ]
    }
  }
}
```

## NVIDIA Operator Management Examples

### 1. Check if NVIDIA GPU Operator is Installed

```python
# List all operators to find NVIDIA GPU Operator
get_all_operators("all")
```

Expected output will include:
```json
{
  "type": "OLM",
  "name": "gpu-operator-certified",
  "namespace": "nvidia-gpu-operator",
  "package": "gpu-operator-certified",
  "channel": "stable",
  "source": "certified-operators",
  "csv_info": {
    "display_name": "NVIDIA GPU Operator",
    "version": "23.9.1",
    "description": "Automates the management of all NVIDIA software components needed to provision GPU",
    "phase": "Succeeded"
  }
}
```

### 2. Get All NVIDIA Operator Pods

```python
# Get pods for NVIDIA GPU Operator
get_operator_pods("gpu-operator", "nvidia-gpu-operator")
```

This will return all pods managed by the NVIDIA GPU Operator:
```json
[
  {
    "name": "gpu-operator-5f7b9d4c8-xyz12",
    "namespace": "nvidia-gpu-operator",
    "status": "Running",
    "ready": 1,
    "containers": 1,
    "node": "worker-gpu-1"
  },
  {
    "name": "nvidia-driver-daemonset-abc34",
    "namespace": "nvidia-gpu-operator",
    "status": "Running",
    "ready": 1,
    "containers": 1,
    "node": "worker-gpu-1"
  }
]
```

### 3. Get Comprehensive NVIDIA Operator Logs

```python
# Get all logs from NVIDIA GPU Operator
get_comprehensive_logs("operator", "gpu-operator", "nvidia-gpu-operator", "all", 200)
```

### 4. Monitor GPU Driver Installation

```python
# Search for driver-related logs
search_all_logs("driver", "nvidia-gpu-operator", "all", 100)
```

### 5. Check GPU Device Plugin Status

```python
# Search for device plugin logs
search_all_logs("device-plugin", "nvidia-gpu-operator", "pod", 50)
```

### 6. Monitor DCGM Exporter (GPU Metrics)

```python
# Get DCGM exporter logs
search_all_logs("dcgm", "nvidia-gpu-operator", "pod", 100)
```

## Troubleshooting Common Issues

### GPU Driver Issues

```python
# Check driver installation logs
search_all_logs("nvidia-driver", "nvidia-gpu-operator", "all", 200)

# Look for driver compilation errors
search_all_logs("ERROR", "nvidia-gpu-operator", "all", 100)
```

### Device Plugin Problems

```python
# Check device plugin registration
search_all_logs("device-plugin", "nvidia-gpu-operator", "pod", 100)

# Look for GPU discovery issues
search_all_logs("ListAndWatch", "nvidia-gpu-operator", "pod", 50)
```

### CUDA Runtime Issues

```python
# Check CUDA container toolkit
search_all_logs("nvidia-container-toolkit", "nvidia-gpu-operator", "all", 100)
```

### Node Feature Discovery

```python
# Check GPU feature discovery
search_all_logs("gpu-feature-discovery", "nvidia-gpu-operator", "pod", 100)
```

## Advanced GPU Management

### MIG (Multi-Instance GPU) Management

```python
# Check MIG manager logs (for A100/H100)
search_all_logs("mig-manager", "nvidia-gpu-operator", "pod", 100)

# Look for MIG configuration changes
search_all_logs("MIG", "nvidia-gpu-operator", "all", 50)
```

### GPU Monitoring and Metrics

```python
# Check DCGM exporter metrics
search_all_logs("dcgm-exporter", "nvidia-gpu-operator", "pod", 100)

# Monitor GPU utilization alerts
search_all_logs("gpu utilization", "all", "event", 50)
```

### Time-Slicing Configuration

```python
# Check time-slicing configuration
search_all_logs("time-slicing", "nvidia-gpu-operator", "all", 100)
```

## GPU Workload Management

### Check GPU-enabled Applications

```python
# Find pods requesting GPU resources
search_all_logs("nvidia.com/gpu", "all", "event", 100)

# Check GPU resource allocation
get_openshift_resources("configmaps", "nvidia-gpu-operator")
```

### Monitor GPU Workload Logs

```python
# Get logs from GPU workload pods
get_comprehensive_logs("pod", "my-gpu-workload", "my-project", "all", 200)
```

## Event Monitoring

### GPU-Related Events

```python
# Monitor GPU-related cluster events
search_all_logs("gpu", "all", "event", 100)

# Check for GPU scheduling issues
search_all_logs("Insufficient nvidia.com/gpu", "all", "event", 50)
```

### Driver Update Events

```python
# Monitor driver updates
search_all_logs("driver upgrade", "nvidia-gpu-operator", "event", 50)
```

## OpenShift-Specific GPU Features

### Node Tuning for GPU

```python
# Check node tuning operator interaction
search_all_logs("node-tuning", "all", "all", 100)
```

### Security Context Constraints

```python
# Check GPU-related SCCs
get_openshift_resources("secrets", "nvidia-gpu-operator")
```

### GPU in OpenShift AI/ML Workflows

```python
# Monitor OpenShift AI workloads with GPU
search_all_logs("opendatahub", "all", "all", 100)
search_all_logs("kubeflow", "all", "all", 100)
```

## Complete NVIDIA Operator Health Check

Here's a comprehensive health check script using the MCP server:

```python
# 1. Check if NVIDIA operators are installed
print("=== NVIDIA Operators ===")
operators = get_all_operators("all")
# Filter for NVIDIA operators

# 2. Check operator pods health
print("=== Operator Pods Health ===")
gpu_pods = get_operator_pods("gpu-operator", "nvidia-gpu-operator")

# 3. Check recent logs for errors
print("=== Recent Error Logs ===")
errors = search_all_logs("ERROR", "nvidia-gpu-operator", "all", 100)

# 4. Check GPU node readiness
print("=== GPU Node Events ===")
gpu_events = search_all_logs("gpu", "all", "event", 50)

# 5. Check driver status
print("=== Driver Status ===")
driver_logs = search_all_logs("nvidia-driver", "nvidia-gpu-operator", "pod", 100)

# 6. Check device plugin
print("=== Device Plugin Status ===")
device_logs = search_all_logs("device-plugin", "nvidia-gpu-operator", "pod", 50)
```

## Best Practices

### 1. Regular Monitoring
- Monitor NVIDIA operator logs regularly
- Check for driver compilation issues
- Watch for GPU scheduling problems

### 2. Resource Management
- Monitor GPU utilization via DCGM exporter
- Set appropriate resource limits
- Use time-slicing for development workloads

### 3. Troubleshooting
- Always check operator logs first
- Verify node labeling and taints
- Check Security Context Constraints

### 4. Updates and Maintenance
- Monitor operator updates via OLM
- Check compatibility with OpenShift versions
- Test driver updates in non-production first

## Integration with OpenShift Features

### OpenShift AI/ML Platform
The NVIDIA operators integrate seamlessly with:
- **OpenShift AI**: Automated GPU provisioning for notebooks
- **OpenShift Pipelines**: GPU-accelerated CI/CD
- **OpenShift Serverless**: GPU-enabled serverless functions

### Monitoring and Alerting
- **OpenShift Monitoring**: GPU metrics via DCGM
- **Grafana Dashboards**: GPU utilization and health
- **AlertManager**: GPU-related alerts

This comprehensive setup ensures you can fully manage, monitor, and troubleshoot NVIDIA operators in your OpenShift cluster using the MCP server.

## BlueField DPU Management

### 1. Check BlueField DPU Operators

```python
# Get all NVIDIA operators including BlueField DPU
get_nvidia_operators("all")
```

Expected output will include BlueField operators:
```json
{
  "type": "OLM",
  "name": "network-operator",
  "namespace": "nvidia-network-operator",
  "package": "network-operator",
  "channel": "stable",
  "source": "certified-operators",
  "csv_info": {
    "display_name": "NVIDIA Network Operator",
    "version": "23.10.0",
    "description": "Automates deployment and management of NVIDIA networking components including BlueField DPU",
    "phase": "Succeeded"
  }
}
```

### 2. Get BlueField DPU Nodes

```python
# Get all nodes with BlueField DPU resources
get_gpu_nodes()
```

This will return nodes with BlueField DPU resources:
```json
[
  {
    "name": "worker-dpu-1",
    "labels": {
      "node.kubernetes.io/instance-type": "Standard_DPU",
      "nvidia.com/dpu": "true",
      "nvidia.com/bluefield": "true"
    },
    "gpu_resources": {
      "nvidia.com/dpu": "1",
      "nvidia.com/sriov_net_a2": "128"
    },
    "nvidia_labels": {
      "nvidia.com/dpu": "true",
      "nvidia.com/bluefield": "true",
      "nvidia.com/dpu.family": "BlueField-3"
    }
  }
]
```

### 3. Monitor BlueField DPU Health

```python
# Check BlueField DPU operator health
get_gpu_operator_health()
```

### 4. Search BlueField DPU Logs

```python
# Search for BlueField-specific logs
search_gpu_logs("bluefield", "pod", 100)
search_gpu_logs("dpu", "all", 100)
search_gpu_logs("ofed", "pod", 50)
```

### 5. Get BlueField DPU Workloads

```python
# Get all pods requesting DPU resources
get_gpu_workloads("all")
```

This will return pods using BlueField DPU resources:
```json
[
  {
    "name": "dpu-accelerated-app",
    "namespace": "networking",
    "status": "Running",
    "node": "worker-dpu-1",
    "gpu_requests": {
      "nvidia.com/dpu": "1",
      "nvidia.com/sriov_net_a2": "2"
    },
    "gpu_limits": {
      "nvidia.com/dpu": "1",
      "nvidia.com/sriov_net_a2": "2"
    }
  }
]
```

## BlueField DPU Troubleshooting

### DPU Driver Issues

```python
# Check BlueField driver logs
search_gpu_logs("bluefield-driver", "all", 200)
search_gpu_logs("mlx5", "all", 100)
```

### Network Offloading Problems

```python
# Check network offloading logs
search_gpu_logs("ovs-hw-offload", "all", 100)
search_gpu_logs("tc-flower", "all", 50)
```

### SR-IOV Configuration

```python
# Check SR-IOV device plugin for BlueField
search_gpu_logs("sriov-device-plugin", "all", 100)
search_gpu_logs("sriov-network-operator", "all", 100)
```

### RDMA and InfiniBand

```python
# Check RDMA shared device plugin
search_gpu_logs("rdma-shared-device-plugin", "all", 100)
search_gpu_logs("rdma", "all", 50)
```

## BlueField DPU Advanced Features

### DOCA (Data Center on-a-Chip Architecture)

```python
# Monitor DOCA applications
search_gpu_logs("doca", "all", 100)
```

### BlueField Software for Networking (BSN)

```python
# Check BSN logs
search_gpu_logs("bsn", "all", 100)
search_gpu_logs("bluefield-software", "all", 50)
```

### DPU Resource Management

```python
# Check DPU resource allocation
get_openshift_resources("configmaps", "nvidia-network-operator")
```

## BlueField DPU Integration with OpenShift

### OpenShift SDN with BlueField Acceleration

```python
# Monitor OpenShift SDN hardware offload
search_all_logs("hw-offload", "openshift-sdn", "all", 100)
```

### OpenShift Service Mesh with BlueField

```python
# Check service mesh acceleration
search_all_logs("istio", "all", "all", 100)
search_gpu_logs("envoy", "all", 50)
```

### BlueField DPU in OpenShift Virtualization

```python
# Monitor CNV with BlueField acceleration
search_all_logs("virt-handler", "openshift-cnv", "all", 100)
search_gpu_logs("kubevirt", "all", 100)
```