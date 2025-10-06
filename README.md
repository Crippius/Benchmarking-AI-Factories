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
│── configs/              # Configuration files for services
├── docs/                 # Project documentation, reports, and presentations
├── examples/             # Example slurm scripts
└── src/                  # Main source code for the backend
    ├── benchmarks/       # Benchmark implementations (Client)
    │   └── inference.py
    ├── deployment/       # Scripts to deploy services (Server)
    │   ├── services/
    │   │   └── run_ollama_server.sh
    │   └── service_deployment.py
    └── monitoring/       # Metrics collection and utilities (Monitor/Log)
```



---

## Tools & Stacks

- **Orchestration:** Slurm ,K8s
- **Framework:** Python
- **Inference:** vLLM
- **Databases:** PostgreSQL 
- **Monitoring:** Prometheus & Grafana
- **Load Generation:** Dask, Spark

---