#!/bin/bash -l
#SBATCH --job-name=ollama_server_job
#SBATCH --output=ollama_server_%j.log
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --account=p200981
#SBATCH --qos=default

# --- Environment Setup ---
echo "Loading Apptainer module..."
module load Apptainer

# --- Apptainer Image Setup ---
IMAGE_FILE="ollama_latest.sif"
if [ ! -f "$IMAGE_FILE" ]; then
    echo "Apptainer image not found. Pulling from Docker Hub..."
    apptainer pull docker://ollama/ollama
fi

# --- Server Execution ---
echo "Starting Ollama server in the background..."
apptainer exec --nv $IMAGE_FILE ollama serve &
SERVER_PID=$!

echo "Waiting for server to initialize..."
sleep 15

# --- Pull Model ---
echo "Pulling the llama2 model..."
apptainer exec --nv $IMAGE_FILE ollama pull llama2

echo "Server is running with PID: $SERVER_PID. Waiting for job to finish..."
wait $SERVER_PID