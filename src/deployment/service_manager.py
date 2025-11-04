import argparse
import subprocess
import re
from pathlib import Path
import time
import yaml
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Health check functions need to be available to be mapped from the config file
from deployment.health_checks.chroma_health_check import test_chroma
from deployment.health_checks.ollama_health_check import test_ollama
from deployment.health_checks.postgres_health_check import test_postgres

# Import common utilities
from common.slurm_utils import get_job_node, cancel_job, get_job_status, list_user_jobs
from common.config_loader import ConfigLoader

class ServiceManager:
    """Discovers, deploys, and manages services on Slurm using a central config."""

    def __init__(self, services_config_path="configs/service_recipes.yaml", job_tracker=None):
        # Load configs
        self.base_path = Path(__file__).parent.parent.parent
        config_loader = ConfigLoader(self.base_path)
        self.services = config_loader.load_services()
        
        # Job tracker (optional)
        self.job_tracker = job_tracker
        
        # Health check mapping
        self.health_check_mapping = {
            "ollama": test_ollama,
            "postgres": test_postgres,
            "chroma": test_chroma,
        }

    def start_service(self, service_name, overrides=None):
        """
        Constructs and submits a service script to Slurm using sbatch,
        based on the central config. Overrides allow for dynamic parameter changes.
        """
        if overrides is None:
            overrides = {}

        service_info = self.services.get(service_name)
        if not service_info:
            print(f"Error: Service '{service_name}' not found in config.")
            return

        # --- Prepare sbatch command and environment variables ---
        params = service_info.get("default_params", {}).copy()
        params.update(overrides)

        sbatch_args = ["sbatch"]
        job_env_vars = {}  # Custom environment variables to pass to the job

        # Separate sbatch params from environment variables
        sbatch_params = ["partition", "nodes", "time", "gres"]
        for key, value in params.items():
            if key in sbatch_params:
                sbatch_args.append(f"--{key}={value}")
            else:
                job_env_vars[key] = str(value)
        
        # Export environment variables to the job using --export
        # ALL means inherit all environment variables, then we add/override our custom ones
        if job_env_vars:
            export_string = ",".join([f"{k}={v}" for k, v in job_env_vars.items()])
            sbatch_args.append(f"--export=ALL,{export_string}")
        
        script_path = Path(__file__).parent / service_info["script"]
        if not script_path.is_file():
            print(f"Error: Script for service '{service_name}' not found at {script_path}")
            return None

        sbatch_args.append(str(script_path))

        print(f"Submitting job for service '{service_name}'...")
        print(f"  Command: {' '.join(sbatch_args)}")
        print(f"  Custom Environment Variables: {job_env_vars}")

        try:
            process = subprocess.run(
                sbatch_args,
                capture_output=True, text=True, check=True
            )
            match = re.search(r"Submitted batch job (\d+)", process.stdout)
            if not match:
                print(f"Could not parse Job ID from sbatch output: {process.stdout.strip()}")
                return None

            job_id = match.group(1)
            print(f"Job submitted successfully! Job ID: {job_id}")
            
            # Track job if tracker is available
            if self.job_tracker:
                self.job_tracker.add_job(
                    job_id=job_id,
                    job_type="service",
                    service_name=service_name,
                    config=params
                )

            node = get_job_node(job_id)
            if not node:
                print("Could not determine the job's node. Skipping health check.")
                return job_id
            
            # Update tracker with node info
            if self.job_tracker:
                self.job_tracker.update_job(job_id, node=node)

            health_check_name = service_info.get("health_check")
            health_check_func = self.health_check_mapping.get(health_check_name)

            if health_check_func:
                print(f"Running health check for {service_name} on node {node}...")
                if health_check_func(node):
                    print(f"Health check for {service_name} passed!")
                    if self.job_tracker:
                        self.job_tracker.update_job(job_id, status="healthy")
                else:
                    print(f"Health check for {service_name} failed.")
                    if self.job_tracker:
                        self.job_tracker.update_job(job_id, status="unhealthy")
            else:
                print(f"No health check defined for service '{service_name}'.")
            
            return job_id

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error starting service: {e}")
            if isinstance(e, subprocess.CalledProcessError):
                print(f"Stderr: {e.stderr}")
            return None


    def stop_service(self, job_id):
        """
        Stops a running job using the 'scancel' command.
        """
        print(f"Stopping job {job_id}...")
        if cancel_job(job_id):
            print(f"Job {job_id} cancelled successfully.")
            if self.job_tracker:
                self.job_tracker.update_job(job_id, status="stopped")
        else:
            print(f"Failed to cancel job {job_id}.")

    def list_services(self):
        """
        Prints a list of all discoverable service recipes.
        """
        print("Available service recipes:")
        for name in self.services:
            print(f"- {name}")

    def list_running_services(self):
        """
        Lists jobs for the current user using 'squeue --me'.
        """
        print("Currently running/pending services (squeue --me):")
        output = list_user_jobs()
        if output:
            print(output)

    def check_service(self, job_id):
        """
        Shows detailed information for a specific job using 'scontrol show job'.
        """
        print(f"Checking status of job {job_id}...")
        output = get_job_status(job_id)
        if output:
            print(output)
    
    def show_logs(self, job_id):
        """
        Show logs for a job by finding and displaying the log file.
        """
        # Try to find log files matching the job ID
        log_patterns = [
            f"*_{job_id}.log",
            f"slurm-{job_id}.out"
        ]
        
        found_logs = []
        for pattern in log_patterns:
            logs = list(self.base_path.glob(pattern))
            logs.extend(list((self.base_path / "src" / "deployment").glob(pattern)))
            found_logs.extend(logs)
        
        if not found_logs:
            print(f"No log files found for job {job_id}")
            print(f"Tried patterns: {log_patterns}")
            return
        
        for log_file in found_logs:
            print(f"\n=== Log: {log_file.name} ===")
            try:
                with open(log_file, "r") as f:
                    print(f.read())
            except Exception as e:
                print(f"Error reading log file: {e}")

