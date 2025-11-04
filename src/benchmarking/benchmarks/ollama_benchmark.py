import requests as http_requests
import time
import json
from datetime import datetime
import statistics

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

    start_benchmark = time.time()
    requests_data = []
    latencies = []
    
    for i in range(int(num_requests)):
        request_start = time.time()
        request_result = {
            "request_id": i + 1,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        try:
            response = http_requests.post(api_url, json=payload, timeout=300)
            response.raise_for_status()
            request_end = time.time()
            latency = request_end - request_start
            
            response_data = response.json()
            
            request_result.update({
                "status": "success",
                "latency": latency,
                "response_length": len(response_data.get("response", "")),
                "eval_count": response_data.get("eval_count"),
                "eval_duration": response_data.get("eval_duration"),
                "load_duration": response_data.get("load_duration"),
                "prompt_eval_count": response_data.get("prompt_eval_count"),
                "prompt_eval_duration": response_data.get("prompt_eval_duration"),
                "total_duration": response_data.get("total_duration"),
            })
            
            latencies.append(latency)
            print(f"Request {i+1}/{num_requests} successful in {latency:.2f}s")
            
        except http_requests.exceptions.RequestException as e:
            request_result.update({
                "status": "failed",
                "error": str(e)
            })
            print(f"Request {i+1}/{num_requests} failed: {e}")
        
        requests_data.append(request_result)

    end_benchmark = time.time()
    
    # Calculate comprehensive statistics
    results = {
        "metadata": {
            "benchmark_name": "ollama_latency",
            "timestamp": datetime.now().isoformat(),
            "host": host,
            "model": model,
            "prompt": prompt,
            "total_benchmark_duration": end_benchmark - start_benchmark
        },
        "configuration": {
            "num_requests": int(num_requests),
            "stream": False
        },
        "summary": {
            "total_requests": int(num_requests),
            "successful_requests": len(latencies),
            "failed_requests": int(num_requests) - len(latencies)
        },
        "requests": requests_data
    }
    
    if latencies:
        results["summary"].update({
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "avg_latency": sum(latencies) / len(latencies),
            "median_latency": statistics.median(latencies),
            "stddev_latency": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "p95_latency": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 2 else max(latencies),
            "p99_latency": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 2 else max(latencies),
            "throughput_rps": len(latencies) / (end_benchmark - start_benchmark)
        })
        
        print("\n--- Benchmark Summary ---")
        print(f"Total Requests: {results['summary']['total_requests']}")
        print(f"Successful Requests: {results['summary']['successful_requests']}")
        print(f"Failed Requests: {results['summary']['failed_requests']}")
        print(f"Min Latency: {results['summary']['min_latency']:.4f}s")
        print(f"Avg Latency: {results['summary']['avg_latency']:.4f}s")
        print(f"Median Latency: {results['summary']['median_latency']:.4f}s")
        print(f"Max Latency: {results['summary']['max_latency']:.4f}s")
        print(f"P95 Latency: {results['summary']['p95_latency']:.4f}s")
        print(f"P99 Latency: {results['summary']['p99_latency']:.4f}s")
        print(f"Throughput: {results['summary']['throughput_rps']:.2f} req/s")
        
        _save_results(log_file, results)
    else:
        print("\nNo requests were successful.")
        _save_results(log_file, results)

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

    benchmark_start = time.time()
    token_timestamps = []
    
    try:
        start_time = time.time()
        response = http_requests.post(api_url, json=payload, stream=True, timeout=300)
        response.raise_for_status()

        first_token_time = None
        total_tokens = 0
        response_text = ""
        tokens_data = []

        for chunk in response.iter_lines():
            if chunk:
                token_time = time.time()
                data = json.loads(chunk)
                
                if 'response' in data:
                    if not first_token_time:
                        first_token_time = token_time
                    
                    token_data = {
                        "token_id": total_tokens + 1,
                        "timestamp": token_time - start_time,
                        "content": data['response'],
                        "done": data.get('done', False)
                    }
                    
                    if data.get('done'):
                        token_data.update({
                            "eval_count": data.get("eval_count"),
                            "eval_duration": data.get("eval_duration"),
                            "load_duration": data.get("load_duration"),
                            "prompt_eval_count": data.get("prompt_eval_count"),
                            "prompt_eval_duration": data.get("prompt_eval_duration"),
                            "total_duration": data.get("total_duration"),
                        })
                    
                    tokens_data.append(token_data)
                    response_text += data['response']
                    total_tokens += 1
                    token_timestamps.append(token_time)

        end_time = time.time()

        results = {
            "metadata": {
                "benchmark_name": "ollama_streaming",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "model": model,
                "prompt": prompt,
                "total_benchmark_duration": end_time - benchmark_start
            },
            "configuration": {
                "stream": True
            },
            "response": {
                "text": response_text,
                "length": len(response_text)
            },
            "tokens": tokens_data
        }

        if first_token_time:
            ttft = first_token_time - start_time
            total_duration = end_time - start_time
            tps = total_tokens / total_duration if total_duration > 0 else 0
            
            # Calculate inter-token latencies
            if len(token_timestamps) > 1:
                inter_token_latencies = [
                    token_timestamps[i] - token_timestamps[i-1] 
                    for i in range(1, len(token_timestamps))
                ]
                avg_inter_token = sum(inter_token_latencies) / len(inter_token_latencies)
            else:
                avg_inter_token = 0

            results["summary"] = {
                "ttft": ttft,
                "total_tokens": total_tokens,
                "total_duration": total_duration,
                "tokens_per_second": tps,
                "avg_inter_token_latency": avg_inter_token
            }

            print("\n--- Benchmark Summary ---")
            print(f"Time to First Token (TTFT): {ttft:.2f}s")
            print(f"Total Tokens Generated: {total_tokens}")
            print(f"Total Duration: {total_duration:.2f}s")
            print(f"Tokens per Second (TPS): {tps:.2f}")
            print(f"Avg Inter-token Latency: {avg_inter_token:.4f}s")
            print(f"Response Length: {len(response_text)} characters")
            
            _save_results(log_file, results)
        else:
            results["summary"] = {
                "status": "failed",
                "error": "Did not receive any tokens"
            }
            print("\nDid not receive any tokens.")
            _save_results(log_file, results)

    except http_requests.exceptions.RequestException as e:
        results = {
            "metadata": {
                "benchmark_name": "ollama_streaming",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "model": model,
                "prompt": prompt
            },
            "summary": {
                "status": "failed",
                "error": str(e)
            }
        }
        print(f"Request failed: {e}")
        _save_results(log_file, results)

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