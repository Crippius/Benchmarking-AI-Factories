"""ChromaDB monitor for collecting metrics."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from monitoring.base_monitor import BaseMonitor
import requests


class ChromaMonitor(BaseMonitor):
    """Monitor for ChromaDB service."""
    
    def __init__(self, endpoint="http://localhost:8000", **kwargs):
        super().__init__(name="ChromaMonitor", **kwargs)
        # ChromaDB doesn't have a /metrics endpoint like Ollama
        # We'll use the main API endpoint
        self.base_url = endpoint.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/v1"
    
    def collect_service_metrics(self):
        """Collect ChromaDB-specific metrics."""
        metrics = {}
        
        try:
            # Check if service is alive
            response = requests.get(f"{self.base_url}/api/v1/heartbeat", timeout=5)
            metrics["heartbeat_status_code"] = response.status_code
            metrics["service_available"] = response.status_code == 200
            
            if response.status_code == 200:
                # Try to get version info
                try:
                    heartbeat_data = response.json()
                    if isinstance(heartbeat_data, dict):
                        metrics.update({f"heartbeat_{k}": v for k, v in heartbeat_data.items()})
                except:
                    pass
            
            # Measure response time
            import time
            start = time.time()
            requests.get(f"{self.base_url}/api/v1/heartbeat", timeout=5)
            metrics["response_time_ms"] = (time.time() - start) * 1000
            
        except requests.exceptions.Timeout:
            metrics["service_available"] = False
            metrics["error"] = "timeout"
        except requests.exceptions.ConnectionError:
            metrics["service_available"] = False
            metrics["error"] = "connection_error"
        except Exception as e:
            metrics["service_available"] = False
            metrics["error"] = str(e)
        
        return metrics
