# Benchmarking AI Factories

This repository contains a unified benchmarking framework for AI Factory workflows on the MeluXina supercomputer. The backend includes reusable modules for managing servers, clients, monitoring, and logging within an HPC environment.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Crippius/Benchmarking-AI-Factories.git
cd Benchmarking-AI-Factories

# 2. Set up virtual environment
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv if not already installed
uv venv
source .venv/bin/activate

# 3. List available services
./aif-cli service list

# 4. Start a service
./aif-cli service start ollama

# 5. Run a benchmark (use job_id from step 4)
./aif-cli benchmark run ollama_latency --job-id <job_id>
```

For detailed usage, see [CLI Guide](docs/CLI_GUIDE.md).

---

## High-Level Architecture

The framework is designed with a backend/frontend architecture:

### Backend 

The backend is responsible for deploying services, generating workloads, and collecting results. It consists of four main components:

- **Server:** Deploys and manages the services under test (e.g., vLLM inference servers, databases).
- **Client:** Generates traffic to stress the server components
- **Monitor:** Collects real-time performance metrics like latency, throughput, and resource usage.
- **Log:** Aggregates logs from all components for debugging and detailed analysis.

### Frontend

A unified command-line interface (CLI) that provides a single control point for all operations:

- **Service Management:** Deploy, stop, and monitor services on Slurm
- **Benchmark Execution:** Run performance benchmarks against deployed services
- **Job Tracking:** Track and query all running jobs and their metadata
- **Results Analysis:** View and analyze benchmark results

All operations are submitted as Slurm jobs, ensuring proper resource management on the HPC cluster.

---

## Repository Structure

The directory structure is organized to reflect the backend architecture, separating the source code, documentation, scripts, and configurations.

```
.
├── README.md
├── configs/
│   ├── service_recipes.yaml      # Service deployment configurations
│   └── benchmark_recipes.yaml    # Benchmark test configurations
├── docs/
│   └── CLI_GUIDE.md              # Detailed CLI usage guide
├── examples/
└── src/
    ├── aif_cli.py                # 🆕 Unified CLI entry point
    ├── common/                   # 🆕 Shared utilities
    │   ├── config_loader.py      # Configuration management
    │   ├── job_tracker.py        # Job metadata tracking
    │   └── slurm_utils.py        # Slurm helper functions
    ├── benchmarking/
    │   ├── benchmark_manager.py  # Benchmark orchestration
    │   └── benchmarks/           # Benchmark implementations
    ├── benchmarks/
    ├── deployment/
    │   ├── service_manager.py    # Service deployment manager
    │   ├── health_checks/        # Service health checks
    │   └── services/             # Service deployment scripts
    │       ├── run_chromadb_server.sh
    │       ├── run_ollama_server.sh
    │       └── run_postgresql_server.sh
    └── monitoring/
```

---

## Tools & Stacks

- **Orchestration:** Slurm
- **Framework:** Python
- **Inference:** Ollama
- **Databases:** PostgreSQL and ChromaDB
- **Monitoring:** Prometheus & Grafana
- **Load Generation:** Dask, Spark

---

## Getting Started

We recommend using `uv` to manage the Python environment. `uv` is a fast, next-generation Python package manager and it works in HPC cluster such as MeluXina by managing python virtual environments and dependencies.

### 1. Install uv

To install `uv`, run the following command in your terminal:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create and Activate the Virtual Environment

Once `uv` is installed, create a virtual environment and install the project dependencies:

```bash
# Create the virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate
```

The required dependencies will be automatically installed from the `pyproject.toml` file.
    
### 3. Using the Unified CLI

The AI Factory CLI (`aif-cli`) provides a single interface for all operations. 

Run commands from the project root directory:

#### Managing Services

```bash
# List available services
./aif-cli service list

# Start a service (submits a Slurm job)
./aif-cli service start ollama

# Start with custom parameters
./aif-cli service start ollama --override OLLAMA_MODEL=qwen3:8b

# Check running services
./aif-cli service status

# Check specific job details
./aif-cli service check <job_id>

# Stop a service
./aif-cli service stop <job_id>

# View service logs
./aif-cli service logs <job_id>
```

#### Running Benchmarks

```bash
# List available benchmarks
./aif-cli benchmark list

# Run a benchmark against a deployed service
./aif-cli benchmark run ollama_latency --job-id <service_job_id>

# Run with custom parameters
./aif-cli benchmark run ollama_latency --job-id <job_id> --override num_requests=100

# View benchmark results
./aif-cli benchmark results <path_to_log_file>
```

#### Monitoring Services

```bash
# List available monitors
./aif-cli monitor list

# Start monitoring a service (runs in background)
./aif-cli monitor start ollama --job-id <service_job_id> --duration 300

# Monitor with custom parameters
./aif-cli monitor start ollama --job-id <job_id> --duration 600 --interval 10

# View monitoring results
./aif-cli monitor results <path_to_log_file>
```

#### Viewing Results

```bash
# List all results (benchmarks and monitoring)
./aif-cli results list

# List only benchmarks
./aif-cli results list --type benchmark

# Show specific result file
./aif-cli results show <log_file>

# Get complete summary for a job
./aif-cli results summary --job-id <job_id>
```

### 4. Complete Workflow Example

```bash
# 1. Start a service
./aif-cli service start ollama
# Note the job ID (e.g., 12345)

# 2. Start monitoring in background
./aif-cli monitor start ollama --job-id 12345 --duration 300 &

# 3. Run benchmarks
./aif-cli benchmark run ollama_latency --job-id 12345

# 4. View all results for the job
./aif-cli results summary --job-id 12345

# 5. Stop service
./aif-cli service stop 12345
```

### 5. Legacy Commands (Still Supported)

You can still use the individual managers directly if needed:

```bash
# Service management
python src/deployment/service_manager.py list
python src/deployment/service_manager.py start ollama

# Benchmark execution
python src/benchmarking/benchmark_manager.py list
python src/benchmarking/benchmark_manager.py run ollama_latency --job_id <job_id>
```

For detailed CLI documentation, see [docs/CLI_GUIDE.md](docs/CLI_GUIDE.md).
