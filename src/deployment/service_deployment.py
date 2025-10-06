import argparse
import subprocess
from pathlib import Path

class Service:
    """Represents a deployable service."""
    def __init__(self, name, script_name):
        self.name = name
        self.script_path = Path(__file__).parent / script_name

    def launch(self):
        """Launches the service using sbatch."""
        if not self.script_path.is_file():
            print(f"Error: Slurm script '{self.script_path.name}' not found at {self.script_path}")
            return

        print(f"Submitting job for service '{self.name}' using script '{self.script_path.name}'...")

        try:
            process = subprocess.run(
                ["sbatch", str(self.script_path)],
                capture_output=True,
                text=True,
                check=True
            )
            print("Job submitted successfully!")
            print(f"Submission output: {process.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"Error submitting job to Slurm.")
            print(f"Return code: {e.returncode}")
            print(f"Stdout: {e.stdout.strip()}")
            print(f"Stderr: {e.stderr.strip()}")
        except FileNotFoundError:
            print("sbatch command not found. Are you on a system with Slurm installed?")

class ServiceDeployer:
    """Discovers and deploys services."""
    def __init__(self):
        self.services = {}
        self.discover_services()

    def discover_services(self):
        """Discovers available services."""
        # This can be extended to dynamically discover services, e.g., by scanning a directory.
        service_definitions = {
            "ollama": "services/run_ollama_server.sh",
            # "vllm": "run_vllm_server.sh",
        }
        for name, script_name in service_definitions.items():
            self.services[name] = Service(name, script_name)

    def launch_service(self, service_name):
        """Launches a service by name."""
        if service_name not in self.services:
            print(f"Error: Service '{service_name}' is not defined.")
            print(f"Available services: {list(self.services.keys())}")
            return
        
        service = self.services[service_name]
        service.launch()

if __name__ == "__main__":
    deployer = ServiceDeployer()
    
    parser = argparse.ArgumentParser(description="Launch a service on Slurm.")
    parser.add_argument(
        "service",
        type=str,
        choices=deployer.services.keys(),
        help="The name of the service to launch."
    )
    args = parser.parse_args()

    deployer.launch_service(args.service)