# Getting Started with OpenShift MCP Server

This guide shows you how to run and test the OpenShift MCP server. **Most users will want to use Option 1 with an existing OpenShift cluster.**

## **🚀 Quick Start (Recommended)**

### **Prerequisites**
- Access to an OpenShift cluster (most common scenario)
- `oc` CLI installed and configured
- Python 3.8+ installed

### **1. Verify OpenShift Access**
```bash
# Check if you have cluster access
oc whoami
oc get nodes
oc get projects

# Check permissions
oc auth can-i get pods --all-namespaces
oc auth can-i get operators --all-namespaces
```

### **2. Set Up the Server**
```bash
# Clone or navigate to project
cd oc-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Configure Environment**
```bash
# Basic configuration (most users only need this)
export KUBECONFIG_PATH=~/.kube/config
export MCP_TRANSPORT=stdio

# Optional: For managed clusters (OCM)
export OCM_CLIENT_ID=cloud-services
export OCM_OFFLINE_TOKEN=your-token
export ACCESS_TOKEN_URL=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
```

### **4. Run the Server**
```bash
# Run locally with stdio transport (recommended for testing)
python openshift_mcp_server.py
```

The server will start and wait for MCP client connections.

## **🧪 Testing the Server**

### **Basic Functionality Tests**

#### **Test 1: Cluster Connection**
```bash
# Test cluster info
python -c "
import asyncio
import sys
sys.path.append('.')
from openshift_mcp_server import get_cluster_info
print(asyncio.run(get_cluster_info()))
"
```

Expected output:
```json
{
  "platform": "OpenShift",
  "openshift_available": true,
  "ocm_available": false,
  "transport": "stdio",
  "capabilities": ["OpenShift Projects & Namespaces", "OpenShift Routes & Services", ...]
}
```

#### **Test 2: Projects**
```bash
# Test OpenShift projects
python -c "
import asyncio
import sys
sys.path.append('.')
from openshift_mcp_server import get_projects
print(asyncio.run(get_projects()))
"
```

#### **Test 3: Operators**
```bash
# Test operator detection
python -c "
import asyncio
import sys
sys.path.append('.')
from openshift_mcp_server import get_all_operators
print(asyncio.run(get_all_operators('all')))
"
```

#### **Test 4: Log Search**
```bash
# Test log search functionality
python -c "
import asyncio
import sys
sys.path.append('.')
from openshift_mcp_server import search_all_logs
print(asyncio.run(search_all_logs('info', 'default', 'pod', 10)))
"
```

### **Advanced Testing**

#### **Test 5: NVIDIA GPU Support**
```bash
# Test NVIDIA operators
python -c "
import asyncio
import sys
sys.path.append('.')
from openshift_mcp_server import get_nvidia_operators
print(asyncio.run(get_nvidia_operators('all')))
"
```

#### **Test 6: BlueField DPU Support**
```bash
# Test BlueField DPU nodes
python -c "
import asyncio
import sys
sys.path.append('.')
from openshift_mcp_server import get_bluefield_dpu_nodes
print(asyncio.run(get_bluefield_dpu_nodes()))
"
```

#### **Test 7: OpenShift Resources**
```bash
# Test OpenShift-specific resources
python -c "
import asyncio
import sys
sys.path.append('.')
from openshift_mcp_server import get_openshift_resources
print(asyncio.run(get_openshift_resources('routes', 'all')))
"
```

### **Using MCP Inspector for Interactive Testing**

#### **1. Install MCP Inspector**
```bash
# Install Node.js if not already installed
curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
sudo dnf install nodejs npm

# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector
```

#### **2. Test with Inspector**
```bash
# Start inspector with our server
npx @modelcontextprotocol/inspector python openshift_mcp_server.py
```

This opens a web interface at `http://localhost:5173` where you can:
- Browse available tools
- Test individual functions
- View tool descriptions and parameters
- Execute tools interactively

### **HTTP Mode Testing**

#### **1. Run as HTTP Server**
```bash
# Run as HTTP server
export MCP_TRANSPORT=sse
python openshift_mcp_server.py
```

Server will be available at `http://localhost:8004`

#### **2. Test HTTP API**
```bash
# Test basic functionality
curl -X POST http://localhost:8004/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "get_cluster_info"}'

# Test OpenShift projects
curl -X POST http://localhost:8004/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "get_projects"}'

# Test operators
curl -X POST http://localhost:8004/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "get_all_operators", "params": {"project": "all"}}'
```

## **📋 Validation Checklist**

After running the server, validate it works by checking:

