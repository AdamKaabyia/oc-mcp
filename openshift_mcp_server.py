import os
import json
from typing import Any, Dict, List, Optional
import httpx
import yaml
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient
from openshift.dynamic.exceptions import ResourceNotFoundError

# Initialize the OpenShift MCP server
mcp = FastMCP(
    name="OpenShift Operator & Log Management Server",
    host="0.0.0.0",
    port=8004
)

# Configuration
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
KUBECONFIG_PATH = os.environ.get("KUBECONFIG_PATH", os.path.expanduser("~/.kube/config"))
OCM_API_BASE = os.environ.get("OCM_API_BASE", "https://api.openshift.com")


class OpenShiftManager:
    """Comprehensive OpenShift cluster management"""

    def __init__(self):
        self.k8s_client = None
        self.dynamic_client = None
        self.v1 = None
        self.apps_v1 = None
        self.extensions_v1 = None
        self.rbac_v1 = None
        self.apiextensions_v1 = None
        self.route_v1 = None
        self.project_v1 = None
        self.operator_v1 = None
        self.operator_v1alpha1 = None
        self.config_v1 = None
        self.security_v1 = None
        self.image_v1 = None
        self._load_config()

    def _load_config(self):
        """Load OpenShift configuration"""
        try:
            if os.path.exists(KUBECONFIG_PATH):
                config.load_kube_config(config_file=KUBECONFIG_PATH)
            else:
                config.load_incluster_config()

            # Standard Kubernetes clients
            self.k8s_client = client.ApiClient()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.extensions_v1 = client.ExtensionsV1beta1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            self.apiextensions_v1 = client.ApiextensionsV1Api()

            # OpenShift dynamic client for custom resources
            self.dynamic_client = DynamicClient(self.k8s_client)

            # OpenShift-specific resources
            self._setup_openshift_resources()

        except Exception as e:
            print(f"Could not load OpenShift config: {e}")

    def _setup_openshift_resources(self):
        """Setup OpenShift-specific resource clients"""
        try:
            if self.dynamic_client and self.dynamic_client.resources:
                # Routes
                self.route_v1 = self.dynamic_client.resources.get(
                    api_version='route.openshift.io/v1',
                    kind='Route'
                )

                # Projects
                self.project_v1 = self.dynamic_client.resources.get(
                    api_version='project.openshift.io/v1',
                    kind='Project'
                )

                # Operators
                self.operator_v1 = self.dynamic_client.resources.get(
                    api_version='operators.coreos.com/v1',
                    kind='OperatorGroup'
                )

                self.operator_v1alpha1 = self.dynamic_client.resources.get(
                    api_version='operators.coreos.com/v1alpha1',
                    kind='Subscription'
                )

            # OpenShift Config
            if self.dynamic_client and self.dynamic_client.resources:
                self.config_v1 = self.dynamic_client.resources.get(
                    api_version='config.openshift.io/v1',
                    kind='ClusterVersion'
                )

                # Security Context Constraints
                self.security_v1 = self.dynamic_client.resources.get(
                    api_version='security.openshift.io/v1',
                    kind='SecurityContextConstraints'
                )

                # Image streams
                self.image_v1 = self.dynamic_client.resources.get(
                    api_version='image.openshift.io/v1',
                    kind='ImageStream'
                )

        except Exception as e:
            print(f"Could not setup OpenShift resources: {e}")

    def is_available(self) -> bool:
        """Check if OpenShift API is available"""
        return self.v1 is not None and self.dynamic_client is not None


class OCMManager:
    """Manages OCM API interactions for managed OpenShift clusters"""

    def __init__(self):
        self.client_id = os.environ.get("OCM_CLIENT_ID")
        self.offline_token = os.environ.get("OCM_OFFLINE_TOKEN")
        self.access_token_url = os.environ.get("ACCESS_TOKEN_URL")

    def is_available(self) -> bool:
        """Check if OCM credentials are available"""
        return all([self.client_id, self.offline_token, self.access_token_url])

    async def make_request(self, url: str) -> Dict[str, Any] | None:
        """Make authenticated request to OCM API"""
        if not self.is_available():
            return None

        offline_token = (
            self.offline_token
            if MCP_TRANSPORT == "stdio"
            else mcp.get_context().request_context.request.headers.get("X-OCM-Offline-Token")
        )

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": offline_token,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.access_token_url, data=data, timeout=30.0)
                response.raise_for_status()
                token = response.json().get("access_token")

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                }

                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"OCM API request failed: {e}")
                return None


# Initialize managers
openshift_manager = OpenShiftManager()
ocm_manager = OCMManager()


