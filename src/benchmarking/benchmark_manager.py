import argparse
import subprocess
import yaml
from pathlib import Path
import time
import importlib
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.slurm_utils import get_job_node
from common.config_loader import ConfigLoader

class BenchmarkManager:
    """Discovers, and runs benchmarks on services deployed on Slurm."""

    def __init__(self, recipes_config_path="configs/benchmark_recipes.yaml", job_tracker=None):
        self.base_path = Path(__file__).parent.parent.parent
        config_loader = ConfigLoader(self.base_path)
        self.recipes = config_loader.load_benchmarks()
        self.job_tracker = job_tracker

    def list_benchmarks(self):
        """Prints a list of all discoverable benchmark recipes."""
        print("Available benchmark recipes:")
        for name, details in self.recipes.items():
            print(f"- {name}: {details.get('description', 'No description')}")

    def run_benchmark(self, benchmark_name, job_id, overrides=None):
        """Run a benchmark against a service."""
        if overrides is None:
            overrides = {}

        recipe = self.recipes.get(benchmark_name)
        if not recipe:
            print(f"Error: Benchmark '{benchmark_name}' not found in config.")
            return

        # Get node from job tracker if available, otherwise query Slurm
        node = None
        if self.job_tracker:
            job_info = self.job_tracker.get_job(job_id)
            if job_info:
                node = job_info.get("node")
        
        if not node:
            node = get_job_node(job_id)
        
        if not node:
            print(f"Could not determine the job's node for job_id {job_id}. Aborting benchmark.")
            return

        params = recipe.get("default_params", {}).copy()
        params.update(overrides)

        log_dir = self.base_path / "results" / "benchmarks"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_file = log_dir / f"{benchmark_name}_{job_id}_{timestamp}.json"

        try:
            script_name = recipe['script']
            module_name = f"benchmarking.benchmarks.{script_name.replace('.py', '')}"
            
            print(f"Running benchmark '{benchmark_name}' on node {node}...")
            print(f"Logging results to {log_file}")
            
            # Import the benchmark module
            benchmark_module = importlib.import_module(module_name)
            
            # Pass benchmark_name and all parameters
            benchmark_module.run(
                host=node,
                log_file=str(log_file),
                benchmark_name=benchmark_name,
                **params
            )
            
            print(f"Benchmark completed. Results saved to {log_file}")

        except ImportError as e:
            print(f"Error loading benchmark module: {e}")
        except Exception as e:
            print(f"An error occurred during benchmark execution: {e}")
    
    def show_results(self, log_file):
        """Display benchmark results from a log file."""
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"Error: Log file not found: {log_file}")
            return
        
        try:
            with open(log_path, "r") as f:
                results = json.load(f)
            
            print(f"\n=== Benchmark Results: {log_path.name} ===")
            print(json.dumps(results, indent=2))
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in log file: {log_file}")
        except Exception as e:
            print(f"Error reading results: {e}")

if __name__ == "__main__":
    manager = BenchmarkManager()
    parser = argparse.ArgumentParser(
        description="A CLI tool to run benchmarks on services in a Slurm cluster.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List all available benchmarks.")

    run_parser = subparsers.add_parser("run", help="Run a benchmark.")
    run_parser.add_argument("benchmark_name", choices=list(manager.recipes.keys()), help="Name of the benchmark to run.")
    run_parser.add_argument("--job_id", required=True, help="The Slurm Job ID of the service to benchmark.")
    run_parser.add_argument("--override", action="append", help="Override a default parameter, e.g., --override requests=100")

    args = parser.parse_args()

    if args.command == "list":
        manager.list_benchmarks()
    elif args.command == "run":
        overrides = {}
        if args.override:
            for override in args.override:
                if "=" not in override:
                    print(f"Invalid override format: {override}. Use KEY=VALUE.")
                    continue
                key, value = override.split("=", 1)
                overrides[key] = value
        manager.run_benchmark(args.benchmark_name, args.job_id, overrides)
