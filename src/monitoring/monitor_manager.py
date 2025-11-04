"""Monitor manager for running monitoring on services."""

import sys
import time
import threading
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.config_loader import ConfigLoader
from monitoring.services.ollama_monitor import OllamaMonitor
# Lazy import for heavy libraries
# from monitoring.services.chroma_monitor import ChromaMonitor
# from monitoring.services.postgres_monitor import PostgresMonitor


class MonitorManager:
    """Manages monitoring of services."""
    
    def __init__(self, job_tracker=None):
        """Initialize the monitor manager."""
        self.base_path = Path(__file__).parent.parent.parent
        self.job_tracker = job_tracker
        self.active_monitors = {}  # Store running monitor threads
        
        # Monitor type mapping - use lazy loading for heavy imports
        self.monitor_types = {
            "ollama": OllamaMonitor,
            "chroma": "monitoring.services.chroma_monitor.ChromaMonitor",  # Lazy load
            "postgres": "monitoring.services.postgres_monitor.PostgresMonitor",  # Lazy load
        }
    
    def _get_monitor_class(self, service_name):
        """Get monitor class with lazy loading."""
        monitor_ref = self.monitor_types.get(service_name)
        
        if monitor_ref is None:
            return None
        
        # If it's already a class, return it
        if not isinstance(monitor_ref, str):
            return monitor_ref
        
        # Lazy load the class
        try:
            module_path, class_name = monitor_ref.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            monitor_class = getattr(module, class_name)
            # Cache it for next time
            self.monitor_types[service_name] = monitor_class
            return monitor_class
        except Exception as e:
            print(f"Error loading monitor class: {e}")
            return None
    
    def list_monitors(self):
        """List available monitor types."""
        print("Available monitors:")
        for name, monitor_class in self.monitor_types.items():
            status = "✓" if monitor_class else "✗ (not implemented)"
            print(f"  - {name}: {status}")
    
    def start_monitor(self, service_name, job_id, duration=300, interval=5):
        """
        Start monitoring a service.
        
        Args:
            service_name: Name of the service (ollama, chroma, postgres)
            job_id: Service job ID
            duration: How long to monitor (seconds)
            interval: How often to collect metrics (seconds)
        
        Returns:
            str: Monitor ID if successful, None otherwise
        """
        # Get service info from job tracker
        node = None
        if self.job_tracker:
            job_info = self.job_tracker.get_job(job_id)
            if job_info:
                node = job_info.get("node")
        
        if not node:
            print(f"Error: Could not determine node for job {job_id}")
            print("Make sure the service is running and tracked.")
            return None
        
        # Get monitor class
        monitor_class = self.monitor_types.get(service_name)
        if not monitor_class:
            print(f"Error: Monitor for '{service_name}' not implemented yet")
            return None
        
        # Setup output file
        log_dir = self.base_path / "results" / "monitoring"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_file = log_dir / f"{service_name}_monitor_{job_id}_{timestamp}.json"
        
        # Create endpoint URL
        if service_name == "ollama":
            endpoint = f"http://{node}:11434/metrics"
        elif service_name == "chroma":
            endpoint = f"http://{node}:8000"  # Chroma doesn't have /metrics
        elif service_name == "postgres":
            endpoint = f"{node}:5432"  # PostgreSQL connection
        else:
            endpoint = None
        
        # Create monitor instance
        monitor = monitor_class(
            endpoint=endpoint,
            interval=interval,
            duration=duration,
            output_file=str(output_file)
        )
        
        # Generate monitor ID
        monitor_id = f"monitor_{service_name}_{job_id}_{timestamp}"
        
        print(f"Starting {service_name} monitor...")
        print(f"  Node: {node}")
        print(f"  Duration: {duration}s")
        print(f"  Interval: {interval}s")
        print(f"  Output: {output_file}")
        print(f"  Monitor ID: {monitor_id}")
        
        # Start monitor in background thread
        def run_monitor():
            try:
                monitor.start()
                print(f"\n[{monitor_id}] Monitoring completed")
            except Exception as e:
                print(f"\n[{monitor_id}] Error during monitoring: {e}")
        
        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()
        
        # Store monitor info
        self.active_monitors[monitor_id] = {
            "thread": monitor_thread,
            "monitor": monitor,
            "service_name": service_name,
            "job_id": job_id,
            "output_file": str(output_file),
            "start_time": time.time()
        }
        
        print(f"\nMonitor started in background. It will run for {duration} seconds.")
        print(f"Results will be saved to: {output_file}")
        
        return monitor_id
    
    def stop_monitor(self, monitor_id):
        """
        Stop a running monitor.
        
        Args:
            monitor_id: ID of the monitor to stop
        """
        if monitor_id not in self.active_monitors:
            print(f"Error: Monitor '{monitor_id}' not found")
            print(f"Active monitors: {list(self.active_monitors.keys())}")
            return
        
        monitor_info = self.active_monitors[monitor_id]
        print(f"Stopping monitor: {monitor_id}")
        print("Note: Monitor is running in background thread and will stop naturally.")
        print(f"Results will be saved to: {monitor_info['output_file']}")
        
        # Remove from active monitors
        del self.active_monitors[monitor_id]
    
    def show_results(self, log_file):
        """Display monitoring results."""
        import json
        
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"Error: Log file not found: {log_file}")
            return
        
        try:
            with open(log_path, "r") as f:
                results = json.load(f)
            
            print(f"\n=== Monitoring Results: {log_path.name} ===")
            print(f"Total samples: {len(results)}")
            
            if results:
                first_sample = results[0]
                last_sample = results[-1]
                
                print(f"\nFirst sample: {first_sample.get('timestamp', 'N/A')}")
                print(f"Last sample: {last_sample.get('timestamp', 'N/A')}")
                
                # Show sample metrics
                print("\nSample metrics from last reading:")
                if 'system' in last_sample:
                    sys_metrics = last_sample['system']
                    print(f"  CPU: {sys_metrics.get('cpu_usage', 'N/A')}%")
                    print(f"  Memory: {sys_metrics.get('memory_usage', 'N/A')}%")
                
                if 'gpu' in last_sample and last_sample['gpu']:
                    gpu_metrics = last_sample['gpu']
                    print(f"  GPU: {gpu_metrics.get('gpu_util', 'N/A')}%")
                    print(f"  GPU Memory: {gpu_metrics.get('gpu_mem_used', 'N/A')}/{gpu_metrics.get('gpu_mem_total', 'N/A')} MB")
                
                if 'service' in last_sample:
                    print(f"  Service metrics: {len(last_sample['service'])} metrics collected")
            
            print(f"\nFull data available in: {log_file}")
            
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in log file: {log_file}")
        except Exception as e:
            print(f"Error reading results: {e}")