@mcp.tool()
async def get_cluster_info() -> str:
    """Get comprehensive OpenShift cluster information and capabilities"""
    info = {
        "platform": "OpenShift",
        "openshift_available": openshift_manager.is_available(),
        "ocm_available": ocm_manager.is_available(),
        "transport": MCP_TRANSPORT,
        "capabilities": []
    }

    if openshift_manager.is_available():
        info["capabilities"].extend([
            "OpenShift Projects & Namespaces",
            "OpenShift Routes & Services",
            "Operator Lifecycle Manager (OLM)",
            "All OpenShift Operators (OLM, Helm, Custom)",
            "Comprehensive Pod & Operator Logs",
            "OpenShift Events & Monitoring",
            "Custom Resource Definitions (CRDs)",
            "OpenShift Security Context Constraints",
            "OpenShift Image Streams & Registry",
            "OpenShift Configuration Management",
            "RBAC & Service Accounts",
            "OpenShift Build & Deploy Configs"
        ])

    if ocm_manager.is_available():
        info["capabilities"].extend([
            "OCM Managed Clusters",
            "OCM Service Logs",
            "OCM Cluster Lifecycle Management"
        ])

    # Try to get cluster version and additional info
    try:
        cluster_version = openshift_manager.config_v1.get()
        if cluster_version.items:
            cv = cluster_version.items[0]
            info["openshift_version"] = cv.status.desired.version
            info["cluster_id"] = cv.spec.clusterID
            info["update_channel"] = cv.spec.channel
    except:
        pass

    return json.dumps(info, indent=2)


@mcp.tool()
async def get_projects() -> str:
    """List all OpenShift projects with detailed information"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    try:
        projects = openshift_manager.project_v1.get()
        result = []
        for project in projects.items:
            # Get resource quotas and limits
            try:
                quotas = openshift_manager.v1.list_namespaced_resource_quota(project.metadata.name)
                quota_info = []
                for quota in quotas.items:
                    quota_info.append({
                        "name": quota.metadata.name,
                        "hard": quota.status.hard,
                        "used": quota.status.used
                    })
            except:
                quota_info = []

            result.append({
                "name": project.metadata.name,
                "display_name": project.metadata.get("annotations", {}).get("openshift.io/display-name", ""),
                "description": project.metadata.get("annotations", {}).get("openshift.io/description", ""),
                "status": project.status.phase,
                "created": project.metadata.creationTimestamp,
                "quotas": quota_info
            })
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Error listing projects: {e}"


@mcp.tool()
async def get_all_operators(project: str = "all") -> str:
    """List ALL OpenShift operators including OLM, Helm, and custom operators"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    all_operators = []

    # 1. Get OLM Operators (Subscriptions)
    try:
        subscriptions_resource = openshift_manager.dynamic_client.resources.get(
            api_version='operators.coreos.com/v1alpha1',
            kind='Subscription'
        )

        if project == "all":
            subscriptions = subscriptions_resource.get()
        else:
            subscriptions = subscriptions_resource.get(namespace=project)

        for sub in subscriptions.items:
            csv_name = sub.status.get("currentCSV") if sub.status else None
            csv_info = None

            if csv_name:
                try:
                    csv_resource = openshift_manager.dynamic_client.resources.get(
                        api_version='operators.coreos.com/v1alpha1',
                        kind='ClusterServiceVersion'
                    )
                    csv = csv_resource.get(name=csv_name, namespace=sub.metadata.namespace)
                    csv_info = {
                        "display_name": csv.spec.displayName,
                        "version": csv.spec.version,
                        "description": csv.spec.description,
                        "phase": csv.status.phase,
                        "owned_resources": [{"kind": res.kind, "name": res.name} for res in csv.spec.customresourcedefinitions.owned] if csv.spec.customresourcedefinitions else []
                    }
                except:
                    pass

            all_operators.append({
                "type": "OLM",
                "name": sub.metadata.name,
                "namespace": sub.metadata.namespace,
                "package": sub.spec.name,
                "channel": sub.spec.channel,
                "source": sub.spec.source,
                "source_namespace": sub.spec.sourceNamespace,
                "installed_csv": csv_name,
                "csv_info": csv_info,
                "created": sub.metadata.creationTimestamp
            })
    except Exception as e:
        all_operators.append({"type": "error", "message": f"Error getting OLM operators: {e}"})

    # 2. Get Helm Releases
    try:
        helm_resource = openshift_manager.dynamic_client.resources.get(
            api_version='helm.openshift.io/v1beta1',
            kind='HelmChartRepository'
        )
        helm_repos = helm_resource.get()
        for repo in helm_repos.items:
            all_operators.append({
                "type": "Helm",
                "name": repo.metadata.name,
                "namespace": repo.metadata.namespace,
                "url": repo.spec.connectionConfig.url,
                "created": repo.metadata.creationTimestamp
            })
    except:
        pass

    # 3. Get Custom Operators (Deployments that look like operators)
    try:
        if project == "all":
            deployments = openshift_manager.apps_v1.list_deployment_for_all_namespaces()
        else:
            deployments = openshift_manager.apps_v1.list_namespaced_deployment(project)

        for deploy in deployments.items:
            # Check if this looks like an operator
            if ("operator" in deploy.metadata.name.lower() or
                "controller" in deploy.metadata.name.lower() or
                deploy.metadata.labels.get("app.kubernetes.io/component") == "operator"):

                all_operators.append({
                    "type": "Custom",
                    "name": deploy.metadata.name,
                    "namespace": deploy.metadata.namespace,
                    "replicas": deploy.spec.replicas,
                    "ready_replicas": deploy.status.ready_replicas,
                    "image": deploy.spec.template.spec.containers[0].image if deploy.spec.template.spec.containers else None,
                    "created": deploy.metadata.creation_timestamp
                })
    except Exception as e:
        all_operators.append({"type": "error", "message": f"Error getting custom operators: {e}"})

    return json.dumps(all_operators, indent=2, default=str)


