import psycopg2
import time
import json
from datetime import datetime

def _save_results(log_file, results):
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=4)

def run_throughput(host, table_name, rows, log_file, **kwargs):
    """Runs a basic throughput benchmark against a PostgreSQL service."""
    print(f"Starting PostgreSQL throughput benchmark on {host}...")
    print(f"Table: '{table_name}', Rows: {rows}")

    conn_string = f"dbname=postgres user=postgres password=mysecretpassword host={host} port=5432"

    benchmark_start = time.time()
    
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, data TEXT);")
        conn.commit()

        # --- Write throughput ---
        print(f"Writing {rows} rows...")
        write_start = time.time()
        for i in range(int(rows)):
            cur.execute(f"INSERT INTO {table_name} (data) VALUES ('This is row {i}');")
        conn.commit()
        write_end = time.time()
        write_duration = write_end - write_start
        write_throughput = int(rows) / write_duration if write_duration > 0 else float('inf')

        print(f"\n--- Write Benchmark Summary ---")
        print(f"Time taken: {write_duration:.2f}s, Throughput: {write_throughput:.2f} rows/s")

        # --- Read throughput ---
        print(f"\nReading {rows} rows...")
        read_start = time.time()
        cur.execute(f"SELECT * FROM {table_name};")
        read_results = cur.fetchall()
        read_end = time.time()
        read_duration = read_end - read_start
        read_throughput = int(rows) / read_duration if read_duration > 0 else float('inf')

        print(f"\n--- Read Benchmark Summary ---")
        print(f"Time taken: {read_duration:.2f}s, Throughput: {read_throughput:.2f} rows/s")

        benchmark_end = time.time()
        
        results = {
            "metadata": {
                "benchmark_name": "postgres_throughput",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "table_name": table_name,
                "total_benchmark_duration": benchmark_end - benchmark_start
            },
            "configuration": {
                "rows": int(rows)
            },
            "write_operation": {
                "rows": int(rows),
                "duration": write_duration,
                "throughput_rows_per_sec": write_throughput,
                "avg_time_per_row": write_duration / int(rows)
            },
            "read_operation": {
                "rows_requested": int(rows),
                "rows_retrieved": len(read_results),
                "duration": read_duration,
                "throughput_rows_per_sec": read_throughput,
                "avg_time_per_row": read_duration / int(rows)
            },
            "summary": {
                "total_operations": 2,
                "total_rows_processed": int(rows) * 2,
                "write_throughput": write_throughput,
                "read_throughput": read_throughput,
                "read_write_ratio": read_throughput / write_throughput if write_throughput > 0 else float('inf')
            }
        }
        
        _save_results(log_file, results)

        # Clean up
        cur.execute(f"DROP TABLE {table_name};")
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        error_results = {
            "metadata": {
                "benchmark_name": "postgres_throughput",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "table_name": table_name
            },
            "error": str(e),
            "status": "failed"
        }
        print(f"An error occurred during the benchmark: {e}")
        _save_results(log_file, error_results)

def run_transaction(host, transactions, log_file, **kwargs):
    """Runs a transaction performance benchmark."""
    print(f"Starting PostgreSQL transaction benchmark on {host}...")
    print(f"Transactions: {transactions}")

    conn_string = f"dbname=postgres user=postgres password=mysecretpassword host={host} port=5432"

    benchmark_start = time.time()
    
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS transaction_test (id INT);")
        conn.commit()

        transaction_start = time.time()
        transaction_times = []
        
        for i in range(int(transactions)):
            tx_start = time.time()
            cur.execute("BEGIN;")
            cur.execute(f"INSERT INTO transaction_test (id) VALUES ({i});")
            cur.execute("COMMIT;")
            tx_end = time.time()
            transaction_times.append(tx_end - tx_start)
            
        transaction_end = time.time()
        duration = transaction_end - transaction_start
        tps = int(transactions) / duration if duration > 0 else float('inf')
        
        benchmark_end = time.time()

        results = {
            "metadata": {
                "benchmark_name": "postgres_transaction",
                "timestamp": datetime.now().isoformat(),
                "host": host,
                "total_benchmark_duration": benchmark_end - benchmark_start
            },
            "configuration": {
                "transactions": int(transactions)
            },
            "transaction_operation": {
                "total_transactions": int(transactions),
                "duration": duration,
                "transactions_per_sec": tps,
                "avg_transaction_time": sum(transaction_times) / len(transaction_times) if transaction_times else 0,
                "min_transaction_time": min(transaction_times) if transaction_times else 0,
                "max_transaction_time": max(transaction_times) if transaction_times else 0
            },
            "summary": {
                "tps": tps,
                "total_duration": duration,
                "avg_latency_ms": (sum(transaction_times) / len(transaction_times) * 1000) if transaction_times else 0
            }
        }
        
        print("\n--- Transaction Benchmark Summary ---")
        print(f"Time taken: {duration:.2f}s")
        print(f"Transactions/sec: {tps:.2f}")
        print(f"Avg Transaction Time: {results['transaction_operation']['avg_transaction_time']:.4f}s")
        
        _save_results(log_file, results)

        # Clean up
        cur.execute("DROP TABLE transaction_test;")
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        error_results = {
            "metadata": {
                "benchmark_name": "postgres_transaction",
                "timestamp": datetime.now().isoformat(),
                "host": host
            },
            "error": str(e),
            "status": "failed"
        }
        print(f"An error occurred during the benchmark: {e}")
        _save_results(log_file, error_results)


BENCHMARKS = {
    "postgres_throughput": run_throughput,
    "postgres_transaction": run_transaction
}

def run(host, log_file, benchmark_name, **params):
    """Main entry point for running benchmarks."""
    if benchmark_name in BENCHMARKS:
        BENCHMARKS[benchmark_name](host=host, log_file=log_file, **params)
    else:
        print(f"Unknown benchmark: {benchmark_name}")