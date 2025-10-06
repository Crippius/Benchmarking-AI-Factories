import argparse
import subprocess
import re
from pathlib import Path

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
            "ollama": "services/run_ollama_server.sh",
            "postgresql": "services/run_postgresql_server.sh",
        }
        services = {}
        for name, script_name in service_definitions.items():
            services[name] = Path(__file__).parent / script_name
        return services

    def start_service(self, service_name):
        """
        Submits a service script to Slurm using the 'sbatch' command.
        Parses and prints the returned Job ID.
        """
        script_path = self.services.get(service_name)
        if not script_path or not script_path.is_file():
            print(f"Error: Service '{service_name}' or its script not found.")
            return

        print(f"Submitting job for service '{service_name}'...")
        try:
            process = subprocess.run(
                ["sbatch", str(script_path)],
                capture_output=True, text=True, check=True
            )
            match = re.search(r"Submitted batch job (\d+)", process.stdout)
            if match:
                job_id = match.group(1)
                print(f"Job submitted successfully! Job ID: {job_id}")
                return job_id
            else:
                print(f"Could not parse Job ID from sbatch output: {process.stdout.strip()}")
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
            # We directly print the output of squeue
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
            # We directly print the output of scontrol
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
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Define 'start' command
    start_parser = subparsers.add_parser("start", help="Start a service by name.")
    start_parser.add_argument("service_name", choices=manager.services.keys(), help="Name of the service to start.")

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
        manager.start_service(args.service_name)
    elif args.command == "stop":
        manager.stop_service(args.job_id)
    elif args.command == "list":
        manager.list_services()
    elif args.command == "status":
        manager.list_running_services()
    elif args.command == "check":
        manager.check_service(args.job_id)
