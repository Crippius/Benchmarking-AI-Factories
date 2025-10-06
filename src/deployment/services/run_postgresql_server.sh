#!/bin/bash -l
#SBATCH --job-name=postgresql_server_job
#SBATCH --output=postgresql_server_%j.log
#SBATCH --nodes=1
#SBATCH --partition=cpu
#SBATCH --time=01:00:00
#SBATCH --account=p200981
#SBATCH --qos=default

# --- Environment Setup ---
echo "Loading Apptainer module..."
module load Apptainer

# --- Data Persistence Setup ---
echo "Creating persistent data directory..."
mkdir -p ./pgdata

# --- Server Execution ---
echo "Starting PostgreSQL server..."
apptainer exec \
    --env POSTGRES_PASSWORD=mysecretpassword \
    --bind ./pgdata:/var/lib/postgresql/data \
    docker://postgres:latest &
SERVER_PID=$!

echo "Server is running with PID: $SERVER_PID. Waiting for job to finish..."
wait $SERVER_PID
