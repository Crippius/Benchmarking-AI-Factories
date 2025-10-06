import argparse
import time
import psycopg2

def test_postgres(host):
    """
    Connects to a running PostgreSQL server and executes a simple query.

    Args:
        host (str): The IP address or hostname of the node where PostgreSQL is running.
    """
    # Standard PostgreSQL connection details
    # The password must match the POSTGRES_PASSWORD in the .sh script
    conn_string = f"dbname=postgres user=postgres password=mysecretpassword host={host} port=5432"
    
    print(f"Connecting to PostgreSQL server at {host}:5432...")

    try:
        # 1. Connect to the server
        start_time = time.time()
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # 2. Execute a simple "ping" query
        print("Executing a simple 'SELECT 1' query...")
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        
        duration = time.time() - start_time
        
        # 3. Clean up
        cur.close()
        conn.close()

        print("\n--- Test Results ---")
        if result and result[0] == 1:
            print("Successfully received '1' from the server.")
        else:
            print("Query did not return the expected result.")
        print("--------------------")
        print(f"\nFull test (connect, query, disconnect) successful in {duration:.2f} seconds.")

    except psycopg2.OperationalError as e:
        print(f"\nAn error occurred: {e}")
        print("Could not connect. Please check if the host IP is correct, the service is running, and wait a moment for it to initialize.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test a running PostgreSQL service.")
    parser.add_argument("host", help="The IP address or hostname of the PostgreSQL server node.")
    args = parser.parse_args()
    
    test_postgres(args.host)
