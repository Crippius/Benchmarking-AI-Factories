import psutil
import time
import json
from datetime import datetime
from abc import ABC, abstractmethod
import subprocess

class BaseMonitor(ABC):
    def __init__(self, name, interval=5, duration=60, output_file="/tmp/metrics.json"):
        self.name = name
        self.interval = interval
        self.duration = duration
        self.output_file = output_file
        self.data = []

    def collect_system_metrics(self):
        """Collect generic system metrics."""
        return {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_io": psutil.disk_io_counters()._asdict(),
            "net_io": psutil.net_io_counters()._asdict(),
        }

    def collect_gpu_metrics(self):
        """Collect GPU metrics (if available)."""
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                 "--format=csv,noheader,nounits"]
            ).decode().strip()
            gpu_util, mem_used, mem_total = map(float, output.split(','))
            return {"gpu_util": gpu_util, "gpu_mem_used": mem_used, "gpu_mem_total": mem_total}
        except Exception:
            return {}

    @abstractmethod
    def collect_service_metrics(self):
        """Service-specific metrics (must be implemented in subclass)."""
        pass

    def start(self):
        start_time = time.time()
        while time.time() - start_time < self.duration:
            timestamp = datetime.utcnow().isoformat()
            record = {
                "timestamp": timestamp,
                "system": self.collect_system_metrics(),
                "gpu": self.collect_gpu_metrics(),
                "service": self.collect_service_metrics(),
            }
            self.data.append(record)
            print(f"[{self.name}] Collected metrics at {timestamp}")
            time.sleep(self.interval)
        self.save()

    def save(self):
        with open(self.output_file, "w") as f:
            json.dump(self.data, f, indent=2)
        print(f"[{self.name}] Metrics saved to {self.output_file}")

    # TODO: send to grafana