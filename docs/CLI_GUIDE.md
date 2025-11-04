# AI Factory CLI - Quick Start Guide

## Overview

The AI Factory CLI (`aif-cli`) is a unified command-line interface for managing services, benchmarks, and monitoring on Slurm clusters. It combines all functionality into a single, easy-to-use tool.

## Installation

The CLI is ready to use after setting up your virtual environment. Simply run it from the project root:

```bash
# From the project root directory
./aif-cli <command> <subcommand> [options]
```

The `aif-cli` wrapper script automatically uses the virtual environment if available.

## Commands Overview

### Service Management

```bash
# List available services
./aif-cli service list

# Start a service
./aif-cli service start ollama
./aif-cli service start ollama --override OLLAMA_MODEL=llama2

# Check all running services
./aif-cli service status

# Check specific job details
./aif-cli service check <job_id>

# View job logs
./aif-cli service logs <job_id>

# Stop a service
./aif-cli service stop <job_id>
```

### Benchmark Management

```bash
# List available benchmarks
./aif-cli benchmark list

# Run a benchmark
./aif-cli benchmark run ollama_latency --job-id <service_job_id>
./aif-cli benchmark run ollama_latency --job-id <service_job_id> --override num_requests=100

# View benchmark results
./aif-cli benchmark results <log_file_path>
```

## Complete Workflow Example

### 1. Start a Service

```bash
./aif-cli service start ollama --override OLLAMA_MODEL=qwen3:0.6b
```

Output:
```
Submitting job for service 'ollama'...
Job submitted successfully! Job ID: 12345
Waiting for job 12345 to start and get a node...
Job 12345 is running on node mel1234.
Running health check for ollama on node mel1234...
✓ Health check for ollama passed!
```

### 2. Run a Benchmark

```bash
./aif-cli benchmark run ollama_latency --job-id 12345 --override num_requests=50
```

### 3. View Results

```bash
./aif-cli benchmark results src/benchmarking/logs/ollama_latency_12345_20251104-100000.json
```

### 4. Clean Up

```bash
./aif-cli service stop 12345
```

## Advanced Usage

### Override Multiple Parameters

```bash
./aif-cli service start ollama \
  --override OLLAMA_MODEL=llama2 \
  --override time=02:00:00 \
  --override partition=gpu
```

### Chain Commands

```bash
# Start service and get job ID
JOB_ID=$(./aif-cli service start ollama | grep "Job ID:" | awk '{print $NF}')

# Wait a moment for service to be ready
sleep 30

# Run benchmark
./aif-cli benchmark run ollama_latency --job-id $JOB_ID
```

## Available Services

- **ollama**: LLM inference service
  - Default model: qwen3:0.6b
  - Partition: gpu
  - Time: 01:00:00

- **postgresql**: PostgreSQL database
  - Partition: cpu
  - Time: 01:00:00

- **chroma**: ChromaDB vector database
  - Partition: cpu
  - Time: 01:00:00

## Available Benchmarks

- **ollama_latency**: Measures request latency
  - Parameters: model, prompt, num_requests

- **ollama_streaming**: Measures TTFT and tokens/sec
  - Parameters: model, prompt

- **chroma_throughput**: Measures read/write throughput
  - Parameters: collection_name, documents

- **chroma_query**: Measures query performance
  - Parameters: collection_name, documents, n_results

- **postgres_throughput**: Measures read/write throughput
  - Parameters: table_name, rows

- **postgres_transaction**: Measures transactions per second
  - Parameters: transactions

## Job Tracking

The CLI automatically tracks all jobs in `.aif_jobs.json` at the project root. This file maintains:
- Job ID and type (service/benchmark)
- Service name
- Node assignment
- Start time and status
- Configuration used

## Troubleshooting

### Service won't start
```bash
# Check Slurm queue
./aif-cli service status

# Check specific job
./aif-cli service check <job_id>

# View logs
./aif-cli service logs <job_id>
```

### Benchmark fails
- Ensure the service job is still running
- Check that the job ID is correct
- Verify the service passed its health check

### Import errors
- Make sure you're running from the project root directory
- Verify all dependencies are installed: `uv sync`
- The wrapper script (`./aif-cli`) handles the virtual environment automatically

## File Locations

- **Service scripts**: `src/deployment/services/`
- **Benchmark scripts**: `src/benchmarking/benchmarks/`
- **Benchmark logs**: `src/benchmarking/logs/`
- **Job tracker**: `.aif_jobs.json` (project root)
- **Service logs**: Project root (e.g., `ollama_server_12345.log`)

## Next Steps

See the main README.md for:
- Workflow orchestration (coming soon)
- Monitoring integration (coming soon)
- Result analysis tools (coming soon)