- [ ] **Cluster connection**: `get_cluster_info()` returns cluster details
- [ ] **Projects**: `get_projects()` lists OpenShift projects
- [ ] **Operators**: `get_all_operators("all")` finds OLM operators
- [ ] **Resources**: `get_openshift_resources("routes", "all")` works
- [ ] **Logs**: `search_all_logs("info", "default", "pod", 10)` returns logs
- [ ] **NVIDIA**: `get_nvidia_operators("all")` detects GPU operators (if available)
- [ ] **BlueField**: `get_bluefield_dpu_nodes()` detects DPU nodes (if available)

## **🔧 Troubleshooting**

### **Common Issues**

#### **1. "OpenShift API not available"**
```bash
# Check cluster connection
oc whoami
oc cluster-info

# Check kubeconfig
echo $KUBECONFIG_PATH
ls -la ~/.kube/config
```

#### **2. Permission errors**
```bash
# Check permissions
oc auth can-i get pods --all-namespaces
oc auth can-i get subscriptions --all-namespaces
oc auth can-i get routes --all-namespaces

# If missing permissions, contact your cluster admin
```

#### **3. Import errors**
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt

# Check virtual environment
which python
```

#### **4. Network connectivity**
```bash
# Check cluster API access
curl -k https://$(oc whoami --show-server)/version

# Check DNS resolution
nslookup $(oc whoami --show-server | cut -d'/' -f3)
```

### **Debug Mode**
```bash
# Enable debug output
export DEBUG=1
python openshift_mcp_server.py
```

## **🚢 Container Testing**

### **1. Build and Test Container**
```bash
# Build container
podman build -t openshift-mcp:latest .

# Test container
podman run -i --rm \
  -v ~/.kube:/root/.kube:ro \
  -e KUBECONFIG_PATH=/root/.kube/config \
  -e MCP_TRANSPORT=stdio \
  openshift-mcp:latest
```

### **2. HTTP Container Testing**
```bash
# Run as HTTP server
podman run -d --rm \
  -v ~/.kube:/root/.kube:ro \
  -e KUBECONFIG_PATH=/root/.kube/config \
  -e MCP_TRANSPORT=sse \
  -p 8004:8004 \
  --name openshift-mcp \
  openshift-mcp:latest

# Test container
curl -X POST http://localhost:8004/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "get_cluster_info"}'

# Clean up
podman stop openshift-mcp
```

## **🔍 Alternative Cluster Options**

If you don't have access to an existing OpenShift cluster, here are alternatives:

### **Local Development Options**

#### **Option A: OpenShift Local (CRC)**
```bash
# Download and install CRC
curl -L https://developers.redhat.com/content-gateway/file/pub/openshift-v4/clients/crc/latest/crc-linux-amd64.tar.xz | tar -xJ
sudo mv crc-linux-*/crc /usr/local/bin/

# Set up and start
crc setup
crc start

# Get credentials and login
crc console --credentials
oc login -u kubeadmin -p <password> https://api.crc.testing:6443
```

#### **Option B: MicroShift (Lightweight)**
```bash
# Install MicroShift (RHEL/Fedora)
sudo dnf install microshift

# Start service
sudo systemctl enable microshift --now

# Setup kubeconfig
sudo cp /var/lib/microshift/resources/kubeadmin/kubeconfig ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
```

#### **Option C: Mock Mode for Development**
```bash
# For testing without a real cluster
export MOCK_MODE=true
python openshift_mcp_server.py
```

### **Cloud Options**
- **OpenShift Dedicated**: https://cloud.redhat.com/
- **ROSA (AWS)**: Red Hat OpenShift Service on AWS
- **ARO (Azure)**: Azure Red Hat OpenShift
- **OpenShift on GCP**: Google Cloud OpenShift

## **📈 Performance Tips**

- **Local testing**: Use CRC or MicroShift for development
- **Large clusters**: Start with smaller line counts in log searches
- **Production**: Deploy to OpenShift cluster for better performance
- **Caching**: Results are fetched fresh each time (no caching)

## **🔗 Next Steps**

1. **Choose your cluster option** (existing cluster recommended)
2. **Run the validation checklist** to ensure everything works
3. **Test with MCP Inspector** for interactive exploration
4. **Integrate with your MCP client** (Claude Desktop, etc.)
5. **Explore advanced features** (NVIDIA, BlueField DPU, OCM)

## **🎯 Common Use Cases**

After getting started, try these common scenarios:

```bash
# Troubleshoot operator issues
get_all_operators("all")
get_operator_pods("gpu-operator", "nvidia-gpu-operator")
search_all_logs("error", "nvidia-gpu-operator", "all", 100)

# Monitor cluster health
get_cluster_info()
search_all_logs("failed", "all", "event", 50)

# Check GPU/DPU resources
get_nvidia_operators("all")
get_bluefield_dpu_nodes()
get_gpu_workloads("all")

# Explore OpenShift resources
get_openshift_resources("routes", "all")
get_openshift_resources("imagestreams", "openshift")
```

For production deployment, see the OpenShift template in `openshift/template.yaml`.