@mcp.tool()
async def get_comprehensive_logs(resource_type: str, resource_name: str, project: str, log_type: str = "all", lines: int = 100) -> str:
    """Get comprehensive logs from any OpenShift resource (pods, operators, services, etc.)"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    all_logs = []

    # Pod logs
    if log_type in ["all", "pod"]:
        try:
            if resource_type == "pod":
                logs = openshift_manager.v1.read_namespaced_pod_log(
                    name=resource_name,
                    namespace=project,
                    tail_lines=lines
                )
                all_logs.append(f"=== Pod Logs: {resource_name} ===\n{logs}\n")
            elif resource_type == "operator":
                # Get all pods for this operator
                pods_info = await get_operator_pods(resource_name, project)
                pods = json.loads(pods_info)
                for pod in pods:
                    try:
                        logs = openshift_manager.v1.read_namespaced_pod_log(
                            name=pod["name"],
                            namespace=pod["namespace"],
                            tail_lines=lines
                        )
                        all_logs.append(f"=== Operator Pod: {pod['name']} ===\n{logs}\n")
                    except Exception as e:
                        all_logs.append(f"=== Operator Pod: {pod['name']} ===\nError: {e}\n")
        except Exception as e:
            all_logs.append(f"Error getting pod logs: {e}")

    # Events
    if log_type in ["all", "events"]:
        try:
            events = openshift_manager.v1.list_namespaced_event(project)
            event_logs = []
            for event in events.items:
                if resource_name.lower() in event.involved_object.name.lower():
                    event_logs.append(f"[{event.last_timestamp}] {event.type}: {event.reason} - {event.message}")

            if event_logs:
                all_logs.append(f"=== Related Events ===\n" + "\n".join(event_logs) + "\n")
        except Exception as e:
            all_logs.append(f"Error getting events: {e}")

    # Build logs (for OpenShift builds)
    if log_type in ["all", "build"]:
        try:
            build_resource = openshift_manager.dynamic_client.resources.get(
                api_version='build.openshift.io/v1',
                kind='Build'
            )
            builds = build_resource.get(namespace=project)
            for build in builds.items:
                if resource_name.lower() in build.metadata.name.lower():
                    build_logs = openshift_manager.dynamic_client.get(
                        api_version='build.openshift.io/v1',
                        kind='BuildLog',
                        name=build.metadata.name,
                        namespace=project
                    )
                    all_logs.append(f"=== Build Logs: {build.metadata.name} ===\n{build_logs}\n")
        except:
            pass

    return "\n".join(all_logs) if all_logs else f"No logs found for {resource_type}/{resource_name} in project {project}"


@mcp.tool()
async def get_operator_pods(operator_name: str, project: str) -> str:
    """Get all pods associated with an operator"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    try:
        # Method 1: Try to find CSV for the operator
        csv_resource = openshift_manager.dynamic_client.resources.get(
            api_version='operators.coreos.com/v1alpha1',
            kind='ClusterServiceVersion'
        )
        csvs = csv_resource.get(namespace=project)

        target_csv = None
        for csv in csvs.items:
            if operator_name in csv.metadata.name:
                target_csv = csv
                break

        operator_pods = []

        if target_csv:
            # Get deployments managed by this CSV
            deployments = openshift_manager.apps_v1.list_namespaced_deployment(project)
            operator_deployments = []

            for deploy in deployments.items:
                if deploy.metadata.owner_references:
                    for owner in deploy.metadata.owner_references:
                        if owner.kind == "ClusterServiceVersion" and owner.name == target_csv.metadata.name:
                            operator_deployments.append(deploy)

            # Get pods for these deployments
            pods = openshift_manager.v1.list_namespaced_pod(project)
            for pod in pods.items:
                if pod.metadata.owner_references:
                    for owner in pod.metadata.owner_references:
                        if owner.kind == "ReplicaSet":
                            for deploy in operator_deployments:
                                rs_name = f"{deploy.metadata.name}-"
                                if owner.name.startswith(rs_name):
                                    operator_pods.append({
                                        "name": pod.metadata.name,
                                        "namespace": pod.metadata.namespace,
                                        "status": pod.status.phase,
                                        "ready": sum(1 for c in pod.status.container_statuses if c.ready) if pod.status.container_statuses else 0,
                                        "containers": len(pod.status.container_statuses) if pod.status.container_statuses else 0,
                                        "created": pod.metadata.creation_timestamp,
                                        "node": pod.spec.node_name
                                    })

        # Method 2: If no CSV found, look for pods with operator name
        if not operator_pods:
            pods = openshift_manager.v1.list_namespaced_pod(project)
            for pod in pods.items:
                if operator_name.lower() in pod.metadata.name.lower():
                    operator_pods.append({
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": pod.status.phase,
                        "ready": sum(1 for c in pod.status.container_statuses if c.ready) if pod.status.container_statuses else 0,
                        "containers": len(pod.status.container_statuses) if pod.status.container_statuses else 0,
                        "created": pod.metadata.creation_timestamp,
                        "node": pod.spec.node_name
                    })

        return json.dumps(operator_pods, indent=2, default=str)
    except Exception as e:
        return f"Error getting operator pods: {e}"


