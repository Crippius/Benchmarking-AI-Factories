"""Common Slurm utilities for job management."""

import subprocess
import time
import re


def get_job_node(job_id, max_wait_time=300, check_interval=5):
    """
    Retrieves the node where a Slurm job is running.
    Waits for the job to be in a running state.
    
    Args:
        job_id: The Slurm job ID
        max_wait_time: Maximum time to wait in seconds (default: 300)
        check_interval: Time between checks in seconds (default: 5)
    
    Returns:
        str: Node name where job is running, or None if failed/timeout
    """
    print(f"Waiting for job {job_id} to start and get a node...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            result = subprocess.run(
                ["scontrol", "show", "job", job_id],
                capture_output=True, text=True, check=True
            )
            
            job_info = {}
            for item in result.stdout.split():
                if "=" in item:
                    key, value = item.split("=", 1)
                    job_info[key] = value
            
            job_state = job_info.get("JobState")
            if job_state == "RUNNING":
                node = job_info.get("NodeList")
                if node and node != "(null)":
                    print(f"Job {job_id} is running on node {node}.")
                    return node
            elif job_state not in ("PENDING", "CONFIGURING"):
                print(f"Job {job_id} is in state {job_state}, not RUNNING.")
                return None
            
            time.sleep(check_interval)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error checking job {job_id}: {e}")
            return None
    
    print(f"Timeout waiting for job {job_id} to start.")
    return None


def submit_job(sbatch_args, script_path):
    """
    Submit a job to Slurm using sbatch.
    
    Args:
        sbatch_args: List of sbatch arguments (e.g., ['--partition=gpu', '--nodes=1'])
        script_path: Path to the script to submit
    
    Returns:
        str: Job ID if successful, None otherwise
    """
    command = ["sbatch"] + sbatch_args + [str(script_path)]
    
    try:
        result = subprocess.run(
            command,
            capture_output=True, text=True, check=True
        )
        match = re.search(r"Submitted batch job (\d+)", result.stdout)
        if match:
            return match.group(1)
        else:
            print(f"Could not parse Job ID from sbatch output: {result.stdout.strip()}")
            return None
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error submitting job: {e}")
        if isinstance(e, subprocess.CalledProcessError):
            print(f"Stderr: {e.stderr}")
        return None


def cancel_job(job_id):
    """
    Cancel a Slurm job.
    
    Args:
        job_id: The Slurm job ID to cancel
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        subprocess.run(
            ["scancel", job_id],
            check=True, capture_output=True, text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error cancelling job {job_id}: {e}")
        return False


def get_job_status(job_id):
    """
    Get detailed status of a Slurm job.
    
    Args:
        job_id: The Slurm job ID
    
    Returns:
        str: Job status output, or None if error
    """
    try:
        result = subprocess.run(
            ["scontrol", "show", "job", job_id],
            check=True, text=True, capture_output=True
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting job status: {e}")
        return None


def list_user_jobs():
    """
    List all jobs for the current user.
    
    Returns:
        str: Output from squeue, or None if error
    """
    try:
        result = subprocess.run(
            ["squeue", "--me"],
            check=True, text=True, capture_output=True
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error listing jobs: {e}")
        return None
