import argparse
import requests
import json
import time

def test_ollama(host, max_wait_time=300, check_interval=10):
    """
    Tests the Ollama server health, waiting for model download if necessary.

    Args:
        host (str): The IP address or hostname of the node where Ollama is running.
        max_wait_time (int): Maximum time to wait in seconds (default: 300s = 5 minutes).
        check_interval (int): Time between checks in seconds (default: 10s).
    """
    # The default port for the Ollama API is 11434
    base_url = f"http://{host}:11434"
    api_url = f"{base_url}/api/generate"
    tags_url = f"{base_url}/api/tags"

    # First, check if the API is accessible
    print(f"Checking if Ollama API is accessible at {base_url}...")
    
    start_time = time.time()
    api_accessible = False
    
    # Try to reach the API endpoint
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(tags_url, timeout=5)
            if response.status_code == 200:
                print("✓ Ollama API is accessible")
                api_accessible = True
                break
        except requests.exceptions.RequestException:
            pass
        
        print(f"  Waiting for Ollama API to become available... ({int(time.time() - start_time)}s elapsed)")
        time.sleep(check_interval)
    
    if not api_accessible:
        print(f"✗ Could not reach Ollama API after {max_wait_time}s")
        return False

    # The data payload for the request
    payload = {
        "model": "llama2",
        "prompt": "In one short sentence, what is a supercomputer?",
        "stream": False  # We want the full response at once
    }

    print(f"\nSending test prompt to Ollama server at {api_url}...")
    print(f"Prompt: \"{payload['prompt']}\"")
    print("(Note: If model is downloading, this may take a few minutes...)")

    # Now try to send inference request, allowing time for model download
    elapsed = time.time() - start_time
    remaining_time = max_wait_time - elapsed
    
    try:
        # Send the HTTP POST request with extended timeout for model download
        request_start = time.time()
        response = requests.post(api_url, json=payload, timeout=remaining_time)
        
        # Check if the request was successful
        response.raise_for_status() 

        # Record end time
        duration = time.time() - request_start

        # Parse the JSON response from the server
        response_data = response.json()
        
        print(f"\n✓ Request successful in {duration:.2f} seconds.")
        print(f"Total health check time: {time.time() - start_time:.2f} seconds")
        return True

    except requests.exceptions.Timeout:
        print(f"\n✗ Request timed out after {remaining_time:.0f}s")
        print("The model may still be downloading. Check the job logs for progress.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n✗ An error occurred: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        print("Please check if the host IP is correct and the Ollama service is running.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test a running Ollama service.")
    parser.add_argument("host", help="The IP address or hostname of the Ollama server node.")
    args = parser.parse_args()
    
    test_ollama(args.host)
