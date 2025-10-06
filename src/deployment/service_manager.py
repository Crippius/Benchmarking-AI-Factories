import argparse
import subprocess
import re
from pathlib import Path
import time
from health_checks.chroma_health_check import test_chroma
from health_checks.ollama_health_check import test_ollama
from health_checks.postgres_health_check import test_postgres

class ServiceManager:
    """Discovers, deploys, and manages services on Slurm."""

    def __init__(self):
        self.services = self._discover_services()

    def _discover_services(self):
        """
        Identifies available service scripts in the 'services' subdirectory.
        Returns a dictionary mapping service names to their script paths.
        """
        service_definitions = {
            "ollama": {
                "script": "services/run_ollama_server.sh",
                "health_check": test_ollama,
            },
            "postgresql": {
                "script": "services/run_postgresql_server.sh",
                "health_check": test_postgres,
            },
            "chroma": {
                "script": "services/run_chromadb_server.sh",
                "health_check": test_chroma,
            },
        }
        services = {}
        for name, definition in service_definitions.items():
            services[name] = {
                "script": Path(__file__).parent / definition["script"],
                "health_check": definition["health_check"],
            }
        return services

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
                
                # FIX: Use a more robust method to parse the scontrol output
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


    def start_service(self, service_name):
        """
        Submits a service script to Slurm using the 'sbatch' command,
        waits for the service to start, and then runs a health check.
        """
        service_info = self.services.get(service_name)
        if not service_info or not service_info["script"].is_file():
            print(f"Error: Service '{service_name}' or its script not found.")
            return

        print(f"Submitting job for service '{service_name}'...")
        try:
            process = subprocess.run(
                ["sbatch", str(service_info["script"])],
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

            print(f"Running health check for {service_name} on node {node}...")
            health_check_func = service_info["health_check"]
            if health_check_func(node):
                print(f"Health check for {service_name} passed!")
            else:
                print(f"Health check for {service_name} failed.")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error starting service: {e}")

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
        description="A CLI tool to manage services on a Slurm cluster.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # This script is now compatible with older Python versions
    subparsers = parser.add_subparsers(dest="command")

    # Define 'start' command
    start_parser = subparsers.add_parser("start", help="Start a service by name.")
    start_parser.add_argument("service_name", choices=list(manager.services.keys()), help="Name of the service to start.")

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
    
    # Manually check if a command was provided for older Python versions
    if not args.command:
        parser.print_help()
    elif args.command == "start":
        manager.start_service(args.service_name)
    elif args.command == "stop":
        manager.stop_service(args.job_id)
    elif args.command == "list":
        manager.list_services()
    elif args.command == "status":
        manager.list_running_services()
    elif args.command == "check":
        manager.check_service(args.job_id)