if __name__ == "__main__":
    manager = ServiceManager()
    parser = argparse.ArgumentParser(
        description="A CLI tool to manage services on a Slurm cluster based on a config file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Define 'start' command
    start_parser = subparsers.add_parser("start", help="Start a service by name.")
    start_parser.add_argument("service_name", choices=list(manager.services.keys()), help="Name of the service to start.")
    start_parser.add_argument("--override", action="append", help="Override a default parameter, e.g., --override OLLAMA_MODEL=qwen3:8b")


    # Define 'stop' command
    stop_parser = subparsers.add_parser("stop", help="Stop a running service by its Slurm Job ID.")
    stop_parser.add_argument("job_id", help="The Job ID of the service to stop.")

    # Define 'list' command
    list_parser = subparsers.add_parser("list", help="List all available service recipes.")

    # Define 'status' command
    status_parser = subparsers.add_parser("status", help="List all running/pending services for the current user.")

    # Define 'check' command
    check_parser = subparsers.add_parser("check", help="Check the detailed status of a specific service by Job ID.")
    check_parser.add_argument("job_id", help="The Job ID of the service to check.")

    args = parser.parse_args()
    
    if args.command == "start":
        overrides = {}
        if args.override:
            for override in args.override:
                if "=" not in override:
                    print(f"Invalid override format: {override}. Use KEY=VALUE.")
                    continue
                key, value = override.split("=", 1)
                overrides[key] = value
        manager.start_service(args.service_name, overrides)
    elif args.command == "stop":
        manager.stop_service(args.job_id)
    elif args.command == "list":
        manager.list_services()
    elif args.command == "status":
        manager.list_running_services()
    elif args.command == "check":
        manager.check_service(args.job_id)
