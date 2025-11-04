# Results Directory

This directory contains all benchmark and monitoring results from the AI Factory CLI.

## Structure

```
results/
├── benchmarks/          # Benchmark results (JSON files)
│   └── {benchmark}_{job_id}_{timestamp}.json
└── monitoring/          # Monitoring results (JSON files)
    └── {service}_monitor_{job_id}_{timestamp}.json
```

## File Naming Convention

### Benchmarks
Format: `{benchmark_name}_{service_job_id}_{timestamp}.json`

Example: `ollama_latency_12345_20251104-123456.json`

### Monitoring
Format: `{service_name}_monitor_{service_job_id}_{timestamp}.json`

Example: `ollama_monitor_12345_20251104-123456.json`

## Viewing Results

### Using the CLI

```bash
# List all results
./aif-cli results list

# List only benchmarks
./aif-cli results list --type benchmark

# List only monitoring
./aif-cli results list --type monitor

# View specific result
./aif-cli results show results/benchmarks/ollama_latency_12345_*.json

# Get summary for a job (shows all results for that job)
./aif-cli results summary --job-id 12345
```

### Direct File Access

All results are stored as JSON files and can be viewed with any text editor or JSON viewer:

```bash
# Using cat
cat results/benchmarks/ollama_latency_12345_20251104-123456.json

# Using jq for pretty printing
jq . results/benchmarks/ollama_latency_12345_20251104-123456.json

# Using Python
python -m json.tool results/benchmarks/ollama_latency_12345_20251104-123456.json
```

## Result Format

### Benchmark Results

Benchmark results contain metrics specific to each benchmark type:

```json
{
  "total_requests": 10,
  "successful_requests": 10,
  "min_latency": 0.5,
  "max_latency": 1.2,
  "avg_latency": 0.8
}
```

### Monitoring Results

Monitoring results are time-series data with system, GPU, and service metrics:

```json
[
  {
    "timestamp": "2025-11-04T12:00:00",
    "system": {
      "cpu_usage": 45.2,
      "memory_usage": 60.1
    },
    "gpu": {
      "gpu_util": 80.5,
      "gpu_mem_used": 8192,
      "gpu_mem_total": 16384
    },
    "service": {
      "service_specific_metric": 123
    }
  }
]
```

## Retention Policy

Results are kept indefinitely. You can manually delete old results:

```bash
# Delete benchmarks older than 30 days
find results/benchmarks -name "*.json" -mtime +30 -delete

# Delete all results for a specific job
rm results/benchmarks/*_12345_*.json
rm results/monitoring/*_12345_*.json
```

## Integration with Job Tracker

The CLI tracks all jobs in `.aif_jobs.json` at the project root. Results are linked to jobs via the job_id in the filename.

To see all results for a specific job:
```bash
./aif-cli results summary --job-id 12345
```