@mcp.tool()
async def search_all_logs(query: str, project: str = "all", resource_types: str = "all", lines: int = 50) -> str:
    """Search across ALL OpenShift logs, events, and resources"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    results = []

    # Search pod logs
    if resource_types in ["all", "pod"]:
        try:
            if project == "all":
                pods = openshift_manager.v1.list_pod_for_all_namespaces()
            else:
                pods = openshift_manager.v1.list_namespaced_pod(project)

            for pod in pods.items[:20]:  # Limit to avoid overwhelming results
                try:
                    logs = openshift_manager.v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=pod.metadata.namespace,
                        tail_lines=lines
                    )
                    if query.lower() in logs.lower():
                        results.append({
                            "type": "pod_log",
                            "source": f"{pod.metadata.namespace}/{pod.metadata.name}",
                            "matches": [line for line in logs.split('\n') if query.lower() in line.lower()][:5]
                        })
                except:
                    continue
        except Exception as e:
            results.append({"type": "error", "message": f"Pod log search error: {e}"})

    # Search events
    if resource_types in ["all", "event"]:
        try:
            if project == "all":
                events = openshift_manager.v1.list_event_for_all_namespaces(limit=200)
            else:
                events = openshift_manager.v1.list_namespaced_event(project, limit=200)

            for event in events.items:
                if query.lower() in event.message.lower():
                    results.append({
                        "type": "event",
                        "source": f"{event.namespace}/{event.involved_object.name}",
                        "message": event.message,
                        "reason": event.reason,
                        "event_type": event.type,
                        "timestamp": event.last_timestamp
                    })
        except Exception as e:
            results.append({"type": "error", "message": f"Event search error: {e}"})

    # Search build logs
    if resource_types in ["all", "build"]:
        try:
            build_resource = openshift_manager.dynamic_client.resources.get(
                api_version='build.openshift.io/v1',
                kind='Build'
            )

            if project == "all":
                builds = build_resource.get()
            else:
                builds = build_resource.get(namespace=project)

            for build in builds.items[:10]:
                try:
                    build_logs = openshift_manager.dynamic_client.get(
                        api_version='build.openshift.io/v1',
                        kind='BuildLog',
                        name=build.metadata.name,
                        namespace=build.metadata.namespace
                    )
                    if query.lower() in str(build_logs).lower():
                        results.append({
                            "type": "build_log",
                            "source": f"{build.metadata.namespace}/{build.metadata.name}",
                            "matches": [line for line in str(build_logs).split('\n') if query.lower() in line.lower()][:3]
                        })
                except:
                    continue
        except:
            pass

    return json.dumps(results, indent=2, default=str)


@mcp.tool()
async def get_openshift_resources(resource_type: str, project: str = "all") -> str:
    """Get comprehensive OpenShift resources (routes, services, configmaps, secrets, etc.)"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    try:
        result = []

        if resource_type == "routes":
            if project == "all":
                routes = openshift_manager.route_v1.get()
            else:
                routes = openshift_manager.route_v1.get(namespace=project)

            for route in routes.items:
                result.append({
                    "name": route.metadata.name,
                    "namespace": route.metadata.namespace,
                    "host": route.spec.host,
                    "path": route.spec.get("path", "/"),
                    "target_service": route.spec.to.name,
                    "port": route.spec.port.targetPort if route.spec.port else None,
                    "tls": "enabled" if route.spec.get("tls") else "disabled",
                    "created": route.metadata.creationTimestamp
                })

        elif resource_type == "services":
            if project == "all":
                services = openshift_manager.v1.list_service_for_all_namespaces()
            else:
                services = openshift_manager.v1.list_namespaced_service(project)

            for svc in services.items:
                result.append({
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "ports": [{"port": p.port, "target_port": p.target_port, "protocol": p.protocol} for p in svc.spec.ports],
                    "selector": svc.spec.selector,
                    "created": svc.metadata.creation_timestamp
                })

        elif resource_type == "configmaps":
            if project == "all":
                cms = openshift_manager.v1.list_config_map_for_all_namespaces()
            else:
                cms = openshift_manager.v1.list_namespaced_config_map(project)

            for cm in cms.items:
                result.append({
                    "name": cm.metadata.name,
                    "namespace": cm.metadata.namespace,
                    "data_keys": list(cm.data.keys()) if cm.data else [],
                    "created": cm.metadata.creation_timestamp
                })

        elif resource_type == "secrets":
            if project == "all":
                secrets = openshift_manager.v1.list_secret_for_all_namespaces()
            else:
                secrets = openshift_manager.v1.list_namespaced_secret(project)

            for secret in secrets.items:
                result.append({
                    "name": secret.metadata.name,
                    "namespace": secret.metadata.namespace,
                    "type": secret.type,
                    "data_keys": list(secret.data.keys()) if secret.data else [],
                    "created": secret.metadata.creation_timestamp
                })

        elif resource_type == "imagestreams":
            try:
                if project == "all":
                    imagestreams = openshift_manager.image_v1.get()
                else:
                    imagestreams = openshift_manager.image_v1.get(namespace=project)

                for ist in imagestreams.items:
                    result.append({
                        "name": ist.metadata.name,
                        "namespace": ist.metadata.namespace,
                        "docker_image_repository": ist.status.dockerImageRepository,
                        "tags": [tag.name for tag in ist.status.tags] if ist.status.tags else [],
                        "created": ist.metadata.creationTimestamp
                    })
            except:
                pass

        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Error getting {resource_type}: {e}"


