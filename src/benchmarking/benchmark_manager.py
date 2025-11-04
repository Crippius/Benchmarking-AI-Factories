import argparse
import subprocess
import yaml
from pathlib import Path
import time
import importlib
import json

class BenchmarkManager:
    """Discovers, and runs benchmarks on services deployed on Slurm."""

    def __init__(self, recipes_config_path="configs/benchmark_recipes.yaml"):
        self.base_path = Path(__file__).parent.parent.parent
        with open(self.base_path / recipes_config_path, "r") as f:
            self.recipes = yaml.safe_load(f)

    def _get_job_node(self, job_id):
        """
        Retrieves the node where a Slurm job is running.
        It waits for the job to be in a running state.
        """
        print(f"Waiting for job {job_id} to start and get a node...")
        start_time = time.time()
        while time.time() - start_time < 300:
            try:
                result = subprocess.run(
                    ["scontrol", "show", "job", job_id],
                    capture_output=True, text=True, check=True
                )
                
                job_info = {}
                for item in result.stdout.split():
                    if "=" in item:
                        key, value = item.split("=", 1)
                        job_info[key] = value

                job_state = job_info.get("JobState")
                if job_state == "RUNNING":
                    node = job_info.get("NodeList")
                    if node and node != "(null)":
                        print(f"Job {job_id} is running on node {node}.")
                        return node
                elif job_state not in ("PENDING", "CONFIGURING"):
                    print(f"Job {job_id} is in state {job_state}, not RUNNING.")
                    return None
                
                time.sleep(5)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error checking job {job_id}: {e.stderr.strip()}")
                return None
        print(f"Timeout waiting for job {job_id} to start.")
        return None

    def list_benchmarks(self):
        """Prints a list of all discoverable benchmark recipes."""
        print("Available benchmark recipes:")
        for name, details in self.recipes.items():
            print(f"- {name}: {details.get('description', 'No description')}")

    def run_benchmark(self, benchmark_name, job_id, overrides=None):
        if overrides is None:
            overrides = {}

        recipe = self.recipes.get(benchmark_name)
        if not recipe:
            print(f"Error: Benchmark '{benchmark_name}' not found in config.")
            return

        node = self._get_job_node(job_id)
        if not node:
            print(f"Could not determine the job's node for job_id {job_id}. Aborting benchmark.")
            return

        params = recipe.get("default_params", {}).copy()
        params.update(overrides)

        log_dir = self.base_path / "src" / "benchmarking" / "logs"
        log_dir.mkdir(exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_file = log_dir / f"{benchmark_name}_{job_id}_{timestamp}.json"

        try:
            script_name = recipe['script']
            module_name = f"benchmarks.{script_name.replace('.py', '')}"
            
            print(f"Running benchmark '{benchmark_name}' on node {node}...")
            print(f"Logging results to {log_file}")
            
            benchmark_module = importlib.import_module(module_name)
            
            # Pass the log_file path to the benchmark script
            benchmark_module.run(host=node, log_file=log_file, **params)

        except ImportError as e:
            print(f"Error loading benchmark module: {e}")
        except Exception as e:
            print(f"An error occurred during benchmark execution: {e}")

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
