import argparse
import time
import chromadb

def test_chroma(host):
    """
    Performs a basic set of operations on a running ChromaDB server.

    Args:
        host (str): The IP address or hostname of the node where ChromaDB is running.
    """
    # The default port for the ChromaDB server is 8000
    print(f"Connecting to ChromaDB server at {host}:8000...")

    try:
        # 1. Connect to the ChromaDB server
        client = chromadb.HttpClient(host=host, port=8000)

        # Record start time for the entire operation
        start_time = time.time()

        # 2. Create or get a collection
        collection_name = "test_collection"
        print(f"Creating a temporary collection: '{collection_name}'")
        collection = client.get_or_create_collection(name=collection_name)

        # 3. Add a document and embedding
        print("Adding a sample document and embedding...")
        collection.add(
            embeddings=[[1.5, 2.9, 3.4]],  # Sample embedding vector
            documents=["This is a test document for ChromaDB."],
            ids=["test_id_1"]
        )

        # 4. Query the collection to retrieve the document
        print("Querying the collection to find the document...")
        results = collection.query(
            query_embeddings=[[1.5, 2.9, 3.4]],
            n_results=1
        )

        # 5. Clean up by deleting the collection
        print(f"Cleaning up by deleting collection '{collection_name}'...")
        client.delete_collection(name=collection_name)
        
        duration = time.time() - start_time
        
        print(f"\nFull test (connect, add, query, delete) successful in {duration:.2f} seconds.")
        return True

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check if the host IP is correct and the ChromaDB service is running.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test a running ChromaDB service.")
    parser.add_argument("host", help="The IP address or hostname of the ChromaDB server node.")
    args = parser.parse_args()
    
    test_chroma(args.host)