# OCM integration tools
@mcp.tool()
async def ocm_get_clusters() -> str:
    """Get OCM managed OpenShift clusters"""
    if not ocm_manager.is_available():
        return "OCM API not available. Set OCM_CLIENT_ID, OCM_OFFLINE_TOKEN, and ACCESS_TOKEN_URL."

    url = f"{OCM_API_BASE}/api/clusters_mgmt/v1/clusters"
    data = await ocm_manager.make_request(url)

    if not data or "items" not in data:
        return "No clusters found or invalid response."

    clusters = []
    for cluster in data["items"]:
        clusters.append({
            "name": cluster.get("name", "N/A"),
            "id": cluster.get("id", "N/A"),
            "api_url": cluster.get("api", {}).get("url", "N/A"),
            "console_url": cluster.get("console", {}).get("url", "N/A"),
            "state": cluster.get("state", "N/A"),
            "openshift_version": cluster.get("openshift_version", "N/A"),
            "product": cluster.get("product", {}).get("id", "N/A"),
            "cloud_provider": cluster.get("cloud_provider", {}).get("id", "N/A"),
            "region": cluster.get("region", {}).get("id", "N/A")
        })

    return json.dumps(clusters, indent=2)


@mcp.tool()
async def ocm_get_cluster_logs(cluster_id: str) -> str:
    """Get OCM service logs for OpenShift cluster"""
    if not ocm_manager.is_available():
        return "OCM API not available"

    url = f"{OCM_API_BASE}/api/service_logs/v1/clusters/cluster_logs?cluster_id={cluster_id}"
    data = await ocm_manager.make_request(url)

    if not data or "items" not in data:
        return "No logs found or invalid response."

    logs = []
    for log in data["items"]:
        logs.append({
            "service_name": log.get("service_name", "N/A"),
            "id": log.get("id", "N/A"),
            "description": log.get("description", ""),
            "timestamp": log.get("timestamp", "N/A"),
            "severity": log.get("severity", "N/A"),
            "summary": log.get("summary", "")
        })

    return json.dumps(logs, indent=2)


@mcp.tool()
async def get_nvidia_operators(project: str = "all") -> str:
    """Get all NVIDIA-related operators (GPU Operator, Network Operator, etc.)"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    try:
        # Get all operators first
        all_operators = await get_all_operators(project)
        operators_data = json.loads(all_operators)

        # Filter for NVIDIA operators
        nvidia_operators = []
        for operator in operators_data:
            if isinstance(operator, dict):
                name = operator.get("name", "").lower()
                package = operator.get("package", "").lower()
                display_name = ""

                if operator.get("csv_info"):
                    display_name = operator.get("csv_info", {}).get("display_name", "").lower()

                # Check if this is an NVIDIA operator
                if any(keyword in name or keyword in package or keyword in display_name
                       for keyword in ["nvidia", "gpu", "cuda", "mellanox", "connectx"]):
                    nvidia_operators.append(operator)

        return json.dumps(nvidia_operators, indent=2, default=str)
    except Exception as e:
        return f"Error getting NVIDIA operators: {e}"


@mcp.tool()
async def get_gpu_nodes() -> str:
    """Get all GPU-enabled nodes in the cluster"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    try:
        nodes = openshift_manager.v1.list_node()
        gpu_nodes = []

        for node in nodes.items:
            node_info = {
                "name": node.metadata.name,
                "labels": node.metadata.labels,
                "taints": [{"key": t.key, "value": t.value, "effect": t.effect} for t in node.spec.taints] if node.spec.taints else [],
                "gpu_resources": {},
                "nvidia_labels": {},
                "conditions": []
            }

            # Check for GPU resources
            if node.status.allocatable:
                for resource, quantity in node.status.allocatable.items():
                    if "nvidia.com" in resource or "gpu" in resource.lower():
                        node_info["gpu_resources"][resource] = quantity

            # Check for NVIDIA-specific labels
            if node.metadata.labels:
                for label, value in node.metadata.labels.items():
                    if "nvidia" in label.lower() or "gpu" in label.lower():
                        node_info["nvidia_labels"][label] = value

            # Check node conditions
            if node.status.conditions:
                for condition in node.status.conditions:
                    if condition.type in ["Ready", "GPUReady", "NvidiaGPU"]:
                        node_info["conditions"].append({
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message
                        })

            # Only include nodes with GPU resources or NVIDIA labels
            if node_info["gpu_resources"] or node_info["nvidia_labels"]:
                gpu_nodes.append(node_info)

        return json.dumps(gpu_nodes, indent=2, default=str)
    except Exception as e:
        return f"Error getting GPU nodes: {e}"


