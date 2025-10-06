# Benchmarking AI Factories

This repository contains a unified benchmarking framework for AI Factory workflows on the MeluXina supercomputer.  The backend includes reusable modules for managing servers, clients, monitoring, and logging within an HPC environment.

## High-Level Architecture

The framework is designed with a backend/frontend architecture.
## Backend 

The backend is responsible for deploying services, generating workloads, and collecting results. It consists of four main components:


- **Server:** Deploys and manages the services under test (e.g., vLLM inference servers, databases).
- **Client:** Generates traffic to stress the server components
- **Monitor:** Collects real-time performance metrics like latency, throughput, and resource usage.
- **Log:** Aggregates logs from all components for debugging and detailed analysis.

## Frontend

TBD

---

## Repository Structure

The directory structure is organized to reflect the backend architecture, separating the source code, documentation, scripts, and configurations.

```
.
├── README.md
├── configs/
├── docs/
├── examples/
└── src/
    ├── benchmarks/
    ├── deployment/
    │   ├── health_checks/
    │   ├── services/
    │   │   ├── run_chromadb_server.sh
    │   │   ├── run_ollama_server.sh
    │   │   └── run_postgresql_server.sh
    │   └── service_manager.py
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
    
### 3. Run the Service

```bash
python src/deployment/service_manager.py list
python src/deployment/service_manager.py start ollama
```
