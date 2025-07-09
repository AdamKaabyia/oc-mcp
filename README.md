# OpenShift Operator & Log Management Server

Comprehensive MCP server for managing **ALL operators** and **ALL types of logs** across OpenShift clusters including:
- **All OpenShift Operators** (OLM operators, Helm operators, custom operators)
- **All Log Types** (pod logs, operator logs, build logs, event logs, OCM logs)
- **OpenShift-specific Resources** (projects, routes, image streams, security contexts)
- **OCM Integration** (managed cluster support)

## Features

### Comprehensive Operator Management
- **OLM Operators**: Full Operator Lifecycle Manager integration
- **Helm Operators**: Helm chart repository and release management
- **Custom Operators**: Detection and management of custom operator deployments
- **Operator Pods**: Automatic discovery of pods belonging to operators
- **Operator Logs**: Aggregated logs from all operator pods
- **Operator Catalog**: Browse available operators from catalogs

### Universal Log Management
- **Pod Logs**: Get logs from any pod with container-specific filtering
- **Operator Logs**: Aggregate logs from all pods belonging to any operator
- **Build Logs**: OpenShift build configuration and build logs
- **Event Logs**: Comprehensive cluster events and system messages
- **OCM Logs**: Service logs from OpenShift Cluster Manager
- **Universal Search**: Search across all log types simultaneously

### OpenShift-Specific Features
- **Projects**: OpenShift project management with quotas and limits
- **Routes**: OpenShift route management and exposure
- **Image Streams**: Container image management and registry integration
- **Security Context Constraints**: Security policy management
- **Build Configs**: OpenShift build pipeline management
- **Custom Resources**: Query any CRD and custom resources

### OCM Integration
- **Managed Clusters**: List and inspect OCM-managed clusters
- **Cluster Lifecycle**: Monitor cluster state and versions
- **Service Logs**: Access OCM service logs and diagnostics

## Configuration

### Environment Variables

#### OpenShift Configuration
- `KUBECONFIG_PATH`: Path to kubeconfig file (default: `~/.kube/config`)

#### OCM Configuration (optional)
- `OCM_CLIENT_ID`: OCM client ID
- `OCM_OFFLINE_TOKEN`: OCM offline token
- `ACCESS_TOKEN_URL`: OCM token endpoint
- `OCM_API_BASE`: OCM API base URL (default: `https://api.openshift.com`)

#### Server Configuration
- `MCP_TRANSPORT`: Transport method (`stdio` or `sse`, default: `stdio`)

## Running with Container

### Basic OpenShift access
```json
{
  "mcpServers": {
    "openshift-server": {
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

### With OCM support
```json
{
  "mcpServers": {
    "openshift-server": {
      "command": "podman",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/home/user/.kube:/root/.kube:ro",
        "-e", "KUBECONFIG_PATH=/root/.kube/config",
        "-e", "ACCESS_TOKEN_URL",
        "-e", "OCM_CLIENT_ID",
        "-e", "OCM_OFFLINE_TOKEN",
        "-e", "MCP_TRANSPORT=stdio",
        "quay.io/redhat-ai-tools/openshift-operator-log-server"
      ],
      "env": {
        "ACCESS_TOKEN_URL": "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
        "OCM_CLIENT_ID": "cloud-services",
        "OCM_OFFLINE_TOKEN": "REDACTED"
      }
    }
  }
}
```

### Running with SSE transport
```json
{
  "mcpServers": {
    "openshift-server": {
      "url": "http://localhost:8004/sse",
      "headers": {
        "X-OCM-Offline-Token": "REDACTED"
      }
    }
  }
}
```

## Available Tools

### System Information
- `get_cluster_info()`: Get comprehensive cluster information and capabilities

### OpenShift Project Management
- `get_projects()`: List all projects with quotas and resource limits

### Comprehensive Operator Management
- `get_all_operators(project)`: List ALL operators (OLM, Helm, Custom)
- `get_operator_pods(operator_name, project)`: Get all pods for an operator
- `get_comprehensive_logs(resource_type, resource_name, project, log_type, lines)`: Get all logs for any resource

### Universal Log Management
- `search_all_logs(query, project, resource_types, lines)`: Search across ALL log types
- `get_comprehensive_logs(resource_type, resource_name, project, log_type, lines)`: Get comprehensive logs from any resource

### OpenShift Resources
- `get_openshift_resources(resource_type, project)`: Get routes, services, configmaps, secrets, imagestreams

### NVIDIA GPU Management
- `get_nvidia_operators(project)`: Get all NVIDIA operators (GPU, Network, etc.)
- `get_gpu_nodes()`: Get all GPU-enabled nodes with detailed information
- `get_gpu_operator_health()`: Comprehensive NVIDIA GPU Operator health check
- `search_gpu_logs(query, log_type, lines)`: Search specifically in GPU/NVIDIA logs
- `get_gpu_workloads(project)`: Get all pods requesting GPU resources

### BlueField DPU Management
- `get_bluefield_dpu_nodes()`: Get all BlueField DPU-enabled nodes with detailed DPU information
- `get_bluefield_dpu_workloads(project)`: Get all pods requesting BlueField DPU resources
- `get_bluefield_dpu_health()`: Comprehensive BlueField DPU infrastructure health check
- `search_bluefield_dpu_logs(query, log_type, lines)`: Search specifically in BlueField DPU logs

### OCM Integration
- `ocm_get_clusters()`: List OCM managed clusters
- `ocm_get_cluster_logs(cluster_id)`: Get OCM service logs

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

For comprehensive instructions on running the server with different cluster options, see [GETTING_STARTED.md](GETTING_STARTED.md).

Quick start:
```bash
# With an existing OpenShift cluster
export KUBECONFIG_PATH=~/.kube/config
python openshift_mcp_server.py

