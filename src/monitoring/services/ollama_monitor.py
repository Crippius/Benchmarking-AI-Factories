
from monitoring.base_monitor import BaseMonitor
import requests

class OllamaMonitor(BaseMonitor):
    def __init__(self, endpoint="http://localhost:11434/metrics", **kwargs):
        super().__init__(name="OllamaMonitor", **kwargs)
        self.endpoint = endpoint

    def collect_service_metrics(self):
        try:
            response = requests.get(self.endpoint)
            response.raise_for_status()
            metrics_text = response.text

            metrics = {}
            for line in metrics_text.splitlines():
                if line and not line.startswith("#"):
                    key, value = line.split()[:2]
                    metrics[key] = float(value)
            return metrics
        except Exception as e:
            return {"error": str(e)}
