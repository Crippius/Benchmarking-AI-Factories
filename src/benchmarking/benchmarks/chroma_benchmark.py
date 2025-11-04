import chromadb
import time
import json

def _save_results(log_file, results):
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=4)

def run_throughput(host, collection_name, documents, log_file, **kwargs):
    """Runs a throughput benchmark against a ChromaDB service."""
    print(f"Starting ChromaDB throughput benchmark on {host}...")
    print(f"Collection: '{collection_name}', Documents: {documents}")

    try:
        client = chromadb.HttpClient(host=host, port=8000)
        collection = client.get_or_create_collection(name=collection_name)

        # --- Write throughput ---
        print(f"Writing {documents} documents...")
        start_time = time.time()
        collection.add(
            ids=[f"id_{i}" for i in range(int(documents))],
            documents=[f"This is document {i}" for i in range(int(documents))]
        )
        end_time = time.time()
        write_duration = end_time - start_time
        write_throughput = int(documents) / write_duration if write_duration > 0 else float('inf')

        write_summary = {
            "operation": "write",
            "documents": int(documents),
            "duration": write_duration,
            "throughput": write_throughput
        }
        print("\n--- Write Benchmark Summary ---")
        print(f"Time taken: {write_duration:.2f}s, Throughput: {write_throughput:.2f} docs/s")

        # --- Read throughput ---
        print(f"\nReading {documents} documents...")
        start_time = time.time()
        collection.get(ids=[f"id_{i}" for i in range(int(documents))])
        end_time = time.time()
        read_duration = end_time - start_time
        read_throughput = int(documents) / read_duration if read_duration > 0 else float('inf')

        read_summary = {
            "operation": "read",
            "documents": int(documents),
            "duration": read_duration,
            "throughput": read_throughput
        }
        print("\n--- Read Benchmark Summary ---")
        print(f"Time taken: {read_duration:.2f}s, Throughput: {read_throughput:.2f} docs/s")

        _save_results(log_file, {"write": write_summary, "read": read_summary})

        # Clean up
        client.delete_collection(name=collection_name)

    except Exception as e:
        print(f"An error occurred during the benchmark: {e}")

def run_query(host, collection_name, documents, n_results, log_file, **kwargs):
    """Runs a query performance benchmark against a ChromaDB service."""
    print(f"Starting ChromaDB query benchmark on {host}...")
    print(f"Collection: '{collection_name}', Documents: {documents}, N_results: {n_results}")

    try:
        client = chromadb.HttpClient(host=host, port=8000)
        collection = client.get_or_create_collection(name=collection_name)

        # Add documents to query
        collection.add(
            embeddings=[[i/10.0, i/10.0, i/10.0] for i in range(int(documents))],
            ids=[f"id_{i}" for i in range(int(documents))]
        )

        # --- Query performance ---
        print(f"Querying for {n_results} results...")
        start_time = time.time()
        collection.query(
            query_embeddings=[[0.5, 0.5, 0.5]],
            n_results=int(n_results)
        )
        end_time = time.time()
        query_duration = end_time - start_time

        summary = {
            "operation": "query",
            "documents_in_collection": int(documents),
            "n_results": int(n_results),
            "duration": query_duration
        }
        print("\n--- Query Benchmark Summary ---")
        print(f"Time taken to query: {query_duration:.2f}s")
        _save_results(log_file, summary)

        # Clean up
        client.delete_collection(name=collection_name)

    except Exception as e:
        print(f"An error occurred during the benchmark: {e}")


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