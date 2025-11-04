import chromadb
import time
import json
from datetime import datetime

def _save_results(log_file, results):
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=4)

def run_throughput(host, collection_name, documents, log_file, **kwargs):
    """Runs a throughput benchmark against a ChromaDB service."""
    print(f"Starting ChromaDB throughput benchmark on {host}...")
    print(f"Collection: '{collection_name}', Documents: {documents}")

    benchmark_start = time.time()
    
    try:
        client = chromadb.HttpClient(host=host, port=8000)
        collection = client.get_or_create_collection(name=collection_name)

        # --- Write throughput ---
        print(f"Writing {documents} documents...")
        write_start = time.time()
        collection.add(
            ids=[f"id_{i}" for i in range(int(documents))],
            documents=[f"This is document {i}" for i in range(int(documents))]
        )
        write_end = time.time()
        write_duration = write_end - write_start
        write_throughput = int(documents) / write_duration if write_duration > 0 else float('inf')

        print("\n--- Write Benchmark Summary ---")
        print(f"Time taken: {write_duration:.2f}s, Throughput: {write_throughput:.2f} docs/s")

        # --- Read throughput ---
        print(f"\nReading {documents} documents...")
        read_start = time.time()
        read_results = collection.get(ids=[f"id_{i}" for i in range(int(documents))])
        read_end = time.time()
        read_duration = read_end - read_start
        read_throughput = int(documents) / read_duration if read_duration > 0 else float('inf')

        print("\n--- Read Benchmark Summary ---")
        print(f"Time taken: {read_duration:.2f}s, Throughput: {read_throughput:.2f} docs/s")

        benchmark_end = time.time()
        
        results = {
            "metadata": {
                "benchmark_name": "chroma_throughput",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "collection_name": collection_name,
                "total_benchmark_duration": benchmark_end - benchmark_start
            },
            "configuration": {
                "documents": int(documents)
            },
            "write_operation": {
                "documents": int(documents),
                "duration": write_duration,
                "throughput_docs_per_sec": write_throughput,
                "avg_time_per_doc": write_duration / int(documents)
            },
            "read_operation": {
                "documents": int(documents),
                "documents_retrieved": len(read_results['ids']) if read_results else 0,
                "duration": read_duration,
                "throughput_docs_per_sec": read_throughput,
                "avg_time_per_doc": read_duration / int(documents)
            },
            "summary": {
                "total_operations": 2,
                "total_documents_processed": int(documents) * 2,
                "write_throughput": write_throughput,
                "read_throughput": read_throughput,
                "read_write_ratio": read_throughput / write_throughput if write_throughput > 0 else float('inf')
            }
        }
        
        _save_results(log_file, results)

        # Clean up
        client.delete_collection(name=collection_name)

    except Exception as e:
        error_results = {
            "metadata": {
                "benchmark_name": "chroma_throughput",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "collection_name": collection_name
            },
            "error": str(e),
            "status": "failed"
        }
        print(f"An error occurred during the benchmark: {e}")
        _save_results(log_file, error_results)

def run_query(host, collection_name, documents, n_results, log_file, **kwargs):
    """Runs a query performance benchmark against a ChromaDB service."""
    print(f"Starting ChromaDB query benchmark on {host}...")
    print(f"Collection: '{collection_name}', Documents: {documents}, N_results: {n_results}")

    benchmark_start = time.time()
    
    try:
        client = chromadb.HttpClient(host=host, port=8000)
        collection = client.get_or_create_collection(name=collection_name)

        # Add documents to query
        insert_start = time.time()
        collection.add(
            embeddings=[[i/10.0, i/10.0, i/10.0] for i in range(int(documents))],
            ids=[f"id_{i}" for i in range(int(documents))]
        )
        insert_end = time.time()
        insert_duration = insert_end - insert_start

        # --- Query performance ---
        print(f"Querying for {n_results} results...")
        query_start = time.time()
        query_results = collection.query(
            query_embeddings=[[0.5, 0.5, 0.5]],
            n_results=int(n_results)
        )
        query_end = time.time()
        query_duration = query_end - query_start
        
        benchmark_end = time.time()

        results = {
            "metadata": {
                "benchmark_name": "chroma_query",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "collection_name": collection_name,
                "total_benchmark_duration": benchmark_end - benchmark_start
            },
            "configuration": {
                "documents_in_collection": int(documents),
                "n_results_requested": int(n_results)
            },
            "insert_operation": {
                "documents": int(documents),
                "duration": insert_duration,
                "throughput_docs_per_sec": int(documents) / insert_duration if insert_duration > 0 else float('inf')
            },
            "query_operation": {
                "duration": query_duration,
                "results_returned": len(query_results['ids'][0]) if query_results and query_results.get('ids') else 0,
                "latency_ms": query_duration * 1000
            },
            "summary": {
                "query_latency": query_duration,
                "query_latency_ms": query_duration * 1000,
                "documents_queried": int(documents),
                "results_per_query": int(n_results)
            }
        }
        
        print("\n--- Query Benchmark Summary ---")
        print(f"Time taken to query: {query_duration:.4f}s ({query_duration * 1000:.2f}ms)")
        print(f"Results returned: {results['query_operation']['results_returned']}")
        
        _save_results(log_file, results)

        # Clean up
        client.delete_collection(name=collection_name)

    except Exception as e:
        error_results = {
            "metadata": {
                "benchmark_name": "chroma_query",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "collection_name": collection_name
            },
            "error": str(e),
            "status": "failed"
        }
        print(f"An error occurred during the benchmark: {e}")
        _save_results(log_file, error_results)


BENCHMARKS = {
    "chroma_throughput": run_throughput,
    "chroma_query": run_query
}

def run(host, log_file, benchmark_name, **params):
    """Main entry point for running benchmarks."""
    if benchmark_name in BENCHMARKS:
        BENCHMARKS[benchmark_name](host=host, log_file=log_file, **params)
    else:
        print(f"Unknown benchmark: {benchmark_name}")