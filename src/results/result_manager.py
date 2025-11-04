"""Result manager for viewing and analyzing benchmark and monitoring results."""

import json
from pathlib import Path
from datetime import datetime


class ResultManager:
    """Manages result viewing and analysis."""
    
    def __init__(self, job_tracker=None):
        """Initialize the result manager."""
        self.base_path = Path(__file__).parent.parent.parent
        self.results_dir = self.base_path / "results"
        self.job_tracker = job_tracker
    
    def list_results(self, result_type=None):
        """
        List all available result files.
        
        Args:
            result_type: Filter by type ('benchmark', 'monitor', or None for all)
        """
        if result_type and result_type not in ['benchmark', 'monitor']:
            print(f"Error: Invalid type '{result_type}'. Use 'benchmark' or 'monitor'.")
            return
        
        # Determine which directories to search
        if result_type == 'benchmark':
            dirs = [(self.results_dir / "benchmarks", "Benchmark")]
        elif result_type == 'monitor':
            dirs = [(self.results_dir / "monitoring", "Monitor")]
        else:
            dirs = [
                (self.results_dir / "benchmarks", "Benchmark"),
                (self.results_dir / "monitoring", "Monitor")
            ]
        
        total_files = 0
        for result_dir, label in dirs:
            if not result_dir.exists():
                continue
            
            files = sorted(result_dir.glob("*.json"))
            if files:
                print(f"\n{label} Results ({len(files)} files):")
                for f in files:
                    # Get file modification time
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    size = f.stat().st_size
                    print(f"  {f.name}")
                    print(f"    Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')} | Size: {size} bytes")
                total_files += len(files)
        
        if total_files == 0:
            print("No result files found.")
            print(f"Results are stored in: {self.results_dir}")
    
    def show_result(self, log_file):
        """
        Display results from a log file.
        
        Args:
            log_file: Path to the result file
        """
        log_path = Path(log_file)
        
        # If relative path, try to find it in results directory
        if not log_path.is_absolute():
            # Try benchmarks first
            benchmark_path = self.results_dir / "benchmarks" / log_file
            monitor_path = self.results_dir / "monitoring" / log_file
            
            if benchmark_path.exists():
                log_path = benchmark_path
            elif monitor_path.exists():
                log_path = monitor_path
        
        if not log_path.exists():
            print(f"Error: Log file not found: {log_file}")
            return
        
        try:
            with open(log_path, "r") as f:
                results = json.load(f)
            
            print(f"\n=== Results: {log_path.name} ===")
            print(json.dumps(results, indent=2))
            
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in log file: {log_file}")
        except Exception as e:
            print(f"Error reading results: {e}")
    
    def get_job_summary(self, job_id):
        """
        Get a summary of all results for a specific job.
        
        Args:
            job_id: The Slurm job ID
        """
        print(f"\n=== Summary for Job {job_id} ===\n")
        
        # Get job info from tracker
        if self.job_tracker:
            job_info = self.job_tracker.get_job(job_id)
            if job_info:
                print(f"Job Type: {job_info.get('job_type')}")
                print(f"Service: {job_info.get('service_name')}")
                print(f"Node: {job_info.get('node', 'N/A')}")
                print(f"Status: {job_info.get('status')}")
                print(f"Start Time: {job_info.get('start_time')}")
                print()
        
        # Find all result files for this job
        benchmark_files = list((self.results_dir / "benchmarks").glob(f"*_{job_id}_*.json")) if (self.results_dir / "benchmarks").exists() else []
        monitor_files = list((self.results_dir / "monitoring").glob(f"*_{job_id}_*.json")) if (self.results_dir / "monitoring").exists() else []
        
        if not benchmark_files and not monitor_files:
            print(f"No result files found for job {job_id}")
            return
        
        # Show benchmark results
        if benchmark_files:
            print(f"Benchmark Results ({len(benchmark_files)}):")
            for f in benchmark_files:
                print(f"  - {f.name}")
                try:
                    with open(f, "r") as file:
                        data = json.load(file)
                        # Show key metrics if available
                        if 'avg_latency' in data:
                            print(f"    Avg Latency: {data['avg_latency']:.4f}s")
                        if 'successful_requests' in data:
                            print(f"    Successful Requests: {data['successful_requests']}/{data.get('total_requests', 'N/A')}")
                        if 'throughput' in data:
                            print(f"    Throughput: {data['throughput']:.2f}/s")
                except:
                    pass
            print()
        
        # Show monitor results
        if monitor_files:
            print(f"Monitoring Results ({len(monitor_files)}):")
            for f in monitor_files:
                print(f"  - {f.name}")
                try:
                    with open(f, "r") as file:
                        data = json.load(file)
                        if isinstance(data, list) and data:
                            print(f"    Samples: {len(data)}")
                            # Show average CPU/Memory from last few samples
                            recent = data[-5:]
                            cpu_vals = [s.get('system', {}).get('cpu_usage', 0) for s in recent if 'system' in s]
                            mem_vals = [s.get('system', {}).get('memory_usage', 0) for s in recent if 'system' in s]
                            if cpu_vals:
                                print(f"    Avg CPU: {sum(cpu_vals)/len(cpu_vals):.1f}%")
                            if mem_vals:
                                print(f"    Avg Memory: {sum(mem_vals)/len(mem_vals):.1f}%")
                except:
                    pass
            print()
        
        print(f"Full results available in: {self.results_dir}")
