"""
AI Factory CLI - Unified command-line interface for managing services, benchmarks, and monitoring.
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from common.config_loader import ConfigLoader
from common.job_tracker import JobTracker
from deployment.service_manager import ServiceManager
from benchmarking.benchmark_manager import BenchmarkManager
from monitoring.monitor_manager import MonitorManager
from results.result_manager import ResultManager


class AIFactoryCLI:
    """Main CLI controller for AI Factory operations."""
    
    def __init__(self):
        """Initialize the CLI with all managers."""
        self.config_loader = ConfigLoader()
        self.job_tracker = JobTracker()
        self.service_manager = ServiceManager(job_tracker=self.job_tracker)
        self.benchmark_manager = BenchmarkManager(job_tracker=self.job_tracker)
        self.monitor_manager = MonitorManager(job_tracker=self.job_tracker)
        self.result_manager = ResultManager(job_tracker=self.job_tracker)
    
    def run(self):
        """Run the CLI with argument parsing."""
        parser = argparse.ArgumentParser(
            prog="aif-cli",
            description="AI Factory CLI - Manage services, benchmarks, and monitoring on Slurm",
            formatter_class=argparse.RawTextHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", required=True, help="Command to execute")
        
        # Service commands
        self._add_service_commands(subparsers)
        
        # Benchmark commands
        self._add_benchmark_commands(subparsers)
        
        # Monitor commands
        self._add_monitor_commands(subparsers)
        
        # Results commands
        self._add_results_commands(subparsers)
        
        # Parse and execute
        args = parser.parse_args()
        self._execute_command(args)
    
    def _add_service_commands(self, subparsers):
        """Add service management commands."""
        service_parser = subparsers.add_parser("service", help="Service management commands")
        service_subparsers = service_parser.add_subparsers(dest="service_command", required=True)
        
        # service start
        start_parser = service_subparsers.add_parser("start", help="Start a service")
        start_parser.add_argument("service_name", help="Name of the service to start")
        start_parser.add_argument("--override", action="append", help="Override parameters (KEY=VALUE)")
        
        # service stop
        stop_parser = service_subparsers.add_parser("stop", help="Stop a running service")
        stop_parser.add_argument("job_id", help="Job ID to stop")
        
        # service list
        service_subparsers.add_parser("list", help="List available services")
        
        # service status
        service_subparsers.add_parser("status", help="Show all running services")
        
        # service check
        check_parser = service_subparsers.add_parser("check", help="Check specific job status")
        check_parser.add_argument("job_id", help="Job ID to check")
        
        # service logs
        logs_parser = service_subparsers.add_parser("logs", help="Show job logs")
        logs_parser.add_argument("job_id", help="Job ID to show logs for")
    
    def _add_benchmark_commands(self, subparsers):
        """Add benchmark commands."""
        benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark commands")
        benchmark_subparsers = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)
        
        # benchmark run
        run_parser = benchmark_subparsers.add_parser("run", help="Run a benchmark")
        run_parser.add_argument("benchmark_name", help="Name of the benchmark to run")
        run_parser.add_argument("--job-id", required=True, help="Service job ID to benchmark")
        run_parser.add_argument("--override", action="append", help="Override parameters (KEY=VALUE)")
        
        # benchmark list
        benchmark_subparsers.add_parser("list", help="List available benchmarks")
        
        # benchmark results
        results_parser = benchmark_subparsers.add_parser("results", help="Show benchmark results")
        results_parser.add_argument("log_file", help="Path to the benchmark log file")
    
    def _add_monitor_commands(self, subparsers):
        """Add monitoring commands."""
        monitor_parser = subparsers.add_parser("monitor", help="Monitoring commands")
        monitor_subparsers = monitor_parser.add_subparsers(dest="monitor_command", required=True)
        
        # monitor start
        start_parser = monitor_subparsers.add_parser("start", help="Start monitoring a service")
        start_parser.add_argument("service_name", help="Name of the service to monitor")
        start_parser.add_argument("--job-id", required=True, help="Service job ID")
        start_parser.add_argument("--duration", type=int, default=300, help="Duration in seconds (default: 300)")
        start_parser.add_argument("--interval", type=int, default=5, help="Interval in seconds (default: 5)")
        
        # monitor list
        monitor_subparsers.add_parser("list", help="List available monitors")
        
        # monitor results
        results_parser = monitor_subparsers.add_parser("results", help="Show monitoring results")
        results_parser.add_argument("log_file", help="Path to the monitoring log file")
    
    def _add_results_commands(self, subparsers):
        """Add results management commands."""
        results_parser = subparsers.add_parser("results", help="Results management commands")
        results_subparsers = results_parser.add_subparsers(dest="results_command", required=True)
        
        # results list
        list_parser = results_subparsers.add_parser("list", help="List all result files")
        list_parser.add_argument("--type", choices=['benchmark', 'monitor'], help="Filter by type")
        
        # results show
        show_parser = results_subparsers.add_parser("show", help="Show specific result file")
        show_parser.add_argument("log_file", help="Path to the result file")
        
        # results summary
        summary_parser = results_subparsers.add_parser("summary", help="Show summary for a job")
        summary_parser.add_argument("--job-id", required=True, help="Job ID to summarize")
    
    def _execute_command(self, args):
        """Execute the parsed command."""
        if args.command == "service":
            self._execute_service_command(args)
        elif args.command == "benchmark":
            self._execute_benchmark_command(args)
        elif args.command == "monitor":
            self._execute_monitor_command(args)
        elif args.command == "results":
            self._execute_results_command(args)
    
    def _execute_service_command(self, args):
        """Execute service commands."""
        if args.service_command == "start":
            overrides = self._parse_overrides(args.override)
            self.service_manager.start_service(args.service_name, overrides)
        
        elif args.service_command == "stop":
            self.service_manager.stop_service(args.job_id)
        
        elif args.service_command == "list":
            self.service_manager.list_services()
        
        elif args.service_command == "status":
            self.service_manager.list_running_services()
        
        elif args.service_command == "check":
            self.service_manager.check_service(args.job_id)
        
        elif args.service_command == "logs":
            self.service_manager.show_logs(args.job_id)
    
    def _execute_benchmark_command(self, args):
        """Execute benchmark commands."""
        if args.benchmark_command == "run":
            overrides = self._parse_overrides(args.override)
            self.benchmark_manager.run_benchmark(args.benchmark_name, args.job_id, overrides)
        
        elif args.benchmark_command == "list":
            self.benchmark_manager.list_benchmarks()
        
        elif args.benchmark_command == "results":
            self.benchmark_manager.show_results(args.log_file)
    
    def _execute_monitor_command(self, args):
        """Execute monitoring commands."""
        if args.monitor_command == "start":
            self.monitor_manager.start_monitor(
                args.service_name,
                args.job_id,
                duration=args.duration,
                interval=args.interval
            )
        
        elif args.monitor_command == "list":
            self.monitor_manager.list_monitors()
        
        elif args.monitor_command == "results":
            self.monitor_manager.show_results(args.log_file)
    
    def _execute_results_command(self, args):
        """Execute results commands."""
        if args.results_command == "list":
            self.result_manager.list_results(result_type=args.type)
        
        elif args.results_command == "show":
            self.result_manager.show_result(args.log_file)
        
        elif args.results_command == "summary":
            self.result_manager.get_job_summary(args.job_id)
    
    def _parse_overrides(self, override_list):
        """Parse override arguments into a dictionary."""
        overrides = {}
        if override_list:
            for override in override_list:
                if "=" not in override:
                    print(f"Warning: Invalid override format '{override}'. Use KEY=VALUE.")
                    continue
                key, value = override.split("=", 1)
                overrides[key] = value
        return overrides


def main():
    """Main entry point."""
    cli = AIFactoryCLI()
    cli.run()


if __name__ == "__main__":
    main()