@mcp.tool()
async def get_gpu_operator_health() -> str:
    """Get comprehensive health status of NVIDIA GPU Operator"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    health_report = {
        "operator_status": {},
        "pods_status": [],
        "recent_errors": [],
        "gpu_nodes": [],
        "driver_status": {},
        "device_plugin_status": {},
        "summary": {}
    }

    try:
        # 1. Check operator installation
        nvidia_operators = await get_nvidia_operators("all")
        operators_data = json.loads(nvidia_operators)

        for operator in operators_data:
            if "gpu-operator" in operator.get("name", ""):
                health_report["operator_status"] = operator
                break

        # 2. Check operator pods
        if health_report["operator_status"]:
            namespace = health_report["operator_status"].get("namespace", "nvidia-gpu-operator")
            pods_info = await get_operator_pods("gpu-operator", namespace)
            health_report["pods_status"] = json.loads(pods_info)

        # 3. Check for recent errors
        error_logs = await search_all_logs("ERROR", "nvidia-gpu-operator", "all", 50)
        health_report["recent_errors"] = json.loads(error_logs)

        # 4. Check GPU nodes
        gpu_nodes = await get_gpu_nodes()
        health_report["gpu_nodes"] = json.loads(gpu_nodes)

        # 5. Check driver status
        driver_logs = await search_all_logs("nvidia-driver", "nvidia-gpu-operator", "pod", 20)
        health_report["driver_status"] = json.loads(driver_logs)

        # 6. Check device plugin
        device_logs = await search_all_logs("device-plugin", "nvidia-gpu-operator", "pod", 20)
        health_report["device_plugin_status"] = json.loads(device_logs)

        # 7. Generate summary
        health_report["summary"] = {
            "operator_installed": bool(health_report["operator_status"]),
            "operator_healthy": health_report["operator_status"].get("csv_info", {}).get("phase") == "Succeeded",
            "total_pods": len(health_report["pods_status"]),
            "running_pods": len([p for p in health_report["pods_status"] if p.get("status") == "Running"]),
            "gpu_nodes_count": len(health_report["gpu_nodes"]),
            "recent_errors_count": len(health_report["recent_errors"]),
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(health_report, indent=2, default=str)
    except Exception as e:
        return f"Error getting GPU operator health: {e}"


@mcp.tool()
async def search_gpu_logs(query: str, log_type: str = "all", lines: int = 100) -> str:
    """Search specifically in GPU/NVIDIA related logs and events"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    gpu_results = []

    # Search in NVIDIA GPU operator namespace
    try:
        nvidia_logs = await search_all_logs(query, "nvidia-gpu-operator", log_type, lines)
        nvidia_data = json.loads(nvidia_logs)
        for item in nvidia_data:
            item["source_type"] = "nvidia-gpu-operator"
            gpu_results.append(item)
    except:
        pass

    # Search in OpenShift AI namespace (if exists)
    try:
        ai_logs = await search_all_logs(query, "opendatahub", log_type, lines)
        ai_data = json.loads(ai_logs)
        for item in ai_data:
            item["source_type"] = "opendatahub"
            gpu_results.append(item)
    except:
        pass

    # Search across all namespaces for GPU-related content
    try:
        gpu_keywords = ["gpu", "nvidia", "cuda", "dcgm", "mig"]
        for keyword in gpu_keywords:
            if keyword.lower() in query.lower():
                all_logs = await search_all_logs(query, "all", log_type, lines // len(gpu_keywords))
                all_data = json.loads(all_logs)
                for item in all_data:
                    item["source_type"] = "cluster-wide"
                    gpu_results.append(item)
                break
    except:
        pass

    return json.dumps(gpu_results, indent=2, default=str)


@mcp.tool()
async def get_gpu_workloads(project: str = "all") -> str:
    """Get all pods that are requesting GPU resources"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    try:
        if project == "all":
            pods = openshift_manager.v1.list_pod_for_all_namespaces()
        else:
            pods = openshift_manager.v1.list_namespaced_pod(project)

        gpu_workloads = []

        for pod in pods.items:
            pod_info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "node": pod.spec.node_name,
                "gpu_requests": {},
                "gpu_limits": {},
                "created": pod.metadata.creation_timestamp
            }

            # Check each container for GPU resources
            has_gpu = False
            if pod.spec.containers:
                for container in pod.spec.containers:
                    if container.resources:
                        # Check requests
                        if container.resources.requests:
                            for resource, quantity in container.resources.requests.items():
                                if "nvidia.com" in resource or "gpu" in resource.lower():
                                    pod_info["gpu_requests"][resource] = quantity
                                    has_gpu = True

                        # Check limits
                        if container.resources.limits:
                            for resource, quantity in container.resources.limits.items():
                                if "nvidia.com" in resource or "gpu" in resource.lower():
                                    pod_info["gpu_limits"][resource] = quantity
                                    has_gpu = True

            if has_gpu:
                gpu_workloads.append(pod_info)

        return json.dumps(gpu_workloads, indent=2, default=str)
    except Exception as e:
        return f"Error getting GPU workloads: {e}"


@mcp.tool()
async def get_bluefield_dpu_nodes() -> str:
    """Get all BlueField DPU-enabled nodes with detailed DPU information"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    try:
        nodes = openshift_manager.v1.list_node()
        bluefield_nodes = []

        for node in nodes.items:
            node_info = {
                "name": node.metadata.name,
                "labels": node.metadata.labels,
                "annotations": node.metadata.annotations,
                "taints": [{"key": t.key, "value": t.value, "effect": t.effect} for t in node.spec.taints] if node.spec.taints else [],
                "dpu_resources": {},
                "bluefield_labels": {},
                "network_resources": {},
                "conditions": [],
                "dpu_info": {}
            }

            # Check for BlueField DPU resources
            if node.status.allocatable:
                for resource, quantity in node.status.allocatable.items():
                    if ("nvidia.com/dpu" in resource or
                        "nvidia.com/bluefield" in resource or
                        "nvidia.com/sriov" in resource or
                        "mellanox.com" in resource):
                        node_info["dpu_resources"][resource] = quantity

            # Check for BlueField-specific labels
            if node.metadata.labels:
                for label, value in node.metadata.labels.items():
                    if ("bluefield" in label.lower() or
                        "dpu" in label.lower() or
                        "mellanox" in label.lower() or
                        "connectx" in label.lower()):
                        node_info["bluefield_labels"][label] = value

            # Check for network resources and SR-IOV
            if node.status.allocatable:
                for resource, quantity in node.status.allocatable.items():
                    if ("sriov" in resource.lower() or
                        "rdma" in resource.lower() or
                        "net" in resource.lower()):
                        node_info["network_resources"][resource] = quantity

            # Extract DPU info from annotations
            if node.metadata.annotations:
                for annotation, value in node.metadata.annotations.items():
                    if ("dpu" in annotation.lower() or
                        "bluefield" in annotation.lower() or
                        "mellanox" in annotation.lower()):
                        node_info["dpu_info"][annotation] = value

            # Check node conditions
            if node.status.conditions:
                for condition in node.status.conditions:
                    if condition.type in ["Ready", "NetworkUnavailable", "DPUReady"]:
                        node_info["conditions"].append({
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message
                        })

            # Only include nodes with DPU/BlueField resources or labels
            if (node_info["dpu_resources"] or
                node_info["bluefield_labels"] or
                node_info["network_resources"]):
                bluefield_nodes.append(node_info)

        return json.dumps(bluefield_nodes, indent=2, default=str)
    except Exception as e:
        return f"Error getting BlueField DPU nodes: {e}"


@mcp.tool()
async def get_bluefield_dpu_workloads(project: str = "all") -> str:
    """Get all pods that are requesting BlueField DPU resources"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    try:
        if project == "all":
            pods = openshift_manager.v1.list_pod_for_all_namespaces()
        else:
            pods = openshift_manager.v1.list_namespaced_pod(project)

        dpu_workloads = []

        for pod in pods.items:
            pod_info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "node": pod.spec.node_name,
                "dpu_requests": {},
                "dpu_limits": {},
                "sriov_requests": {},
                "sriov_limits": {},
                "rdma_requests": {},
                "rdma_limits": {},
                "created": pod.metadata.creation_timestamp
            }

            # Check each container for DPU resources
            has_dpu = False
            if pod.spec.containers:
                for container in pod.spec.containers:
                    if container.resources:
                        # Check requests
                        if container.resources.requests:
                            for resource, quantity in container.resources.requests.items():
                                if "nvidia.com/dpu" in resource or "nvidia.com/bluefield" in resource:
                                    pod_info["dpu_requests"][resource] = quantity
                                    has_dpu = True
                                elif "sriov" in resource.lower():
                                    pod_info["sriov_requests"][resource] = quantity
                                    has_dpu = True
                                elif "rdma" in resource.lower():
                                    pod_info["rdma_requests"][resource] = quantity
                                    has_dpu = True

                        # Check limits
                        if container.resources.limits:
                            for resource, quantity in container.resources.limits.items():
                                if "nvidia.com/dpu" in resource or "nvidia.com/bluefield" in resource:
                                    pod_info["dpu_limits"][resource] = quantity
                                    has_dpu = True
                                elif "sriov" in resource.lower():
                                    pod_info["sriov_limits"][resource] = quantity
                                    has_dpu = True
                                elif "rdma" in resource.lower():
                                    pod_info["rdma_limits"][resource] = quantity
                                    has_dpu = True

            if has_dpu:
                dpu_workloads.append(pod_info)

        return json.dumps(dpu_workloads, indent=2, default=str)
    except Exception as e:
        return f"Error getting BlueField DPU workloads: {e}"


@mcp.tool()
async def get_bluefield_dpu_health() -> str:
    """Get comprehensive health status of BlueField DPU infrastructure"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    health_report = {
        "network_operator_status": {},
        "dpu_nodes": [],
        "dpu_workloads": [],
        "sriov_operator_status": {},
        "recent_dpu_errors": [],
        "ofed_driver_status": {},
        "rdma_device_status": {},
        "summary": {}
    }

    try:
        # 1. Check NVIDIA Network Operator
        nvidia_operators = await get_nvidia_operators("all")
        operators_data = json.loads(nvidia_operators)

        for operator in operators_data:
            if "network-operator" in operator.get("name", ""):
                health_report["network_operator_status"] = operator
                break

        # 2. Check BlueField DPU nodes
        dpu_nodes = await get_bluefield_dpu_nodes()
        health_report["dpu_nodes"] = json.loads(dpu_nodes)

        # 3. Check DPU workloads
        dpu_workloads = await get_bluefield_dpu_workloads("all")
        health_report["dpu_workloads"] = json.loads(dpu_workloads)

        # 4. Check for recent DPU errors
        dpu_errors = await search_gpu_logs("ERROR", "all", 50)
        health_report["recent_dpu_errors"] = json.loads(dpu_errors)

        # 5. Check OFED driver status
        ofed_logs = await search_gpu_logs("ofed", "all", 20)
        health_report["ofed_driver_status"] = json.loads(ofed_logs)

        # 6. Check RDMA device status
        rdma_logs = await search_gpu_logs("rdma", "all", 20)
        health_report["rdma_device_status"] = json.loads(rdma_logs)

        # 7. Create summary
        health_report["summary"] = {
            "network_operator_installed": bool(health_report["network_operator_status"]),
            "dpu_nodes_count": len(health_report["dpu_nodes"]),
            "dpu_workloads_count": len(health_report["dpu_workloads"]),
            "recent_errors_count": len(health_report["recent_dpu_errors"]),
            "health_status": "healthy" if not health_report["recent_dpu_errors"] else "degraded"
        }

        return json.dumps(health_report, indent=2, default=str)
    except Exception as e:
        return f"Error getting BlueField DPU health: {e}"


