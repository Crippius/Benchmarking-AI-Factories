#!/bin/bash -l
#SBATCH --job-name=chromadb_server_job
#SBATCH --output=chromadb_server_%j.log
#SBATCH --nodes=1
#SBATCH --partition=cpu
#SBATCH --time=01:00:00
#SBATCH --account=p200981
#SBATCH --qos=default

# --- Environment Setup ---
echo "Loading Apptainer module..."
module load Apptainer

# --- Data Persistence Setup ---
echo "Creating persistent data directory for ChromaDB..."
mkdir -p ./chroma_data

# --- Server Execution ---
echo "Starting ChromaDB server in the background..."
# Note: The chroma server runs as the 'chroma' user inside the container.
# We bind our host data path to the container's default persistence directory.
apptainer exec \
    --bind ./chroma_data:/chroma/chroma \
    docker://chromadb/chroma \
    chroma run --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

echo "Server is running with PID: $SERVER_PID. Waiting for job to finish..."
# Wait for the server process to exit, keeping the Slurm job alive
wait $SERVER_PID
