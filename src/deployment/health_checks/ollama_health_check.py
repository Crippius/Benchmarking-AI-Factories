import argparse
import requests
import json
import time

def test_ollama(host):
    """
    Sends a single inference request to a running Ollama server.

    Args:
        host (str): The IP address or hostname of the node where Ollama is running.
    """
    # The default port for the Ollama API is 11434
    url = f"http://{host}:11434/api/generate"

    # The data payload for the request
    payload = {
        "model": "llama2",
        "prompt": "In one short sentence, what is a supercomputer?",
        "stream": False  # We want the full response at once
    }

    print(f"Sending prompt to Ollama server at {url}...")
    print(f"Prompt: \"{payload['prompt']}\"")

    try:
        # Record start time
        start_time = time.time()

        # Send the HTTP POST request
        response = requests.post(url, json=payload)
        
        # Check if the request was successful
        response.raise_for_status() 

        # Record end time
        duration = time.time() - start_time

        # Parse the JSON response from the server
        response_data = response.json()
        
        print(f"\nRequest successful in {duration:.2f} seconds.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred: {e}")
        print("Please check if the host IP is correct and the Ollama service is running.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test a running Ollama service.")
    parser.add_argument("host", help="The IP address or hostname of the Ollama server node.")
    args = parser.parse_args()
    
    test_ollama(args.host)