@mcp.tool()
async def search_bluefield_dpu_logs(query: str, log_type: str = "all", lines: int = 100) -> str:
    """Search specifically in BlueField DPU related logs and events"""
    if not openshift_manager.is_available():
        return "OpenShift API not available"

    dpu_results = []

    # Search in NVIDIA Network Operator namespace
    try:
        network_logs = await search_all_logs(query, "nvidia-network-operator", log_type, lines)
        network_data = json.loads(network_logs)
        for item in network_data:
            item["source_type"] = "nvidia-network-operator"
            dpu_results.append(item)
    except:
        pass

    # Search in SR-IOV Operator namespace
    try:
        sriov_logs = await search_all_logs(query, "openshift-sriov-network-operator", log_type, lines)
        sriov_data = json.loads(sriov_logs)
        for item in sriov_data:
            item["source_type"] = "openshift-sriov-network-operator"
            dpu_results.append(item)
    except:
        pass

    # Search across all namespaces for DPU-related content
    try:
        dpu_keywords = ["bluefield", "dpu", "mellanox", "connectx", "ofed", "rdma", "sriov"]
        for keyword in dpu_keywords:
            if keyword.lower() in query.lower():
                all_logs = await search_all_logs(query, "all", log_type, lines // len(dpu_keywords))
                all_data = json.loads(all_logs)
                for item in all_data:
                    item["source_type"] = "cluster-wide"
                    dpu_results.append(item)
                break
    except:
        pass

    return json.dumps(dpu_results, indent=2, default=str)


if __name__ == "__main__":
    mcp.run(transport=MCP_TRANSPORT)