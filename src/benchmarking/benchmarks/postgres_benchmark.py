import psycopg2
import time
import json

def _save_results(log_file, results):
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=4)

def run_throughput(host, table_name, rows, log_file, **kwargs):
    """Runs a basic throughput benchmark against a PostgreSQL service."""
    print(f"Starting PostgreSQL throughput benchmark on {host}...")
    print(f"Table: '{table_name}', Rows: {rows}")

    conn_string = f"dbname=postgres user=postgres password=mysecretpassword host={host} port=5432"

    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, data TEXT);")
        conn.commit()

        # --- Write throughput ---
        print(f"Writing {rows} rows...")
        start_time = time.time()
        for i in range(int(rows)):
            cur.execute(f"INSERT INTO {table_name} (data) VALUES ('This is row {i}');")
        conn.commit()
        end_time = time.time()
        write_duration = end_time - start_time
        write_throughput = int(rows) / write_duration if write_duration > 0 else float('inf')

        write_summary = {
            "operation": "write",
            "rows": int(rows),
            "duration": write_duration,
            "throughput": write_throughput
        }
        print(f"\n--- Write Benchmark Summary ---")
        print(f"Time taken: {write_duration:.2f}s, Throughput: {write_throughput:.2f} rows/s")

        # --- Read throughput ---
        print(f"\nReading {rows} rows...")
        start_time = time.time()
        cur.execute(f"SELECT * FROM {table_name};")
        _ = cur.fetchall()
        end_time = time.time()
        read_duration = end_time - start_time
        read_throughput = int(rows) / read_duration if read_duration > 0 else float('inf')

        read_summary = {
            "operation": "read",
            "rows": int(rows),
            "duration": read_duration,
            "throughput": read_throughput
        }
        print(f"\n--- Read Benchmark Summary ---")
        print(f"Time taken: {read_duration:.2f}s, Throughput: {read_throughput:.2f} rows/s")

        _save_results(log_file, {"write": write_summary, "read": read_summary})

        # Clean up
        cur.execute(f"DROP TABLE {table_name};")
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"An error occurred during the benchmark: {e}")

def run_transaction(host, transactions, log_file, **kwargs):
    """Runs a transaction performance benchmark."""
    print(f"Starting PostgreSQL transaction benchmark on {host}...")
    print(f"Transactions: {transactions}")

    conn_string = f"dbname=postgres user=postgres password=mysecretpassword host={host} port=5432"

    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS transaction_test (id INT);")
        conn.commit()

        start_time = time.time()
        for i in range(int(transactions)):
            cur.execute("BEGIN;")
            cur.execute(f"INSERT INTO transaction_test (id) VALUES ({i});")
            cur.execute("COMMIT;")
        end_time = time.time()
        duration = end_time - start_time
        tps = int(transactions) / duration if duration > 0 else float('inf')

        summary = {
            "operation": "transaction",
            "transactions": int(transactions),
            "duration": duration,
            "tps": tps
        }
        print("\n--- Transaction Benchmark Summary ---")
        print(f"Time taken: {duration:.2f}s, Transactions/sec: {tps:.2f}")
        _save_results(log_file, summary)

        # Clean up
        cur.execute("DROP TABLE transaction_test;")
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"An error occurred during the benchmark: {e}")


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