# Run with SSE transport
MCP_TRANSPORT=sse python openshift_mcp_server.py
```

## Examples

### Search for errors across ALL logs and resources
```python
search_all_logs("error", "all", "all", 100)
```

### Get comprehensive logs from any operator
```python
get_comprehensive_logs("operator", "cluster-monitoring-operator", "openshift-monitoring", "all", 200)
```

### List ALL operators in the cluster
```python
get_all_operators("all")
```

### Get logs from builds
```python
get_comprehensive_logs("build", "my-app-build", "my-project", "build", 100)
```

### Search pod logs across all projects
```python
search_all_logs("connection refused", "all", "pod", 50)
```

### Get OpenShift routes
```python
get_openshift_resources("routes", "all")
```

### Monitor image streams
```python
get_openshift_resources("imagestreams", "openshift")
```

### Check NVIDIA GPU Operator health
```python
get_gpu_operator_health()
```

### Get all GPU workloads
```python
get_gpu_workloads("all")
```

### Search GPU-specific logs
```python
search_gpu_logs("driver", "pod", 100)
```

### Get BlueField DPU nodes
```python
get_bluefield_dpu_nodes()
```

### Check BlueField DPU health
```python
get_bluefield_dpu_health()
```

### Get all BlueField DPU workloads
```python
get_bluefield_dpu_workloads("all")
```

### Search BlueField DPU logs
```python
search_bluefield_dpu_logs("ofed", "pod", 100)
```

## Supported Resource Types

### Operators
- **OLM Operators**: Installed via Operator Lifecycle Manager
- **Helm Operators**: Installed via Helm charts
- **Custom Operators**: Custom deployments acting as operators

### Logs
- **Pod Logs**: From any pod in any namespace
- **Operator Logs**: Aggregated from all operator pods
- **Build Logs**: From OpenShift build configurations
- **Event Logs**: Cluster events and system messages
- **OCM Logs**: Service logs from managed clusters

### OpenShift Resources
- **Projects**: OpenShift projects with quotas
- **Routes**: OpenShift external access routes
- **Services**: Kubernetes services
- **ConfigMaps**: Configuration data
- **Secrets**: Sensitive data
- **ImageStreams**: Container image repositories

## Architecture

The server provides a unified interface to:
1. **OpenShift API**: Direct cluster access via kubeconfig
2. **Dynamic Client**: Access to custom resources and CRDs
3. **OCM API**: Managed cluster integration
4. **Log Aggregation**: Unified search across all log sources

All tools are designed to work seamlessly whether you're using self-managed OpenShift or OCM-managed clusters.

## NVIDIA GPU Support

The server provides comprehensive support for NVIDIA operators and GPU workloads. For detailed information on managing NVIDIA GPU operators, see [NVIDIA_OPERATORS.md](NVIDIA_OPERATORS.md).

Key NVIDIA features:
- **Automatic Detection**: All NVIDIA operators via OLM integration
- **GPU Node Management**: Monitor GPU-enabled nodes and resources
- **BlueField DPU Support**: Full BlueField DPU infrastructure management
- **Comprehensive Health Checks**: Full GPU and DPU operator health monitoring
- **Specialized Log Search**: GPU and DPU-specific log filtering and search
- **Workload Monitoring**: Track all GPU and DPU-requesting pods and containers
