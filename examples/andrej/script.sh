#!/bin/bash
#SBATCH --job-name=hello_world_job   # Job name
#SBATCH --output=hello_world_%j.out  # Standard output and error log (%j is the job I$
#SBATCH --ntasks=1                   # Run on a single CPU
#SBATCH --time=00:01:00              # Time limit of 1 minute        
#SBATCH --partition=gpu
#SBATCH --account=p200981
#SBATCH --qos=default
# --- Commands to run ---

echo "Compiling the C code..."
gcc main.c -o main

echo "Running the compiled program..."
./main

echo "Job finished."
