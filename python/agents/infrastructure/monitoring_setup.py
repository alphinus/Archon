"""
Monitoring Setup for Archon

Configures Prometheus metrics, Grafana dashboards, and alerting.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import json
import logging

logger = logging.getLogger(__name__)


class MonitoringSetup:
    """
    Sets up monitoring and alerting for Archon.
    
    Features:
    - Prometheus metrics export
    - Grafana dashboard generation
    - Alert rule configuration
    - Log aggregation setup
    - Uptime monitoring
    
    Example:
        monitor = MonitoringSetup()
        monitor.create_prometheus_config()
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize monitoring setup."""
        self.project_root = project_root or Path.cwd()
        self.monitoring_dir = self.project_root / "monitoring"
        self.monitoring_dir.mkdir(exist_ok=True)
    
    def create_prometheus_config(self) -> Dict[str, Any]:
        """
        Create Prometheus configuration.
        
        Returns:
            Config details
        """
        logger.info("Creating Prometheus configuration")
        
        config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "archon-server",
                    "static_configs": [
                        {"targets": ["archon-server:8000"]}
                    ],
                    "metrics_path": "/metrics"
                },
                {
                    "job_name": "archon-agents",
                    "static_configs": [
                        {"targets": [
                            "agent-testing:8001",
                            "agent-devex:8002",
                            "agent-data:8003"
                        ]}
                    ]
                },
                {
                    "job_name": "postgres",
                    "static_configs": [
                        {"targets": ["postgres:9187"]}
                    ]
                },
                {
                    "job_name": "redis",
                    "static_configs": [
                        {"targets": ["redis:9121"]}
                    ]
                }
            ],
            "alerting": {
                "alertmanagers": [
                    {
                       "static_configs": [
                            {"targets": ["alertmanager:9093"]}
                        ]
                    }
                ]
            }
        }
        
        config_path = self.monitoring_dir / "prometheus.yml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Prometheus config created: {config_path}")
        
        return {
            "status": "success",
            "config_path": str(config_path)
        }
    
    def create_grafana_dashboard(self) -> Dict[str, Any]:
        """
        Create Grafana dashboard for Archon metrics.
        
        Returns:
            Dashboard configuration
        """
        logger.info("Creating Grafana dashboard")
        
        dashboard = {
            "dashboard": {
                "title": "Archon System Overview",
                "tags": ["archon", "overview"],
                "timezone": "browser",
                "panels": [
                    {
                        "title": "Request Rate",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "{{method}} {{endpoint}}"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "title": "Response Time (p95)",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "p95"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "title": "Memory Usage",
                        "targets": [
                            {
                                "expr": "go_memstats_alloc_bytes",
                                "legendFormat": "{{instance}}"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "title": "Active Sessions",
                        "targets": [
                            {
                                "expr": "archon_active_sessions",
                                "legendFormat": "Sessions"
                            }
                        ],
                        "type": "stat"
                    }
                ]
            }
        }
        
        dashboard_path = self.monitoring_dir / "grafana-dashboard.json"
        with open(dashboard_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        logger.info(f"Grafana dashboard created: {dashboard_path}")
        
        return {
            "status": "success",
            "dashboard_path": str(dashboard_path)
        }
    
    def create_alert_rules(self) -> Dict[str, Any]:
        """
        Create Prometheus alert rules.
        
        Returns:
            Alert rules configuration
        """
        logger.info("Creating alert rules")
        
        rules = {
            "groups": [
                {
                    "name": "archon_alerts",
                    "rules": [
                        {
                            "alert": "HighErrorRate",
                            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) > 0.05",
                            "for": "5m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "High error rate detected",
                                "description": "Error rate is {{ $value }} errors/sec"
                            }
                        },
                        {
                            "alert": "HighLatency",
                            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High response time",
                                "description": "p95 latency is {{ $value }}s"
                            }
                        },
                        {
                            "alert": "ServiceDown",
                            "expr": "up == 0",
                            "for": "1m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "Service is down",
                                "description": "{{ $labels.instance }} is unreachable"
                            }
                        },
                        {
                            "alert": "HighMemoryUsage",
                            "expr": "container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High memory usage",
                                "description": "Memory usage is {{ $value | humanizePercentage }}"
                            }
                        }
                    ]
                }
            ]
        }
        
        rules_path = self.monitoring_dir / "alert_rules.yml"
        with open(rules_path, 'w') as f:
            yaml.dump(rules, f, default_flow_style=False)
        
        logger.info(f"Alert rules created: {rules_path}")
        
        return {
            "status": "success",
            "rules_path": str(rules_path),
            "alert_count": len(rules["groups"][0]["rules"])
        }
    
    def create_docker_compose_monitoring(self) -> Dict[str, Any]:
        """
        Create docker-compose configuration for monitoring stack.
        
        Returns:
            Compose configuration
        """
        logger.info("Creating monitoring docker-compose")
        
        compose = {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml",
                        "./monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml",
                        "prometheus_data:/prometheus"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus"
                    ]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "ports": ["3001:3000"],
                    "volumes": [
                        "grafana_data:/var/lib/grafana",
                        "./monitoring/grafana-dashboard.json:/etc/grafana/provisioning/dashboards/archon.json"
                    ],
                    "environment": {
                        "GF_SECURITY_ADMIN_PASSWORD": "admin"
                    }
                },
                "alertmanager": {
                    "image": "prom/alertmanager:latest",
                    "ports": ["9093:9093"],
                    "volumes": [
                        "./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml"
                    ]
                }
            },
            "volumes": {
                "prometheus_data": {},
                "grafana_data": {}
            }
        }
        
        compose_path = self.monitoring_dir / "docker-compose.monitoring.yml"
        with open(compose_path, 'w') as f:
            yaml.dump(compose, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Monitoring compose created: {compose_path}")
        
        return {
            "status": "success",
            "compose_path": str(compose_path),
            "services": list(compose["services"].keys())
        }
