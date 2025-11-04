import requests as http_requests
import time
import json

def _save_results(log_file, results):
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=4)

def run_latency(host, model, prompt, num_requests, log_file, **kwargs):
    """Runs a latency benchmark against an Ollama service."""
    print(f"Starting Ollama latency benchmark on {host}...")
    print(f"Model: {model}, Prompt: '{prompt}', Requests: {num_requests}")

    base_url = f"http://{host}:11434"
    api_url = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    latencies = []
    for i in range(int(num_requests)):
        try:
            start_time = time.time()
            response = http_requests.post(api_url, json=payload, timeout=300)
            response.raise_for_status()
            end_time = time.time()
            latency = end_time - start_time
            latencies.append(latency)
            print(f"Request {i+1}/{num_requests} successful in {latency:.2f}s")
        except http_requests.exceptions.RequestException as e:
            print(f"Request {i+1}/{num_requests} failed: {e}")

    if latencies:
        summary = {
            "total_requests": int(num_requests),
            "successful_requests": len(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "avg_latency": sum(latencies) / len(latencies)
        }
        print("\n--- Benchmark Summary ---")
        for key, value in summary.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        _save_results(log_file, summary)
    else:
        print("\nNo requests were successful.")

def run_streaming(host, model, prompt, log_file, **kwargs):
    """Runs a streaming benchmark, measuring TTFT and tokens/sec."""
    print(f"Starting Ollama streaming benchmark on {host}...")
    print(f"Model: {model}, Prompt: '{prompt}'")

    base_url = f"http://{host}:11434"
    api_url = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }

    try:
        start_time = time.time()
        response = http_requests.post(api_url, json=payload, stream=True, timeout=300)
        response.raise_for_status()

        first_token_time = None
        total_tokens = 0
        response_text = ""

        for chunk in response.iter_lines():
            if chunk:
                data = json.loads(chunk)
                if 'response' in data and not first_token_time:
                    first_token_time = time.time()
                
                if 'response' in data:
                    response_text += data['response']
                    total_tokens += 1

        end_time = time.time()

        if first_token_time:
            ttft = first_token_time - start_time
            total_duration = end_time - start_time
            tps = total_tokens / total_duration if total_duration > 0 else 0

            summary = {
                "ttft": ttft,
                "total_tokens": total_tokens,
                "total_duration": total_duration,
                "tps": tps
            }

            print("\n--- Benchmark Summary ---")
            print(f"Time to first token (TTFT): {ttft:.2f}s")
            print(f"Total tokens generated: {total_tokens}")
            print(f"Total duration: {total_duration:.2f}s")
            print(f"Tokens per second (TPS): {tps:.2f}")
            _save_results(log_file, summary)
        else:
            print("\nDid not receive any tokens.")

    except http_requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

# A mapping of benchmark names to functions
BENCHMARKS = {
    "ollama_latency": run_latency,
    "ollama_streaming": run_streaming
}

def run(host, log_file, benchmark_name, **params):
    if benchmark_name in BENCHMARKS:
        BENCHMARKS[benchmark_name](host=host, log_file=log_file, **params)
    else:
        print(f"Unknown benchmark: {benchmark_name}")