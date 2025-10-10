import argparse
import subprocess
import re
from pathlib import Path
import time
import yaml
import os

# Health check functions need to be available to be mapped from the config file
from health_checks.chroma_health_check import test_chroma
from health_checks.ollama_health_check import test_ollama
from health_checks.postgres_health_check import test_postgres

class ServiceManager:
    """Discovers, deploys, and manages services on Slurm using a central config."""

    def __init__(self, services_config_path="configs/service_recipes.yaml"):
        # Load configs
        base_path = Path(__file__).parent.parent.parent
        with open(base_path / services_config_path, "r") as f:
            self.services = yaml.safe_load(f)
        
        # Health check mapping
        self.health_check_mapping = {
            "ollama": test_ollama,
            "postgres": test_postgres,
            "chroma": test_chroma,
        }

    def _get_job_node(self, job_id):
        """
        Retrieves the node where a Slurm job is running.
        It waits for the job to be in a running state.
        """
        print(f"Waiting for job {job_id} to start and get a node...")
        start_time = time.time()
        # Increased timeout to 300 seconds (5 minutes) for busy clusters
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
                
                time.sleep(5)  # Wait 5 seconds before checking again
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error checking job {job_id}: {e.stderr.strip()}")
                return None
        print(f"Timeout waiting for job {job_id} to start.")
        return None


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
            return

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
                return

            job_id = match.group(1)
            print(f"Job submitted successfully! Job ID: {job_id}")

            node = self._get_job_node(job_id)
            if not node:
                print("Could not determine the job's node. Skipping health check.")
                return

            health_check_name = service_info.get("health_check")
            health_check_func = self.health_check_mapping.get(health_check_name)

            if health_check_func:
                print(f"Running health check for {service_name} on node {node}...")
                if health_check_func(node):
                    print(f"Health check for {service_name} passed!")
                else:
                    print(f"Health check for {service_name} failed.")
            else:
                print(f"No health check defined for service '{service_name}'.")


        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error starting service: {e}")
            if isinstance(e, subprocess.CalledProcessError):
                print(f"Stderr: {e.stderr}")


    def stop_service(self, job_id):
        """
        Stops a running job using the 'scancel' command.
        """
        print(f"Stopping job {job_id}...")
        try:
            subprocess.run(["scancel", job_id], check=True, capture_output=True, text=True)
            print(f"Job {job_id} cancelled successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error stopping service {job_id}: {e.stderr.strip()}")

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
        try:
            result = subprocess.run(["squeue", "--me"], check=True, text=True, capture_output=True)
            print(result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error listing running services: {e.stderr.strip()}")

    def check_service(self, job_id):
        """
        Shows detailed information for a specific job using 'scontrol show job'.
        """
        print(f"Checking status of job {job_id}...")
        try:
            result = subprocess.run(["scontrol", "show", "job", job_id], check=True, text=True, capture_output=True)
            print(result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error checking service {job_id}: {e.stderr.strip()}")

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
